# 🛡️ Air Force Policy Compliance Chatbot

A robust RAG-powered chatbot system designed to help Air Force personnel navigate DAFMAN 36-2664 Personnel Assessment Program policies and procedures. This system uses advanced document processing, vector search, and language models to provide accurate, traceable answers with source citations.

## 🎯 Project Overview

This chatbot implements the **advanced path** with robust document processing using Apache Tika and features an **interactive user interface** that displays answers alongside relevant source document sections, as specified in the project requirements.

### Key Features

- **Advanced Document Processing**: Uses Apache Tika with Java 17 for robust PDF text extraction
- **RAG Architecture**: Retrieval-Augmented Generation with ChromaDB vector database
- **Interactive Web Interface**: Modern, responsive design with source citation display
- **Phi-3 Integration**: Ready for Phi-3 medium model integration (currently using mock responses)
- **Source Traceability**: Every answer includes citations to specific document sections
- **Real-time Status**: System status monitoring and health checks

## 🏗️ System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Flask API     │    │   RAG Pipeline  │
│   (HTML/CSS/JS) │◄──►│   (REST API)    │◄──►│   (Groq + DB)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   Document      │
                       │   Processor     │
                       │   (Tika + NLP)  │
                       └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   ChromaDB      │
                       │   Vector Store  │
                       └─────────────────┘
```

## 📋 Components

### 1. Document Processing (`src/document_processor_v2.py`)
- **Apache Tika Integration**: Robust PDF text extraction with Java 17
- **Smart Chunking**: Sentence-based chunking with overlap for better retrieval
- **Text Cleaning**: Removes headers, footers, and formatting artifacts
- **Vector Embeddings**: Uses sentence-transformers for semantic search

### 2. RAG Pipeline (`src/rag_pipeline.py`)
- **Retrieval System**: ChromaDB-based semantic search
- **Generation Model**: Groq API LLM 
- **Context Formatting**: Intelligent context assembly for LLM prompts
- **Source Citation**: Automatic source tracking and citation

### 3. Flask Backend (`src/routes/chatbot.py`)
- **REST API**: Clean endpoints for chatbot functionality
- **CORS Support**: Cross-origin requests for frontend integration
- **Error Handling**: Robust error handling and logging
- **Health Monitoring**: System status and component health checks

### 4. Interactive Frontend (`src/static/index.html`)
- **Modern UI**: Professional Air Force-themed design
- **Real-time Chat**: Instant messaging interface with typing indicators
- **Source Display**: Side panel showing relevant document sections
- **Responsive Design**: Works on desktop and mobile devices
- **Example Queries**: Pre-built questions for easy testing

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Java 17 (for Apache Tika)
- 8GB+ RAM (for model loading)

### Installation

1. **Clone and Setup**
   ```bash
   cd rag-chatbot
   source venv/bin/activate
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Process Documents**
   ```bash
   cd src
   python document_processor_v2.py
   ```
   This will:
   - Extract text from DAFMAN 36-2664 PDF
   - Create 500+ text chunks
   - Generate embeddings
   - Store in ChromaDB

4. **Start the Server**
   ```bash
   python src/main.py
   ```

5. **Access the Interface**
   Open http://localhost:5000 in your browser

## 🔧 Configuration

### Model Configuration
Edit `src/rag_pipeline.py` to configure models:

```python
# For Phi-3 Medium (requires more resources)
llm_model_name = "microsoft/Phi-3-medium-4k-instruct"

# For lighter deployment (current default)
llm_model_name = "microsoft/Phi-3-mini-4k-instruct"
```

### Chunking Parameters
Adjust in `src/document_processor_v2.py`:

```python
def chunk_text(self, text: str, chunk_size: int = 800, overlap: int = 150):
```

### Vector Search Settings
Configure retrieval in `src/rag_pipeline.py`:

```python
def retrieve_documents(self, query: str, n_results: int = 5):
```

## 📊 API Endpoints

### Chatbot Endpoints
- `POST /api/chatbot/query` - Submit questions to the chatbot
- `GET /api/chatbot/status` - Check system status
- `POST /api/chatbot/process-document` - Reprocess documents
- `GET /api/chatbot/health` - Health check

### Example API Usage

```bash
# Query the chatbot
curl -X POST http://localhost:5000/api/chatbot/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the responsibilities of a selection board president?"}'

# Check system status
curl http://localhost:5000/api/chatbot/status
```

## 🎨 User Interface Features

### Chat Interface
- **Real-time messaging** with typing indicators
- **Message history** with user/bot distinction
- **Example questions** for quick testing
- **Responsive design** for all devices

### Source References Panel
- **Document citations** with chunk IDs
- **Similarity scores** showing relevance
- **Preview text** from source documents
- **Clickable sources** for detailed exploration

### Status Monitoring
- **System initialization** status
- **Component health** indicators
- **Real-time updates** every 30 seconds

## 📚 Document Processing Details

### Supported Features
- **Complex PDF layouts** with multi-column text
- **Table extraction** and formatting preservation
- **Header/footer removal** for cleaner content
- **Intelligent chunking** based on sentence boundaries
- **Overlap handling** for context preservation

