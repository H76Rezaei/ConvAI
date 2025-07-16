import { useState, useEffect, useRef } from "react"; 
import { useNavigate, useLocation } from "react-router-dom";
import { IoIosSend } from "react-icons/io";
import { FaMicrophone } from "react-icons/fa";
import { RiVoiceprintFill } from "react-icons/ri";
import { Loader } from 'lucide-react';
import axios from 'axios'; 
import ChatSidebar from './ChatSidebar';

const Chat = () => {

  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState([]); 
  const [isRecording, setIsRecording] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const [isLoading, setIsLoading] = useState(false);
  const hasProcessedInitial = useRef(false);
  const messagesEndRef = useRef(null);
  const [chatTitle, setChatTitle] = useState("New Chat");

  // Get initial message from App page
  const initialMessage = location.state?.initialMessage;

  const generateAIResponse = async (userMessage) => {
    setIsLoading(true);

  
    try {
      const response = await axios.post('http://127.0.0.1:8000/api/chat', {
        message: userMessage,
        user_id: 'react_user'
        }, {
        timeout: 3000 
        });

      const aiMessage = {
        id: Date.now() + 1,
        text: response.data.ai_response,
        sender: 'ai'
      };
      setMessages(prev => [...prev, aiMessage]);
    }  catch (error) {
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

  useEffect(() => {
    console.log("useEffect running with:", initialMessage);
    if (initialMessage && !hasProcessedInitial.current) {
      hasProcessedInitial.current = true;
        const newMessage = {
          id: Date.now(),
          text: initialMessage,
          sender: 'user'
        };
        setMessages([newMessage]);
        if (messages.length === 0) {
          const title = initialMessage.length > 30 ? initialMessage.slice(0, 30) + "..." : initialMessage;
          //const title = "New Chat";
          setChatTitle(title);
        }
        generateAIResponse(initialMessage);  // Trigger AI response
      }
  }, [initialMessage]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = () => {
    console.log("handleSend called with:", message);
    if (message.trim()) {
      const userMessage = {
        id: Date.now(),
        text: message,
        sender: 'user'
      };
    
      setMessages(prev => [...prev, userMessage]);
      const currentMessage = message;
      setMessage("");
      generateAIResponse(currentMessage);  // Trigger AI response
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter") {
      handleSend();
    }
  };

  const VoiceChat = () => {
    if (message.trim()) {
      navigate("/VoiceChat", { state: { initialMessage: message } });
    }
  };


  return (
    <div className="bg-stone-100 h-screen flex">

      {/* Sidebar */}
      <div className="w-16">
        <ChatSidebar />
      </div>

      {/* Main area: Chat messages + Input */}
      <div className="flex-1 flex flex-col relative">
        <div className="absolute top-0 left-0 right-0 z-10 p-5 bg-gradient-to-b from-stone-100 via-stone-100 to-transparent">
          <h1 className="text-lg font-semibold text-black">{chatTitle}</h1>
        </div>
        {/* Chat messages (scrollable) */}
        <div className="flex-1 flex flex-col space-y-4 p-4 pt-16 overflow-y-auto">
          {messages.map(msg => (
          <div
            key={msg.id}
            className={`max-w-xs p-3 rounded-xl shadow ${
              msg.sender === 'user' ? 'self-end bg-pink-50' : 'self-start bg-sky-50'
            } text-black`}
          >
            <p>{msg.text}</p>
          </div>
          ))}

          {isLoading && (
            <Loader className="animate-[spin_2s_linear_infinite] text-indigo-500" />
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input box fixed at bottom */}
        <div className="p-4">
          <div className="max-w-2xl mx-auto min-h-[100px] w-full bg-white text-black 
            rounded-2xl shadow-md p-4 border border-gray-300 flex flex-col justify-between">
            <input
              type="text"
              placeholder="Type your message..."
              className="w-full bg-transparent focus:outline-none"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={handleKeyPress}
            />
            <div className="flex space-x-4 justify-end mt-2">
              <FaMicrophone className="cursor-pointer text-2xl text-indigo-500" />
              {(message.trim() || isRecording) ? (
                <IoIosSend className="cursor-pointer text-2xl text-indigo-500" onClick={handleSend} />
              ) : (
                <RiVoiceprintFill className="cursor-pointer text-2xl text-indigo-500" onClick={VoiceChat} />
              )}
            </div>
          </div>
        </div>
    </div>
  </div>
  );

}

export default Chat;