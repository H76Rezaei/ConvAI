# ConvAI - Smart Memory Chat App

> AI chat that remembers and understands conversation context using vector embeddings and semantic search.

🔗 **[Live Demo](https://conv-ai-six.vercel.app)** | 🚀 **[Backend API](https://convai-production.up.railway.app)**

## Key Features

- **Intelligent Memory**: Finds relevant past conversations by meaning, not keywords
- **Fast Responses**: Background memory storage, ~3 second response time
- **Privacy**: User isolation with GDPR-compliant data deletion
- **Semantic Search**: "chocolate cookies" matches "baking desserts"

## Tech Stack

**Backend**: FastAPI • OpenAI GPT-3.5 • Pinecone Vector DB • LangChain  
**Frontend**: React • Vite • Tailwind CSS  
**Deploy**: Railway • Vercel

## Quick Start

### Backend
```bash
cd Backend
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
# Add OPENAI_API_KEY and PINECONE_API_KEY to .env
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
