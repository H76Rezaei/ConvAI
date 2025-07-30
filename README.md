# ConvAI - Smart Memory Chat App

> AI chat that remembers and understands conversation context using vector embeddings and semantic search.

🔗 **[Live Demo](https://conv-ai-six.vercel.app)** | 🚀 **[Backend API](https://convai-production.up.railway.app)**

## Key Features

**User Authentication System**
JWT-based authentication with secure user registration and login. Implemented route protection and user session management with isolated conversation spaces.

**Intelligent Memory Architecture**
Built a two-tier memory system combining recent conversation context with semantic search across conversation history. Uses vector embeddings to retrieve relevant past discussions, enabling contextual responses that improve over time.

**Real-time Chat Interface**
Integrated OpenAI GPT-3.5 with custom context management. Each conversation maintains session tracking while leveraging personalized conversation history for enhanced response quality.

**Performance Optimization**
Designed background processing architecture for memory storage operations. Users receive immediate responses while conversation indexing and vector storage occur asynchronously.

**Full-Stack Implementation**
React frontend with protected routing and token-based authentication. FastAPI backend with automated API documentation, Pinecone vector database integration, and SQLite user management.

## Tech Stack

**Frontend**: React • Vite • Tailwind CSS • Axios Interceptors
**Backend**: FastAPI • JWT Authentication • SQLite • OpenAI GPT-3.5 • Pinecone Vector DB • LangChain  
**Deploy**: Railway • Vercel

## Quick Start

### Backend

```bash
cd Backend
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
# Add OPENAI_API_KEY, PINECONE_API_KEY, and JWT_SECRET_KEY to .env
python run.py
```

### Frontend

```bash
cd frontend
npm install && npm run dev
```

## How Smart Memory Works

1. **Store**: Conversations → Vector embeddings → Pinecone
2. **Search**: New message → Find similar past conversations
3. **Context**: Recent chat + Relevant history → OpenAI
4. **Result**: Context-aware AI responses

## What This Demonstrates

- **Vector Database Implementation** with semantic search
- **Production AI Architecture** with background processing
- **Modern Full-Stack Development** with proper deployment
- **Advanced Memory Systems** combining short-term + long-term storage

## 🔧 Environment Variables

```bash
OPENAI_API_KEY=sk-your-key-here
PINECONE_API_KEY=your-key-here
```
