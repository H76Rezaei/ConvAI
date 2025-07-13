import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { IoIosSend } from "react-icons/io";
import { FaMicrophone } from "react-icons/fa";
import { RiVoiceprintFill } from "react-icons/ri";

function App() {

  const [message, setMessage] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const navigate = useNavigate();

  const handleSend = () => {
    if (message.trim()) {
      navigate("/Chat", { state: { initialMessage: message } });
    }
  };
  const VoiceChat = () => {
    if (message.trim()) {
      navigate("/VoiceChat", { state: { initialMessage: message } });
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter") {
      handleSend();
    }
  };
return (
  <>
    <div className="bg-stone-100 h-screen flex flex-col">
      {/* Top area - centers the text */}
      <div className="flex-1 flex flex-col items-center justify-center gap-8">
        <h1 className="text-4xl font-bold text-black">
          Hi! How can I help you today?
        </h1>
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
          <FaMicrophone className="cursor-pointer text-2xl text-indigo-500" onClick={handleSend} />
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
  </>
);
}
export default App;