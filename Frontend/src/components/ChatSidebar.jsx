import { FaCirclePlus } from "react-icons/fa6";
import { MdOutlineHistory } from "react-icons/md";
import { LuUserPen } from "react-icons/lu";
import { useNavigate } from "react-router-dom";

const ChatSidebar = () => {

  const navigate = useNavigate();

  const handleNewChat = () => {
      navigate("/");
  };
  const handleChatHistory = () => {
      navigate("/ChatHistory");
  };
  return (
  <div className="w-16 bg-stone-200 flex flex-col justify-between items-center pt-20 h-screen">
    <div className="flex flex-col items-center space-y-4">

      <div className="p-2 rounded-full hover:bg-gray-50 transition-colors cursor-pointer">
        <FaCirclePlus className="text-3xl text-indigo-500" onClick={handleNewChat}/>
      </div>
      
      <div className="p-2 rounded-full hover:bg-gray-50 transition-colors cursor-pointer">
        <MdOutlineHistory className="text-3xl text-indigo-500" onClick={handleChatHistory}/>
      </div>

    </div>
    <div className="flex flex-col items-center mb-4">
      
      <div className="p-2 rounded-full hover:bg-gray-50 transition-colors cursor-pointer">
        <LuUserPen className="text-3xl text-indigo-600" />
      </div>

    </div>
  </div>
);
};

export default ChatSidebar;
