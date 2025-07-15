import os
import torch
from sentence_transformers import SentenceTransformer
import chromadb
from typing import List, Dict, Any

# Import Groq client
from groq import Groq

class RAGPipeline:
    def __init__(self):
        self.embedding_model = None
        self.chroma_client = None
        self.collection = None
        self.groq_client = None
        self.is_ready = False
        self.load_pipeline()

    def load_pipeline(self):
        try:
            # 1. Load Embedding Model
            print("INFO:src.rag_pipeline:Loading embedding model: all-MiniLM-L6-v2")
            # Explicitly set device to CPU to avoid MPS meta tensor issues
            self.embedding_model = SentenceTransformer(
                'all-MiniLM-L6-v2',
                device='cpu' # Force CPU to avoid MPS meta tensor error
            )

            # 2. Connect to ChromaDB
            print("INFO:src.rag_pipeline:Connecting to ChromaDB at: ./chroma_db")
            self.chroma_client = chromadb.PersistentClient(path="./chroma_db")
            self.collection = self.chroma_client.get_or_create_collection(name="dafman_documents")

            # 3. Initialize Groq Client
            groq_api_key = "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"
            self.groq_client = Groq(api_key=groq_api_key)
            print("INFO:src.rag_pipeline:Groq client initialized.")

            self.is_ready = True
            print("INFO:src.rag_pipeline:RAG pipeline initialized successfully")

        except Exception as e:
            self.is_ready = False
            print(f"ERROR:src.rag_pipeline:Error initializing RAG pipeline: {e}")

    def retrieve_documents(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        if not self.is_ready:
            return []
        
        query_embedding = self.embedding_model.encode(query).tolist()
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=["documents", "metadatas", "distances"]
        )
        
        # Format results for easier use
        formatted_results = []
        if results and results["documents"]:
            for i in range(len(results["documents"][0])):
                formatted_results.append({
                    "document": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i]
                })
        return formatted_results

    def generate_response(self, query: str, context: List[str]) -> str:
        if not self.is_ready or not self.groq_client:
            return "I am currently initializing. Please try again in a moment."

        # Construct the prompt for the LLM
        system_prompt = "You are an AI assistant specialized in Air Force policy and logistics compliance. Answer the user's question based ONLY on the provided context. If the answer is not in the context, state that you cannot find the information. Do not make up answers."
        
        context_str = "\n\nContext:\n" + "\n".join(context)
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"{query}{context_str}"},
        ]

        try:
            chat_completion = self.groq_client.chat.completions.create(
                messages=messages,
                model="llama3-8b-8192", # Using a common Groq-supported model.
                temperature=0.7,
                max_tokens=512,
            )
            response = chat_completion.choices[0].message.content
            return response
        except Exception as e:
            print(f"ERROR:src.rag_pipeline:Error calling Groq API: {e}")
            return f"Error generating response from AI: {e}"

    def query(self, user_query: str, n_results: int = 5) -> Dict[str, Any]:
        if not self.is_ready:
            return {
                "response": "I am currently initializing. Please try again in a moment.",
                "sources": [],
                "status": "mock_response"
            }

        retrieved_docs = self.retrieve_documents(user_query, n_results)
        
        context = [doc["document"] for doc in retrieved_docs]
        sources = [{
            "source": doc["metadata"].get("source", "Unknown"),
            "chunk_id": doc["metadata"].get("chunk_id", "N/A"),
            "preview": doc["document"][:200] + "..." if len(doc["document"]) > 200 else doc["document"],
            "distance": doc["distance"]
        } for doc in retrieved_docs]

        generated_answer = self.generate_response(user_query, context)

        return {
            "response": generated_answer,
            "sources": sources,
            "status": "success"
        }

# For testing purposes (optional, can be removed in production)
if __name__ == "__main__":
    rag_pipeline = RAGPipeline()
    if rag_pipeline.is_ready:
        print("RAG Pipeline is ready. Testing a query...")
        test_query = "What are the responsibilities of a selection board president?"
        response = rag_pipeline.query(test_query)
        print(f"\nQuery: {test_query}")
        print(f"Response: {response["response"]}")
        print("Sources:")
        for source in response["sources"]:
            print(f"  - {source["source"]} (Chunk {source["chunk_id"]}): {source["preview"]}")
    else:
        print("RAG Pipeline failed to initialize. Check logs for errors.")
