import os
from tika import parser
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
import chromadb
import re
import torch

class DocumentProcessor:
    def __init__(self):
        self.embedding_model = None
        self.chroma_client = None
        self.collection = None
        self.load_embedding_model()
        self.connect_to_chromadb()

    def load_embedding_model(self):
        print("INFO:document_processor:Loading embedding model: all-MiniLM-L6-v2")
        # Explicitly set device to CPU to avoid MPS meta tensor issues
        self.embedding_model = SentenceTransformer(
            'all-MiniLM-L6-v2',
            device='cpu' # Force CPU to avoid MPS meta tensor error
        )

    def connect_to_chromadb(self):
        print("INFO:document_processor:Connecting to ChromaDB at: ./chroma_db")
        self.chroma_client = chromadb.PersistentClient(path="./chroma_db")
        self.collection = self.chroma_client.get_or_create_collection(name="dafman_documents")

    def process_document(self, pdf_path: str) -> Dict[str, Any]:
        print(f"INFO:__main__:Extracting text from {pdf_path}")
        try:
            parsed_pdf = parser.from_file(pdf_path)
            text = parsed_pdf["content"]
            if not text:
                raise ValueError("Could not extract text from PDF.")

            # Clean and chunk text
            cleaned_text = self.clean_text(text)
            chunks = self.chunk_text(cleaned_text)

            # Store chunks in ChromaDB
            self.store_chunks_in_chromadb(chunks, pdf_path)

            return {
                "status": "success",
                "total_chunks": len(chunks),
                "total_characters": len(cleaned_text),
                "embedding_dimension": self.embedding_model.get_sentence_embedding_dimension(),
                "average_chunk_size": sum(len(c["text"]) for c in chunks) / len(chunks) if chunks else 0
            }
        except Exception as e:
            print(f"ERROR:__main__:Error extracting text from PDF: {e}")
            return {"status": "error", "error": str(e)}

    def clean_text(self, text: str) -> str:
        # Remove multiple newlines and replace with single space
        text = re.sub(r'\n\s*\n', '\n', text)
        # Remove page numbers, headers, footers (often at top/bottom of pages)
        # This is a generic attempt; may need fine-tuning for specific documents
        text = re.sub(r'\s*Page \d+ of \d+\s*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\s*DAFMAN 36-2664\s*', '', text, flags=re.IGNORECASE)
        return text.strip()

    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 100) -> List[Dict[str, Any]]:
        chunks = []
        words = text.split()
        current_chunk = []
        current_length = 0
        chunk_id_counter = 0

        for word in words:
            word_length = len(word) + 1  # +1 for space
            if current_length + word_length > chunk_size and current_chunk:
                chunks.append({
                    "id": f"chunk_{chunk_id_counter}",
                    "text": " ".join(current_chunk),
                    "metadata": {}
                })
                chunk_id_counter += 1
                # Create overlap
                current_chunk = current_chunk[-int(overlap / (chunk_size / len(current_chunk))):] if current_chunk else []
                current_length = sum(len(w) + 1 for w in current_chunk)

            current_chunk.append(word)
            current_length += word_length

        if current_chunk:
            chunks.append({
                "id": f"chunk_{chunk_id_counter}",
                "text": " ".join(current_chunk),
                "metadata": {}
            })

        return chunks

    def store_chunks_in_chromadb(self, chunks: List[Dict[str, Any]], source_doc: str):
        documents = [chunk["text"] for chunk in chunks]
        metadatas = []
        for chunk in chunks:
            # Ensure metadata values are not None
            metadata = {
                "source": source_doc,
                "chunk_id": chunk["id"],
            }
            # Only add page_number if it exists and is not None
            if "page_number" in chunk["metadata"] and chunk["metadata"]["page_number"] is not None:
                metadata["page_number"] = str(chunk["metadata"]["page_number"]) # Ensure it's a string
            else:
                metadata["page_number"] = "N/A" # Provide a default string value
            metadatas.append(metadata)

        ids = [chunk["id"] for chunk in chunks]

        # Generate embeddings
        print("INFO:document_processor:Generating embeddings for chunks...")
        embeddings = self.embedding_model.encode(documents).tolist()

        # Add to ChromaDB
        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings,
            ids=ids
        )
        print(f"INFO:__main__:Stored {len(documents)} documents in vector database")

# For testing purposes
if __name__ == "__main__":
    processor = DocumentProcessor()
    # Ensure the PDF is in the parent directory or provide the full path
    result = processor.process_document("../dafman36-2664.pdf")
    print(f"Processing result: {result}")