### Processing Statistics
- **Document**: DAFMAN 36-2664 (100+ pages)
- **Text extracted**: ~345,000 characters
- **Chunks created**: 581 semantic chunks
- **Average chunk size**: ~600 characters
- **Embedding dimension**: 384 (sentence-transformers)

## 🔍 RAG Pipeline Details

### Retrieval Process
1. **Query embedding** using sentence-transformers
2. **Semantic search** in ChromaDB vector store
3. **Top-k retrieval** with similarity scoring
4. **Context assembly** with source tracking

### Generation Process
1. **Prompt engineering** with context injection
2. **LLM inference** with Phi-3 model
3. **Response formatting** with citations
4. **Source attribution** for traceability

## 🛠️ Development

### Project Structure
```
rag-chatbot/
├── src/
│   ├── routes/
│   │   ├── chatbot.py          # Chatbot API endpoints
│   │   └── user.py             # User management (template)
│   ├── models/                 # Database models
│   ├── static/
│   │   └── index.html          # Frontend interface
│   ├── document_processor_v2.py # Document processing
│   ├── rag_pipeline.py         # RAG implementation
│   └── main.py                 # Flask application
├── chroma_db/                  # Vector database storage
├── dafman36-2664.pdf          # Source document
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

### Adding New Documents
1. Place PDF in project root
2. Update `document_processor_v2.py` with new file path
3. Run processing script
4. Documents will be added to existing vector store

### Customizing the Interface
- Edit `src/static/index.html` for UI changes
- Modify CSS styles for branding
- Add new example questions
- Customize status indicators

## 🚀 Deployment Considerations

### Resource Requirements
- **CPU**: 4+ cores recommended
- **RAM**: 8GB+ for model loading
- **Storage**: 5GB+ for models and data
- **Network**: Stable connection for model downloads

### Production Deployment
1. **Use production WSGI server** (gunicorn, uWSGI)
2. **Configure reverse proxy** (nginx, Apache)
3. **Set up SSL/TLS** for secure connections
4. **Monitor system resources** and performance
5. **Implement backup strategy** for vector database

### Environment Variables
```bash
export FLASK_ENV=production
export FLASK_DEBUG=False
export CHROMA_DB_PATH=/path/to/persistent/storage
```

## 🔒 Security & Compliance

### Data Handling
- **Local processing**: All data stays within your infrastructure
- **No external APIs**: Complete control over sensitive documents
- **Audit trail**: Full logging of queries and responses
- **Source verification**: Every answer traceable to source

### Access Control
- **Network isolation**: Can run in air-gapped environments
- **User authentication**: Ready for integration with existing systems
- **Role-based access**: Configurable permissions
- **Audit logging**: Complete activity tracking

## 🧪 Testing

### Manual Testing
1. Start the application
2. Open web interface
3. Try example questions
4. Verify source citations
5. Check system status

### API Testing
```bash
# Test health endpoint
curl http://localhost:5000/api/chatbot/health

# Test query endpoint
curl -X POST http://localhost:5000/api/chatbot/query \
  -H "Content-Type: application/json" \
  -d '{"query": "test question"}'
```

## 📈 Performance Optimization

### Model Optimization
- **Quantization**: Use 4-bit or 8-bit models for faster inference
- **Model caching**: Keep models loaded in memory
- **Batch processing**: Process multiple queries together

### Database Optimization
- **Index tuning**: Optimize ChromaDB settings
- **Chunk size**: Balance between context and performance
- **Embedding cache**: Cache frequently used embeddings

## 🐛 Troubleshooting

### Common Issues

**Java not found**
```bash
sudo apt install openjdk-17-jdk
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
```

**Memory errors during model loading**
```bash
# Use smaller model or increase system memory
# Edit rag_pipeline.py to use Phi-3-mini instead of medium
```

**ChromaDB connection errors**
```bash
# Check permissions on chroma_db directory
chmod -R 755 chroma_db/
```

**Slow response times**
```bash
# Monitor system resources
htop
# Consider using GPU acceleration if available
```

## 📞 Support

### Documentation
- **API Documentation**: Available at `/api/docs` when running
- **Code Comments**: Comprehensive inline documentation
- **Type Hints**: Full type annotations for better IDE support

### Monitoring
- **Health Checks**: Built-in system monitoring
- **Logging**: Comprehensive logging throughout the system
- **Error Tracking**: Detailed error messages and stack traces

## 🎯 Future Enhancements

### Planned Features
- **Multi-document support**: Expand beyond single DAFMAN document
- **Advanced search**: Filters, date ranges, document types
- **User management**: Authentication and authorization
- **Analytics dashboard**: Usage statistics and insights
- **Mobile app**: Native mobile applications
- **Voice interface**: Speech-to-text and text-to-speech

### Integration Opportunities
- **SharePoint integration**: Connect to existing document repositories
- **Active Directory**: Enterprise authentication
- **Microsoft Teams**: Bot integration for Teams channels
- **Slack integration**: Workplace chat integration

## 📄 License

This project is developed for Air Force use and follows applicable government software guidelines.

## 🤝 Contributing

For contributions and improvements:
1. Follow existing code style and patterns
2. Add comprehensive tests for new features
3. Update documentation for any changes
4. Ensure security and compliance requirements are met

---

**Built with ❤️ for the United States Air Force**

*Enhancing operational readiness through intelligent policy navigation*

