import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import './index.css'
import App from './App.jsx'
import Chat from './components/Chat.jsx'
import VoiceChat from './components/VoiceChat.jsx'
import ChatSidebar from './components/ChatSidebar.jsx';
import ChatHistory from './components/ChatHistory.jsx';
import NewChat from './components/NewChat.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<App />} />
        <Route path="/Chat" element={<Chat />} />
        <Route path="/VoiceChat" element={<VoiceChat />} />
        <Route path="/ChatSidebar" element={<ChatSidebar />} />
        <Route path="/ChatHistory" element={<ChatHistory />} />
        <Route path="/NewChat" element={<NewChat />} />
      </Routes>
    </BrowserRouter>
  </StrictMode>
)
