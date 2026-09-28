# SmartCogniDoc

## Local Vision-RAG Document Intelligence

SmartCogniDoc is a SwiftUI + Python/FastAPI document assistant that runs its AI pipeline locally with Ollama. It supports text PDFs and scanned PDFs, semantic retrieval with ChromaDB, grounded question answering with Qwen models, and page-level citations.

### Architecture

```text
SwiftUI
   ↓
FastAPI
   ↓
PDF extraction / Qwen2.5-VL for scanned pages
   ↓
Python chunking
   ↓
Ollama + nomic-embed-text
   ↓
ChromaDB
   ↓
Semantic retrieval
   ↓
Ollama + Qwen3
   ↓
Answer + page citations
```

### Components

| Part | Technology | Responsibility |
|---|---|---|
| PDF extraction | PyMuPDF | Reads text from normal PDFs |
| Scanned pages | Qwen2.5-VL via Ollama | Reads page images |
| Chunking | Python | Splits text into retrieval chunks |
| Embeddings | nomic-embed-text via Ollama | Converts chunks/questions to vectors |
| Vector store | ChromaDB | Stores vectors, text and metadata |
| Retrieval | ChromaDB | Finds relevant chunks |
| Generation | Qwen3 via Ollama | Produces grounded answers |
| iOS UI | SwiftUI | Uploads PDFs and displays answers |

## Requirements

- macOS
- Xcode
- Python 3
- Ollama
- iPhone Simulator or iPhone

For small local models, start with short PDFs and avoid running multiple heavy models simultaneously on machines with limited memory.

## 1. Install Ollama

Install Ollama from its official website:

https://ollama.com/

Verify:

```bash
ollama --version
ollama list
```

Pull the models:

```bash
ollama pull qwen2.5vl:3b
ollama pull qwen3:4b
ollama pull nomic-embed-text
```

## 2. Run the backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 127.0.0.1 --port 8000
```

Test it:

```bash
curl http://127.0.0.1:8000/health
```

## 3. Run the iOS app

Create or open a SwiftUI iOS project in Xcode and add:

```text
ios/SmartCogniDoc/
├── SmartCogniDocApp.swift
├── AppConfig.swift
├── ContentView.swift
├── APIClient.swift
└── Models.swift
```

For the iPhone Simulator, the default API URL is:

```text
http://127.0.0.1:8000
```

### Physical iPhone

For a physical iPhone, change `AppConfig.swift` locally to your Mac's LAN address. Do not commit your personal LAN address:

```swift
static let apiBaseURL = URL(string: "http://YOUR-MAC-LAN-IP:8000")!
```

Run FastAPI for LAN access:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

You may need local-network permission and an iOS development ATS exception for HTTP.

Keep Ollama bound to localhost. Do not expose port `11434` directly to the internet.

## 4. Use the app

1. Start Ollama.
2. Start FastAPI.
3. Run SmartCogniDoc in Simulator.
4. Tap **Upload PDF**.
5. Select a PDF through the iOS document picker.
6. Wait for ingestion and RAG indexing.
7. Ask a question.
8. The app displays the answer and source pages.

### RAG pipeline

```text
PDF
 ↓
Extract text / Vision
 ↓
Python chunking
 ↓
Embedding with nomic-embed-text
 ↓
ChromaDB
 ↓
Question embedding
 ↓
Top relevant chunks
 ↓
Qwen3
 ↓
Grounded answer + citations
```

## 5. Public repository safety

This repository contains application source code and local-development configuration only. It does not contain a cloud API key, user documents, local vector-store data, or machine-specific paths.

Before publishing, run:

```bash
git status
git ls-files
git grep -n -I -E 'AIza|api[_-]?key|secret|token|password|BEGIN (RSA|OPENSSH|EC|PRIVATE)'
```

If a real secret is ever committed, revoke or rotate it immediately. Removing it from the latest file does not remove it from Git history.

Local document data is stored under:

```text
backend/data/chroma/
```

and is intentionally ignored by Git.

## 6. Project ownership and third-party software

The original source files in this repository are released under the MIT License included in this repository.

The project uses third-party software and model packages, including FastAPI, PyMuPDF, Requests, ChromaDB, Pydantic, Ollama, Qwen models and `nomic-embed-text`. Those third-party components remain subject to their respective licenses and terms. This repository does not claim ownership of those third-party components.

## Portfolio description

**SmartCogniDoc — Local Vision-RAG Document Intelligence**

Built a privacy-focused local document intelligence platform using SwiftUI, Python/FastAPI, Ollama, Vision LLMs, embeddings and ChromaDB. Implemented scanned-document understanding, semantic retrieval, grounded local LLM responses and page-level citations.

## About
Atreyee P.

Senior iOS Developer exploring Generative AI and Agentic AI.

