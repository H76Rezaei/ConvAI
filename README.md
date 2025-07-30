# ConvAI - Intelligent Chat Application

A full-stack chat application with AI memory capabilities using FastAPI, React, and LangChain.

## Features

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

## Setup Instructions

### Backend Setup

```bash
cd Backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
# Add OPENAI_API_KEY, PINECONE_API_KEY, and JWT_SECRET_KEY to .env
python run.py
```

### Frontend setup:

```bash
cd frontend
npm install
npm run dev
```
