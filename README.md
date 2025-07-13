# ConvAI - Intelligent Chat Application

A full-stack chat application with AI memory capabilities using FastAPI, React, and LangChain.

## Features

- ✅ Real-time chat interface
- ✅ OpenAI integration
- ✅ Smart conversation memory (short-term + long-term)
- ✅ Vector-based semantic search
- ✅ Clean FastAPI backend
- ✅ Modern React frontend with Tailwind CSS

## Tech Stack

**Backend:**

- FastAPI
- LangChain
- OpenAI API
- ChromaDB (Vector Database)
- Python 3.8+

**Frontend:**

- React
- Vite
- Tailwind CSS
- Axios

## Setup Instructions

### Backend Setup

```bash
cd Backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
cp .env.example .env  # Add your OpenAI API key
python run.py
```

FRONTEND setup:
cd frontend
npm install
npm run dev
