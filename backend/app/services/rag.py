from pathlib import Path
from typing import Any
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from pypdf import PdfReader
from app.core.config import get_settings
from app.services.ollama import OllamaService


class RagService:
    def __init__(self) -> None:
        self.settings = get_settings()
        Path(self.settings.chroma_path).mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=self.settings.chroma_path)
        self.embedding_function = SentenceTransformerEmbeddingFunction(model_name=self.settings.embedding_model)
        self.collection = self.client.get_or_create_collection(
            name="clinic_documents",
            embedding_function=self.embedding_function,
        )
        self.ollama = OllamaService()

    def extract_text(self, filename: str, content: bytes) -> str:
        suffix = Path(filename).suffix.lower()
        if suffix == ".pdf":
            tmp_path = Path(self.settings.chroma_path) / f"upload-{filename}"
            tmp_path.write_bytes(content)
            reader = PdfReader(str(tmp_path))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        return content.decode("utf-8", errors="ignore")

    def chunk_text(self, text: str, chunk_size: int = 900, overlap: int = 120) -> list[str]:
        clean = " ".join(text.split())
        if not clean:
            return []
        chunks: list[str] = []
        start = 0
        while start < len(clean):
            end = start + chunk_size
            chunks.append(clean[start:end])
            start = max(end - overlap, end)
        return chunks

    def add_document(self, filename: str, content: bytes, uploaded_by: int) -> int:
        text = self.extract_text(filename, content)
        chunks = self.chunk_text(text)
        if not chunks:
            return 0
        ids = [f"{filename}-{uploaded_by}-{idx}" for idx in range(len(chunks))]
        self.collection.upsert(
            ids=ids,
            documents=chunks,
            metadatas=[{"source": filename, "uploaded_by": uploaded_by} for _ in chunks],
        )
        return len(chunks)

    def search(self, query: str, limit: int = 4) -> list[dict[str, Any]]:
        result = self.collection.query(query_texts=[query], n_results=limit)
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]
        chunks: list[dict[str, Any]] = []
        for doc, metadata, distance in zip(documents, metadatas, distances, strict=False):
            chunks.append({"text": doc, "source": metadata.get("source", "unknown"), "score": distance})
        return chunks

    async def answer(self, query: str) -> tuple[str, list[dict[str, Any]]]:
        chunks = self.search(query)
        context = "\n\n".join(f"Source: {chunk['source']}\n{chunk['text']}" for chunk in chunks)
        if not context:
            return "I could not find matching clinic documents. Please upload relevant documents first.", []
        prompt = f"""
Use only the document context below. If the answer is not in the context, say that the uploaded documents do not contain enough information.

Question: {query}

Context:
{context}
"""
        answer = await self.ollama.generate(prompt, system="You answer clinic document questions clearly and briefly.")
        return answer, chunks


rag_service = RagService()
