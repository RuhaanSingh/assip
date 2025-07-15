"""
Document processor for extracting text from PDFs using Apache Tika
and preparing it for vector database storage.
"""

import os
import re
from typing import List, Dict, Any
from tika import parser
import chromadb
from sentence_transformers import SentenceTransformer
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self, embedding_model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the document processor with embedding model.
        
        Args:
            embedding_model_name: Name of the sentence transformer model to use
        """
        self.embedding_model = SentenceTransformer(embedding_model_name)
        self.chroma_client = chromadb.PersistentClient(path="./chroma_db")
        self.collection = None
        
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extract text from PDF using Apache Tika.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text content
        """
        try:
            logger.info(f"Extracting text from {pdf_path}")
            parsed = parser.from_file(pdf_path)
            text = parsed['content']
            
            if not text:
                raise ValueError("No text content extracted from PDF")
                
            logger.info(f"Successfully extracted {len(text)} characters")
            return text
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            raise
    
    def clean_text(self, text: str) -> str:
        """
        Clean and normalize extracted text.
        
        Args:
            text: Raw extracted text
            
        Returns:
            Cleaned text
        """
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove page numbers and headers/footers patterns
        text = re.sub(r'Page \d+ of \d+', '', text)
        text = re.sub(r'DAFMAN\s+\d+-\d+', '', text)
        
        # Remove excessive line breaks
        text = re.sub(r'\n\s*\n', '\n', text)
        
        return text.strip()
    
    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 100) -> List[Dict[str, Any]]:
        """
        Split text into overlapping chunks for better retrieval.
        
        Args:
            text: Text to chunk
            chunk_size: Maximum size of each chunk
            overlap: Number of characters to overlap between chunks
            
        Returns:
            List of chunk dictionaries with metadata
        """
        chunks = []
        
        # Split by paragraphs first
        paragraphs = text.split('\n')
        
        current_chunk = ""
        chunk_id = 0
        
        for paragraph in paragraphs:
            # If adding this paragraph would exceed chunk size, save current chunk
            if len(current_chunk) + len(paragraph) > chunk_size and current_chunk:
                chunks.append({
                    'id': f"chunk_{chunk_id}",
                    'text': current_chunk.strip(),
                    'metadata': {
                        'chunk_id': chunk_id,
                        'source': 'DAFMAN 36-2664',
                        'length': len(current_chunk.strip())
                    }
                })
                
                # Start new chunk with overlap
                overlap_text = current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk
                current_chunk = overlap_text + " " + paragraph
                chunk_id += 1
            else:
                current_chunk += " " + paragraph if current_chunk else paragraph
        
        # Add the last chunk
        if current_chunk.strip():
            chunks.append({
                'id': f"chunk_{chunk_id}",
                'text': current_chunk.strip(),
                'metadata': {
                    'chunk_id': chunk_id,
                    'source': 'DAFMAN 36-2664',
                    'length': len(current_chunk.strip())
                }
            })
        
        logger.info(f"Created {len(chunks)} text chunks")
        return chunks
    
    def create_embeddings(self, chunks: List[Dict[str, Any]]) -> List[List[float]]:
        """
        Create embeddings for text chunks.
        
        Args:
            chunks: List of text chunks
            
        Returns:
            List of embedding vectors
        """
        texts = [chunk['text'] for chunk in chunks]
        logger.info(f"Creating embeddings for {len(texts)} chunks")
        
        embeddings = self.embedding_model.encode(texts, show_progress_bar=True)
        return embeddings.tolist()
    
    def setup_vector_database(self, collection_name: str = "dafman_documents"):
        """
        Set up ChromaDB collection for storing document embeddings.
        
        Args:
            collection_name: Name of the collection
        """
        try:
            # Delete existing collection if it exists
            try:
                self.chroma_client.delete_collection(name=collection_name)
                logger.info(f"Deleted existing collection: {collection_name}")
            except:
                pass
            
            # Create new collection
            self.collection = self.chroma_client.create_collection(
                name=collection_name,
                metadata={"description": "DAFMAN 36-2664 Personnel Assessment Program"}
            )
            logger.info(f"Created new collection: {collection_name}")
            
        except Exception as e:
            logger.error(f"Error setting up vector database: {e}")
            raise
    
    def store_documents(self, chunks: List[Dict[str, Any]], embeddings: List[List[float]]):
        """
        Store document chunks and embeddings in ChromaDB.
        
        Args:
            chunks: List of text chunks with metadata
            embeddings: List of embedding vectors
        """
        if not self.collection:
            raise ValueError("Vector database collection not initialized")
        
        try:
            # Prepare data for ChromaDB
            ids = [chunk['id'] for chunk in chunks]
            documents = [chunk['text'] for chunk in chunks]
            metadatas = [chunk['metadata'] for chunk in chunks]
            
            # Add to collection
            self.collection.add(
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"Stored {len(chunks)} documents in vector database")
            
        except Exception as e:
            logger.error(f"Error storing documents: {e}")
            raise
    
    def process_document(self, pdf_path: str) -> Dict[str, Any]:
        """
        Complete document processing pipeline.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Processing results summary
        """
        try:
            # Extract text
            raw_text = self.extract_text_from_pdf(pdf_path)
            
            # Clean text
            cleaned_text = self.clean_text(raw_text)
            
            # Create chunks
            chunks = self.chunk_text(cleaned_text)
            
            # Create embeddings
            embeddings = self.create_embeddings(chunks)
            
            # Setup vector database
            self.setup_vector_database()
            
            # Store documents
            self.store_documents(chunks, embeddings)
            
            return {
                'status': 'success',
                'total_chunks': len(chunks),
                'total_characters': len(cleaned_text),
                'embedding_dimension': len(embeddings[0]) if embeddings else 0
            }
            
        except Exception as e:
            logger.error(f"Document processing failed: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }

if __name__ == "__main__":
    # Test the document processor
    processor = DocumentProcessor()
    result = processor.process_document("../dafman36-2664.pdf")
    print(f"Processing result: {result}")

