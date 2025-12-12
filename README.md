# 🤖 LangGraph Documentation Chatbot

A full-stack chatbot that uses n8n for data pipeline orchestration, RAG for document retrieval, and Next.js for the UI.

## 🎯 Project Overview

**What it does:**

- Ingests LangGraph documentation into a RAG system
- Provides a ChatGPT-like interface to ask questions about LangGraph
- Uses n8n workflows to orchestrate the data pipeline

**Architecture:**

```
┌─────────────────────────────────────────────────────────┐
│                    USER INTERFACE                        │
│                                                          │
│  ┌────────────────────────────────────────────────┐     │
│  │      Next.js Chat UI (Port 3000)               │     │
│  │  - ChatGPT-like interface                      │     │
│  │  - Message history                             │     │
│  │  - Typing indicators                           │     │
│  └────────────────┬───────────────────────────────┘     │
└───────────────────┼──────────────────────────────────────┘
                    │
                    │ HTTP POST
                    ▼
┌─────────────────────────────────────────────────────────┐
│              Next.js API Routes                          │
│  /api/chat  -  Proxies requests to n8n                  │
└────────────────┬────────────────────────────────────────┘
                 │
                 │ HTTP POST
                 ▼
┌─────────────────────────────────────────────────────────┐
│                 n8n WORKFLOWS (Port 5678)                │
│                                                          │
│  Workflow 1: Document Ingestion Pipeline                │
│  ┌────────────────────────────────────────────┐         │
│  │ Webhook → Scrape LangGraph Docs → Split   │         │
│  │ → Embed → Store in Vector DB → Notify     │         │
│  └────────────────────────────────────────────┘         │
│                                                          │
│  Workflow 2: Chat Query Pipeline                        │
│  ┌────────────────────────────────────────────┐         │
│  │ Webhook → Call RAG Service → Format        │         │
│  │ → Add Sources → Return Response            │         │
│  └────────────────────────────────────────────┘         │
└────────────────┬────────────────────────────────────────┘
                 │
                 │ HTTP POST
                 ▼
┌─────────────────────────────────────────────────────────┐
│           Python RAG Service (Port 5001)                 │
│                                                          │
│  ┌──────────────────────────────────────────┐           │
│  │  /ingest  - Process documents            │           │
│  │  /query   - Answer questions             │           │
│  └──────────────────────────────────────────┘           │
│                                                          │
│  ┌──────────────────────────────────────────┐           │
│  │  LlamaIndex + ChromaDB                   │           │
│  │  - Semantic search                       │           │
│  │  - Context retrieval                     │           │
│  │  - Response generation                   │           │
│  └──────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Node.js 18+
- Python 3.9+
- Docker (for n8n)
- OpenAI API key

### Setup (10 Minutes)

1. **Clone and Install Backend**

```bash
# Navigate to backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

2. **Install Frontend**

```bash
# Navigate to frontend
cd frontend
npm install
```

3. **Start Services**

```bash
# Terminal 1: Start RAG Service
cd backend
python rag_service.py

# Terminal 2: Start n8n
docker run -d --name n8n -p 5678:5678 -v ~/.n8n:/home/node/.n8n docker.n8n.io/n8nio/n8n

# Terminal 3: Start Next.js
cd frontend
npm run dev
```

4. **Setup n8n Workflows**

- Open http://localhost:5678
- Import workflows from `n8n-workflows/` directory
- Activate both workflows

5. **Open Application**

- Navigate to http://localhost:3000
- Start chatting about LangGraph!

## 📁 Project Structure

```
langraph-docs-chatbot/
├── backend/                      # Python RAG service
│   ├── rag_service.py           # Main RAG service
│   ├── requirements.txt         # Python dependencies
│   ├── .env.example            # Environment template
│   └── documents/              # Ingested documents
│
├── frontend/                    # Next.js application
│   ├── app/
│   │   ├── page.tsx            # Chat UI
│   │   └── api/
│   │       └── chat/
│   │           └── route.ts    # API route to n8n
│   ├── components/
│   │   ├── ChatInterface.tsx   # Main chat component
│   │   ├── MessageList.tsx     # Message display
│   │   └── ChatInput.tsx       # Input component
│   ├── package.json
│   └── next.config.js
│
├── n8n-workflows/               # n8n workflow definitions
│   ├── 1-document-ingestion.json
│   └── 2-chat-query.json
│
└── README.md                    # This file
```

## 🎓 How It Works

### Document Ingestion Flow

1. **User triggers ingestion** (manual or scheduled in n8n)
2. **n8n workflow starts:**
   - Scrapes LangGraph documentation from website
   - Cleans and extracts text content
   - Splits into chunks
   - Calls Python service `/ingest` endpoint
3. **Python RAG service:**
   - Creates embeddings using OpenAI
   - Stores in ChromaDB vector database
   - Returns success confirmation
4. **n8n completes:**
   - Logs results
   - Sends notification (optional)

### Chat Query Flow

1. **User types question** in Next.js UI
2. **Next.js sends to** `/api/chat` route
3. **API route forwards to** n8n webhook
4. **n8n workflow:**
   - Receives query
   - Calls Python service `/query` endpoint
   - Formats response
   - Adds source citations
5. **Python RAG service:**
   - Searches vector database
   - Retrieves relevant chunks
   - Generates answer with LLM
   - Returns with sources
6. **Response flows back:**
   - n8n → Next.js API → Frontend
   - UI displays answer with sources

## 🎯 Key Features

### ✅ Full Stack

- **Frontend**: Modern Next.js 14 with TypeScript
- **Backend**: Python with LlamaIndex
- **Orchestration**: n8n for data pipelines

### ✅ n8n Data Pipeline

- Visual workflow design
- Error handling at each step
- Logging and monitoring
- Easy to modify and extend

### ✅ RAG Implementation

- Semantic search with embeddings
- Context-aware responses
- Source citations
- ChromaDB for persistence

### ✅ Production Ready

- Environment configuration
- Error handling
- Type safety (TypeScript)
- Docker support

## 🔧 Configuration

### Backend (.env)

```env
OPENAI_API_KEY=your_key_here
```

### Frontend (.env.local)

```env
N8N_WEBHOOK_URL=http://localhost:5678/webhook/chat
```

### n8n

- Import workflows from `n8n-workflows/`
- Configure webhook URLs
- Set OpenAI credentials if needed

## 🧪 Testing

### Test RAG Service

```bash
# Test ingestion
curl -X POST http://localhost:5001/ingest \
  -H "Content-Type: application/json" \
  -d '{"url": "https://docs.langchain.com/oss/python/langgraph/overview"}'

# Test query
curl -X POST http://localhost:5001/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What is LangGraph?"}'
```

### Test n8n Workflows

1. Open n8n at http://localhost:5678
2. Open each workflow
3. Click "Execute Workflow" to test

### Test Full Flow

1. Open http://localhost:3000
2. Type: "What is LangGraph?"
3. Verify you get a response with sources

## 🚀 Next Steps

### Enhancements I Could Add

1. Conversation memory
2. Streaming responses
3. Document upload via UI
4. Admin dashboard
5. User authentication

## 📝 License

MIT
