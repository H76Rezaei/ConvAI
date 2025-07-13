import { useState, useEffect, useRef } from "react";  // Add useEffect here
import { useNavigate, useLocation } from "react-router-dom";
import { IoIosSend } from "react-icons/io";
import { FaMicrophone } from "react-icons/fa";
import { RiVoiceprintFill } from "react-icons/ri";
import axios from 'axios'; 

const Chat = () => {

  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState([]); // Array to store all messages
  const [isRecording, setIsRecording] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const [isLoading, setIsLoading] = useState(false);
  const hasProcessedInitial = useRef(false);

  // Get initial message from App page
  const initialMessage = location.state?.initialMessage;
/*
  const generateAIResponse = (userMessage) => {
    setIsLoading(true);
    setTimeout(() => {
      const aiMessage = {
        id: Date.now() + 1,
        text: `AI: You said "${userMessage}"`,
        sender: 'ai'
      };
      setMessages(prev => [...prev, aiMessage]);
      setIsLoading(false);
    }, 1000);
  };
*/
  const generateAIResponse = async (userMessage) => {
    setIsLoading(true);
  
    try {
      const response = await axios.post('http://127.0.0.1:8000/api/chat', {
        message: userMessage,
        user_id: 'react_user'
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
        generateAIResponse(initialMessage);  // Trigger AI response
      }
  }, [initialMessage]);

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
    <div className="bg-stone-100 h-screen flex flex-col">
      {/* User message box */}
      <div className="flex-1 flex flex-col space-y-4 p-4 overflow-y-auto">
        {messages.map(msg => (
          <div key={msg.id} className={`max-w-xs p-3 rounded-xl shadow ${
            msg.sender === 'user' 
              ? 'self-end bg-pink-50' 
              : 'self-start bg-sky-50'
            } text-black`}>
            <p>{msg.text}</p>
          </div>
        ))}
        {isLoading && (
        <div className="max-w-xs text-black p-3 rounded-xl shadow">
          <p>ConvAI is thinking...</p>
        </div>
        )}
      </div>

      {/* Input area at bottom */}
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
          <div className="flex space-x-4 justify-end">
            <FaMicrophone className="cursor-pointer text-2xl text-indigo-500" />
            {(message.trim() || isRecording) ? (
              <IoIosSend className="cursor-pointer text-2xl text-indigo-500" onClick={handleSend} />
            ) : (
              <>
                <RiVoiceprintFill className="cursor-pointer text-2xl text-indigo-500" onClick={VoiceChat} />
              </>
            )}
          </div>
        </div>
      </div>
    </div>

  );

}

export default Chat;