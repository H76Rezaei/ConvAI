import { useState, useEffect, useRef } from "react"; 
import { useNavigate, useLocation } from "react-router-dom";
import { Loader, FileText, X } from 'lucide-react';
import ChatSidebar from './ChatSidebar';
import ChatInput from './ChatInput.jsx'
import api from '../utils/api';
import { getCurrentUserId } from '../utils/authUtils';

const Chat = () => {
  const [messages, setMessages] = useState([]); 
  const navigate = useNavigate();
  const location = useLocation();
  const [isLoading, setIsLoading] = useState(false);
  const hasProcessedInitial = useRef(false);
  const messagesEndRef = useRef(null);
  const [chatTitle, setChatTitle] = useState("New Chat");
  const [sessionId, setSessionId] = useState(null); 
  const [uploadedFiles, setUploadedFiles] = useState([]); 

  // Get data from navigation state
  const initialMessage = location.state?.initialMessage;
  const uploadedDocument = location.state?.uploadedDocument;

  // Auth check
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) navigate('/');
  }, [navigate]);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Generate AI response with document context
  const generateAIResponse = async (userMessage, documentsContext = []) => {
    setIsLoading(true);

    try {
      // Use provided context or fallback to current uploaded files
      const docsToUse = documentsContext.length > 0 ? documentsContext : uploadedFiles;
      const documentIds = docsToUse.map(file => file.id);
      
      const requestData = {
        message: userMessage,
        session_id: sessionId, 
        user_id: getCurrentUserId(),
        document_ids: documentIds.length > 0 ? documentIds : undefined
      };
      
      const response = await api.post('/api/chat', requestData);

      // Store session_id for subsequent messages
      if (response.data.session_id && !sessionId) {
        setSessionId(response.data.session_id);
        localStorage.setItem('current_session_id', response.data.session_id);
      }

      const aiMessage = {
        id: Date.now() + 1,
        text: response.data.ai_response,
        sender: 'ai'
      };
      setMessages(prev => [...prev, aiMessage]);
      
    } catch (error) {
      console.error('Error:', error);
      const errorMessage = {
        id: Date.now() + 1,
        text: 'Sorry, there was an error getting AI response.',
        sender: 'ai'
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle initial data from navigation (document + message)
  useEffect(() => {
    if (hasProcessedInitial.current) return;

    let newMessages = [];
    let newFiles = [];
    let title = "New Chat";

    // Process uploaded document from NewChat
    if (uploadedDocument) {
      const documentFile = {
        id: uploadedDocument.document_id,
        name: uploadedDocument.filename,
        chunks: uploadedDocument.total_chunks || 0,
        uploadedAt: new Date(),
        status: 'ready'
      };
      newFiles.push(documentFile);
      
      // If we have a document, use its name as title
      title = `📄 ${uploadedDocument.filename}`;
    }

    // Process initial message from NewChat
    if (initialMessage) {
      const userMessage = {
        id: Date.now(),
        text: initialMessage,
        sender: 'user',
        hasDocuments: newFiles.length > 0,
        documentFilename: newFiles.length > 0 ? newFiles[0].name : null
      };
      newMessages.push(userMessage);
      
      // Only use message as title if no document
      if (!uploadedDocument) {
        title = initialMessage.length > 30 
          ? initialMessage.slice(0, 30) + "..." 
          : initialMessage;
      }
    }

    // Apply all state changes
    if (newFiles.length > 0) {
      setUploadedFiles(newFiles);
    }
    if (newMessages.length > 0) {
      setMessages(newMessages);
    }
    setChatTitle(title);

    // Generate AI response if we have an initial message
    if (initialMessage) {
      generateAIResponse(initialMessage, newFiles);
    }

    hasProcessedInitial.current = true;
  }, [initialMessage, uploadedDocument]);

  // Handle new message from input
  const handleSendMessage = (inputMessage) => {
    if (!inputMessage || !inputMessage.trim()) return;

    const userMessage = {
      id: Date.now(),
      text: inputMessage, 
      sender: 'user',
      hasDocuments: uploadedFiles.length > 0,
      documentFilename: uploadedFiles.length > 0 ? uploadedFiles[0].name : null
    };
    
    setMessages(prev => [...prev, userMessage]);
    generateAIResponse(inputMessage);
  };

  // Handle new file upload within chat
  const handleFileUploaded = (uploadResult) => {
    const newFile = {
      id: uploadResult.document_id,
      name: uploadResult.filename,
      chunks: uploadResult.total_chunks || 0,
      uploadedAt: new Date(),
      status: 'ready'
    };
    
    setUploadedFiles(prev => [...prev, newFile]);
    
    // Update title if this is the first document
    if (uploadedFiles.length === 0) {
      setChatTitle(`📄 ${uploadResult.filename}`);
    }
  };

  // Remove uploaded file
  const handleRemoveFile = (fileId) => {
    setUploadedFiles(prev => prev.filter(file => file.id !== fileId));
    
    // Reset title if no files left
    if (uploadedFiles.length === 1) {
      setChatTitle("New Chat");
    }
  };

  return (
    <div className="bg-stone-100 h-screen flex">
      {/* Sidebar */}
      <div className="w-16">
        <ChatSidebar />
      </div>

      {/* Main chat area */}
      <div className="flex-1 flex flex-col relative">
        
        {/* Header with title */}
        <div className="absolute top-0 left-0 right-0 z-10 p-5 bg-gradient-to-b from-stone-100 via-stone-100 to-transparent">
          <h1 className="text-lg font-semibold text-black">{chatTitle}</h1>
        </div>

        {/* Messages area */}
        <div className="flex-1 flex flex-col space-y-4 p-4 pt-16 overflow-y-auto">
          {messages.map(msg => (
            <div key={msg.id} className={`flex flex-col gap-1 ${msg.sender === 'user' ? 'items-end' : 'items-start'}`}>
              
              {/* Document indicator above user message (if message has documents) */}
              {msg.sender === 'user' && msg.hasDocuments && (
                <div className="flex items-center gap-1 text-xs text-gray-500 mb-1">
                  <span>📄 {msg.documentFilename}</span>
                </div>
              )}
              
              {/* Message bubble */}
              <div
                className={`max-w-md p-3 rounded-xl shadow-sm ${
                  msg.sender === 'user' 
                    ? 'bg-blue-500 text-white' 
                    : 'bg-white text-gray-800 border border-gray-200'
                }`}
              >
                <p className="text-sm leading-relaxed">{msg.text}</p>
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="self-start flex items-center gap-2 p-3 bg-gray-50 rounded-xl">
              <Loader className="w-4 h-4 animate-spin text-gray-600" />
              <span className="text-sm text-gray-600">Thinking...</span>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Input area */}
        <div className="p-4 border-t border-gray-200 bg-white">
          <ChatInput 
            onSendMessage={handleSendMessage}
            onFileUploaded={handleFileUploaded}
            placeholder={
              uploadedFiles.length > 0 
                ? "Ask me anything about your documents..." 
                : "Type your message..."
            }
            showUploadFeature={true}
            disabled={isLoading}
            uploadedFiles={uploadedFiles}
          />
        </div>
      </div>
    </div>
  );
};

export default Chat;