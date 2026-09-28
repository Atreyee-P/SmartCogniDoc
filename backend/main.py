import os
import base64
import json
import uuid
from pathlib import Path

import pymupdf
import requests
import chromadb
from fastapi import FastAPI, File, UploadFile, HTTPException
from pydantic import BaseModel

# Public-safe defaults: local-only Ollama, no API keys required.
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
VISION_MODEL = os.getenv("VISION_MODEL", "qwen2.5vl:3b")
TEXT_MODEL = os.getenv("TEXT_MODEL", "qwen3:4b")
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "20"))
MAX_PAGES = int(os.getenv("MAX_PAGES", "50"))

app = FastAPI(title="SmartCogniDoc")

Path("data").mkdir(exist_ok=True)
chroma = chromadb.PersistentClient(path="data/chroma")
collection = chroma.get_or_create_collection(
    name="smartcognidoc_documents",
    metadata={"hnsw:space": "cosine"},
)

DOCUMENTS: dict[str, dict] = {}


class AskRequest(BaseModel):
    document_id: str
    question: str


def ollama_chat(model: str, messages: list[dict]) -> str:
    response = requests.post(
        f"{OLLAMA_URL}/api/chat",
        json={"model": model, "messages": messages, "stream": False},
        timeout=300,
    )
    response.raise_for_status()
    return response.json()["message"]["content"]


def ollama_embed(text: str) -> list[float]:
    response = requests.post(
        f"{OLLAMA_URL}/api/embed",
        json={"model": EMBED_MODEL, "input": text},
        timeout=120,
    )
    response.raise_for_status()
    return response.json()["embeddings"][0]


def vision_extract(page) -> str:
    # Lower resolution keeps memory use manageable on an 8 GB Mac.
    pixmap = page.get_pixmap(
        matrix=pymupdf.Matrix(1.25, 1.25),
        alpha=False,
    )
    image_b64 = base64.b64encode(pixmap.tobytes("jpeg")).decode("utf-8")

    return ollama_chat(
        VISION_MODEL,
        [{
            "role": "user",
            "content": (
                "Read this scanned document page. Extract useful text faithfully. "
                "Preserve headings, dates, numbers and important table values. "
                "Do not invent missing information. Return plain text only."
            ),
            "images": [image_b64],
        }],
    )


def extract_page_text(page) -> str:
    # Normal PDFs use PyMuPDF. Vision is used only when extracted text is too short.
    text = page.get_text("text").strip()
    if len(text) >= 30:
        return text
    return vision_extract(page)


def chunk_text(text: str, size: int = 900, overlap: int = 120) -> list[str]:
    text = " ".join(text.split())
    chunks: list[str] = []
    start = 0

    while start < len(text):
        end = min(start + size, len(text))
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start = end - overlap

    return chunks


@app.get("/health")
def health():
    return {
        "status": "ok",
        "project": "SmartCogniDoc",
        "vision_model": VISION_MODEL,
        "llm_model": TEXT_MODEL,
        "embedding_model": EMBED_MODEL,
        "mode": "local",
    }


@app.post("/ingest")
async def ingest(file: UploadFile = File(...)):
    filename = Path(file.filename or "document.pdf").name
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Please upload a PDF.")

    pdf_data = await file.read()
    max_bytes = MAX_UPLOAD_MB * 1024 * 1024
    if len(pdf_data) > max_bytes:
        raise HTTPException(413, f"PDF is larger than {MAX_UPLOAD_MB} MB.")
    if not pdf_data.startswith(b"%PDF"):
        raise HTTPException(400, "The uploaded file is not a valid PDF.")

    try:
        pdf = pymupdf.open(stream=pdf_data, filetype="pdf")
    except Exception as exc:
        raise HTTPException(400, f"Invalid PDF: {exc}") from exc

    try:
        if len(pdf) > MAX_PAGES:
            raise HTTPException(413, f"PDF has more than {MAX_PAGES} pages.")

        document_id = str(uuid.uuid4())
        ids: list[str] = []
        documents: list[str] = []
        embeddings: list[list[float]] = []
        metadatas: list[dict] = []

        for page_number, page in enumerate(pdf, start=1):
            text = extract_page_text(page)

            for chunk_number, chunk in enumerate(chunk_text(text)):
                ids.append(f"{document_id}-{page_number}-{chunk_number}")
                documents.append(chunk)
                embeddings.append(ollama_embed(chunk))
                metadatas.append({
                    "document_id": document_id,
                    "filename": filename,
                    "page": page_number,
                    "chunk": chunk_number,
                })

        if not documents:
            raise HTTPException(400, "No readable content found.")

        collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )

        DOCUMENTS[document_id] = {
            "filename": filename,
            "pages": len(pdf),
        }

        return {
            "document_id": document_id,
            "filename": filename,
            "pages": len(pdf),
            "chunks": len(documents),
        }
    finally:
        pdf.close()


@app.post("/ask")
def ask(request: AskRequest):
    if request.document_id not in DOCUMENTS:
        raise HTTPException(404, "Document not found. Upload it first.")

    question = request.question.strip()
    if not question:
        raise HTTPException(400, "Question cannot be empty.")

    question_vector = ollama_embed(question)

    result = collection.query(
        query_embeddings=[question_vector],
        n_results=5,
        where={"document_id": request.document_id},
    )

    retrieved = result["documents"][0]
    metadata = result["metadatas"][0]

    if not retrieved:
        raise HTTPException(404, "No relevant content found.")

    context = "\n\n".join(
        f"[Page {meta['page']}]\n{doc}"
        for doc, meta in zip(retrieved, metadata)
    )

    prompt = f"""
You are SmartCogniDoc, a local document question-answering assistant.

Answer using ONLY the supplied document context.

Question:
{question}

Document context:
{context}

Rules:
- Do not invent information.
- If the answer is not present, say it is not found in the document.
- Cite relevant page numbers.
- Keep the answer concise.
- Return JSON only:
{{"answer":"your answer","citations":[1,2]}}
"""

    raw = ollama_chat(
        TEXT_MODEL,
        [{"role": "user", "content": prompt}],
    ).strip()

    try:
        cleaned = raw.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(cleaned)
    except Exception:
        parsed = {
            "answer": raw,
            "citations": sorted({int(m["page"]) for m in metadata}),
        }

    return {
        "answer": parsed.get("answer", ""),
        "citations": parsed.get("citations", []),
        "retrieved_pages": sorted({int(m["page"]) for m in metadata}),
    }
