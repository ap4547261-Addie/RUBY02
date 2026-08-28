import os
from google import genai
from google.genai import types

class DataIngestion:
    def __init__(self, api_key=None):
        self.client = genai.Client(api_key=api_key or os.environ.get("GEMINI_API_KEY"))

    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
        """Splits large text documents into overlapping segments for processing and indexing."""
        if not text:
            return []
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunks.append(text[start:end])
            start += chunk_size - overlap
        return chunks

    def generate_embeddings(self, texts: list[str]) -> list:
        """Transforms text chunks into vector embeddings using Google's text-embedding model."""
        if not texts:
            return []
        response = self.client.models.embed_content(
            model="text-embedding-004",
            contents=texts
        )
        return [embedding.values for embedding in response.embeddings]

    def process_document(self, file_path: str) -> list[dict]:
        """Reads a local file, splits it into chunks, and prepares vector payloads."""
        if not os.path.exists(file_path):
            return []
            
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            
        chunks = self.chunk_text(content)
        vectors = self.generate_embeddings(chunks)
        
        processed_data = []
        for i, (chunk, vector) in enumerate(zip(chunks, vectors)):
            processed_data.append({
                "id": f"{os.path.basename(file_path)}_chunk_{i}",
                "text": chunk,
                "values": vector
            })
        return processed_data
      
