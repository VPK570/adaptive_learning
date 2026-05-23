# Architecture (MVP)

This project is built as a modular MVP for experimenting with RAG and adaptive learning.

## Components
- **Client UI**: Next.js interface.
- **Backend**: FastAPI managing requests, AI integration, and analytics.
- **RAG Engine**: ChromaDB stores vector embeddings for course materials.
- **Storage**: Lightweight local JSON files used for flashcards, quizzes, and chat history.

## Data Flow
1. **Ingestion**: PDFs/text docs are converted into embeddings via OpenRouter and saved in ChromaDB.
2. **Retrieval**: User queries are embedded, compared against ChromaDB, and relevant context is pulled.
3. **Synthesis**: The system combines the retrieved context + prompt + user query and sends it to OpenRouter for an AI-generated response.

## Key Design Principles
- **Modular**: Backend/Frontend separation makes it easy to experiment with new components.
- **Extensible**: Designed to allow students to swap out LLMs or add new RAG techniques.
- **Simple**: Uses local storage where possible to avoid complex database management.
