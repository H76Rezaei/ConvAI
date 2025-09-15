import { useState } from "react";
import { LuUserPen, LuLogOut, LuX } from "react-icons/lu"; 
import { useNavigate } from "react-router-dom"; 
import { FaCirclePlus } from "react-icons/fa6";
import { MdOutlineHistory } from "react-icons/md";

const ChatSidebar = () => {

  const navigate = useNavigate();
  const [isProfileOpen, setIsProfileOpen] = useState(false);

  const handleNewChat = () => {
      navigate("/NewChat");
  };

  
  const handleChatHistory = () => {
      navigate("/ChatHistory");
  };
  
  const handleProfileClick = () => {
    setIsProfileOpen(true);
  };
  
  const handleLogout = () => {
  const confirmed = window.confirm("Are you sure you want to logout?");
  if (confirmed) {
    // Clear all auth data
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    localStorage.removeItem('current_session_id'); 
    
    // Navigate to login
    navigate("/");
    
    // Close profile menu
    setIsProfileOpen(false);
    }
  };

  return (
    <>
      {/* Original Sidebar */}
      <div className="w-16 bg-stone-300 flex flex-col justify-between items-center pt-20 h-screen">
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
            <LuUserPen className="text-3xl text-indigo-600" onClick={handleProfileClick}/>
          </div>

        </div>
      </div>

      {/* Profile Sidebar - Background overlay */}
      <div 
        className={`fixed inset-0 bg-black bg-opacity-50 z-40 transition-opacity duration-300 ${
          isProfileOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'
        }`}
        onClick={() => setIsProfileOpen(false)}
      />

      {/* Profile Sidebar - Panel */}
      <div 
        className={`fixed right-0 top-0 h-full w-80 bg-white shadow-xl z-50 transform transition-transform duration-300 ease-in-out ${
          isProfileOpen ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-800">Profile</h2>
          <button 
            onClick={() => setIsProfileOpen(false)}
            className="p-2 rounded-full hover:bg-gray-100 transition-colors"
          >
            <LuX className="text-xl text-gray-600" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {/* Logout Option */}
          <button
            onClick={handleLogout}
            className="w-full flex items-center space-x-3 p-3 rounded-lg hover:bg-red-50 transition-colors group"
          >
            <LuLogOut className="text-xl text-gray-600 group-hover:text-red-600" />
            <span className="text-gray-700 group-hover:text-red-600">Logout</span>
          </button>
        </div>
      </div>
    </>
  );
};

export default ChatSidebar;