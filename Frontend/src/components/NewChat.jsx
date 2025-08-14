import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import ChatSidebar from './ChatSidebar';
import ChatInput from './ChatInput.jsx';
import { getCurrentUser } from '../utils/authUtils'; 

function NewChat() {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [pendingDocument, setPendingDocument] = useState(null);

  useEffect(() => {
    localStorage.removeItem('current_session_id');
    localStorage.removeItem('uploadedFiles');
    localStorage.removeItem('pendingDocument');
    // Get user data from token 
    const currentUser = getCurrentUser();
    if (currentUser) {
      setUser(currentUser);
    }
  }, []);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) navigate('/'); 
  }, []);

  const handleFileUploaded = (uploadResult) => {
    setPendingDocument(uploadResult);
  };

  const handleSendMessage = (msg) => {
    navigate("/Chat", {
      state: {
        initialMessage: msg,
        uploadedDocument: pendingDocument 
      } 
    });
  };

  return (
    <>
      <div className="bg-stone-100 h-screen flex"> 
        <div className="w-16">
          <ChatSidebar />
        </div>
        
        {/* Main content - centered vertically */}
        <div className="flex-1 flex flex-col items-center justify-center gap-8 px-4">
          <h1 className="text-4xl font-bold text-black text-center">
            Hi {user?.username || 'there'}, How can I help you today?
          </h1>
          
          {/* Input directly under the text */}
          <div className="w-full  max-w-2xl min-h-24">
            <ChatInput 
              onSendMessage={handleSendMessage}
              onFileUploaded={handleFileUploaded}
              placeholder={
                pendingDocument 
                  ? `Document "${pendingDocument.filename}" ready. Ask me anything about it...`
                  : "Type your message..."
              }
              showUploadFeature={true}
              uploadedFiles={pendingDocument ? [pendingDocument] : []}
            />
          </div>
        </div>
      </div>
    </>
  );
}

export default NewChat;