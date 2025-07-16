import { useState, useEffect } from 'react';
import { useNavigate } from "react-router-dom";
import ChatSidebar from './ChatSidebar';

function ChatHistory() {
  const [conversations, setConversations] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

return (
  <>
    <div className="bg-stone-100 h-screen flex">
      {/* Sidebar */}
      <div className="w-16">
        <ChatSidebar />
      </div>
    </div>
  </>
);
  
}

export default ChatHistory;