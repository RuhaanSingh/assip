"""
Chatbot API routes for the RAG-powered Air Force policy compliance chatbot.
"""

import os
import sys
import logging
from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
import pandas as pd

# Add the 'src' directory to sys.path so imports from src/*.py work
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))  # Points to root/src

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

chatbot_bp = Blueprint('chatbot', __name__)

# Global variables for lazy loading
rag_pipeline = None
document_processor = None

def get_rag_pipeline():
    """Lazy load the RAG pipeline to avoid startup delays."""
    global rag_pipeline
    if rag_pipeline is None:
        try:
            from rag_pipeline import RAGPipeline  # No src. prefix now
            rag_pipeline = RAGPipeline()
            logger.info("RAG pipeline loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load RAG pipeline: {e}")
            # Return a mock pipeline for development
            rag_pipeline = MockRAGPipeline()
    return rag_pipeline

def get_document_processor():
    """Lazy load the document processor."""
    global document_processor
    if document_processor is None:
        try:
            from document_processor_v2 import DocumentProcessor  # No src. prefix
            document_processor = DocumentProcessor()
            logger.info("Document processor loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load document processor: {e}")
            document_processor = None
    return document_processor

class MockRAGPipeline:
    """Mock RAG pipeline for development when models aren't available."""
    
    def query(self, user_query: str, n_results: int = 5):
        return {
            'response': f"This is a mock response for the query: '{user_query}'. The RAG pipeline is not fully loaded yet. Please ensure the document processing is complete and the models are properly installed.",
            'sources': [
                {
                    'chunk_id': 'mock_chunk_1',
                    'source': 'DAFMAN 36-2664',
                    'distance': 0.5,
                    'preview': 'This is a mock document chunk preview...'
                }
            ],
            'status': 'mock_response',
            'query': user_query
        }

@chatbot_bp.route('/query', methods=['POST'])
@cross_origin()
def query_chatbot():
    """
    Handle chatbot queries using the RAG pipeline.
    
    Expected JSON payload:
    {
        "query": "What are the responsibilities of a selection board president?",
        "n_results": 5  # optional, defaults to 5
    }
    """
    try:
        # Get request data
        data = request.get_json()
        
        if not data or 'query' not in data:
            return jsonify({
                'error': 'Missing required field: query',
                'status': 'error'
            }), 400
        
        user_query = data['query'].strip()
        n_results = data.get('n_results', 5)
        
        if not user_query:
            return jsonify({
                'error': 'Query cannot be empty',
                'status': 'error'
            }), 400
        
        # Validate n_results
        if not isinstance(n_results, int) or n_results < 1 or n_results > 20:
            n_results = 5
        
        logger.info(f"Processing query: {user_query}")
        
        # Get RAG pipeline and process query
        rag = get_rag_pipeline()
        result = rag.query(user_query, n_results)
        
        # Add request metadata
        import pandas as pd  # Import here to avoid errors if not installed globally
        result['timestamp'] = str(pd.Timestamp.now()) if 'pd' in globals() else 'unknown'
        result['n_results_requested'] = n_results
        
        logger.info(f"Query processed successfully. Status: {result.get('status', 'unknown')}")
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error processing chatbot query: {e}")
        return jsonify({
            'error': 'Internal server error while processing query',
            'status': 'error',
            'details': str(e)
        }), 500

@chatbot_bp.route('/status', methods=['GET'])
@cross_origin()
def get_status():
    """Get the current status of the chatbot system."""
    try:
        status = {
            'system': 'operational',
            'components': {}
        }
        
        # Check document processor
        try:
            processor = get_document_processor()
            if processor:
                status['components']['document_processor'] = 'loaded'
            else:
                status['components']['document_processor'] = 'not_loaded'
        except Exception as e:
            status['components']['document_processor'] = f'error: {str(e)}'
        
        # Check RAG pipeline
        try:
            rag = get_rag_pipeline()
            if isinstance(rag, MockRAGPipeline):
                status['components']['rag_pipeline'] = 'mock_mode'
            else:
                status['components']['rag_pipeline'] = 'loaded'
        except Exception as e:
            status['components']['rag_pipeline'] = f'error: {str(e)}'
        
        # Check vector database
        try:
            import chromadb
            chroma_client = chromadb.PersistentClient(path="./chroma_db")
            collections = chroma_client.list_collections()
            if collections:
                collection = chroma_client.get_collection("dafman_documents")
                count = collection.count()
                status['components']['vector_database'] = f'ready ({count} documents)'
            else:
                status['components']['vector_database'] = 'no_collections'
        except Exception as e:
            status['components']['vector_database'] = f'error: {str(e)}'
        
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        return jsonify({
            'error': 'Failed to get system status',
            'status': 'error',
            'details': str(e)
        }), 500

@chatbot_bp.route('/process-document', methods=['POST'])
@cross_origin()
def process_document():
    """
    Trigger document processing for the DAFMAN PDF.
    This endpoint can be used to reprocess the document if needed.
    """
    try:
        processor = get_document_processor()
        
        if not processor:
            return jsonify({
                'error': 'Document processor not available',
                'status': 'error'
            }), 500
        
        # Process the DAFMAN document
        pdf_path = "../dafman36-2664.pdf"
        
        if not os.path.exists(pdf_path):
            return jsonify({
                'error': 'DAFMAN PDF file not found',
                'status': 'error'
            }), 404
        
        logger.info("Starting document processing...")
        result = processor.process_document(pdf_path)
        
        logger.info(f"Document processing completed. Status: {result.get('status', 'unknown')}")
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error processing document: {e}")
        return jsonify({
            'error': 'Failed to process document',
            'status': 'error',
            'details': str(e)
        }), 500

@chatbot_bp.route('/health', methods=['GET'])
@cross_origin()
def health_check():
    """Simple health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'rag-chatbot-api',
        'version': '1.0.0'
    })

# Error handlers
@chatbot_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Endpoint not found',
        'status': 'error'
    }), 404

@chatbot_bp.errorhandler(500)
def internal_error(error):
    return jsonify({
        'error': 'Internal server error',
        'status': 'error'
    }), 500
