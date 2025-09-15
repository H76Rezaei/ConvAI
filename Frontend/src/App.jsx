import { useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios"; 
import Lottie from 'lottie-react';
import Animation from './Live chatbot.json';

function App() {
  const navigate = useNavigate();
  const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';
  
  // State management 
  const [isLoginMode, setIsLoginMode] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  
  // Form data that works for both login and register
  const [formData, setFormData] = useState({
    email: "",
    password: "",
    username: "",
    confirmPassword: ""
  });

  const handleLogin = async () => {
    setError("");
    setSuccessMessage("");
    
    if (!formData.email || !formData.password) {
      setError("Please fill in both email and password.");
      return;
    }

    setIsLoading(true);

    try {
      const response = await axios.post(`${API_URL}/auth/login`, {
        email: formData.email,
        password: formData.password
      });

      // Store token and user data
      localStorage.setItem("access_token", response.data.access_token);
      localStorage.setItem("user", JSON.stringify(response.data.user));
      
      setSuccessMessage("Login successful!");
      setTimeout(() => navigate("/NewChat"), 1500);

    } catch (error) {
      console.log("Login error:", error);
      if (error.response?.data?.detail) {
        if (typeof error.response.data.detail === 'string') {
          setError(error.response.data.detail);
        } else {
          setError('Login failed. Please check your credentials.');
      }
    } else {
      setError("Login failed. Please try again.");
    }
  } finally {
  setIsLoading(false);
}
  };

  const handleRegister = async () => {
    setError("");
    setSuccessMessage("");
    
    if (!formData.email || !formData.password || !formData.username) {
      setError("Please fill in all fields.");
      return;
    }
    
    if (formData.password !== formData.confirmPassword) {
      setError("Passwords don't match");
      return;
    }

    setIsLoading(true);
    
    try {
      const response = await axios.post(`${API_URL}/auth/register`, {
        email: formData.email,
        username: formData.username,
        password: formData.password
      });

      localStorage.setItem("access_token", response.data.access_token);
      localStorage.setItem("user", JSON.stringify(response.data.user));
      
      setSuccessMessage("Registration successful!");
      setTimeout(() => navigate("/NewChat"), 1500);
      
    } catch (error) {
      if (error.response?.data?.detail) {
        setError(error.response.data.detail);
      } else {
        setError("Registration failed. Please try again.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-stone-300 h-screen flex"> 
      <div className="w-1/2 flex flex-col items-center justify-center">
        <h1 className="text-4xl font-bold text-black mb-8 animate-pulse">
          Hi! Welcome to ConvAI!
        </h1>
        <Lottie
          animationData={Animation}
          style={{ width: 300, height: 300, backgroundColor: 'transparent' }}
        />
      </div>
      
      <div className="w-1/2 flex flex-col items-center justify-center p-8">
        <div className="bg-stone-200 rounded-lg shadow-lg p-8 w-full max-w-md">
          <h2 className="text-xl font-bold mb-4">
            {isLoginMode ? "Log in" : "Create Account"}
          </h2>

          <div className="bg-stone-300 rounded-lg shadow-lg p-8 w-full max-w-md">
            <input
              type="email" 
              placeholder="Email" 
              className="border border-stone-400 p-2 mb-4 w-full rounded"
              value={formData.email}
              onChange={e => setFormData({ ...formData, email: e.target.value })}
              disabled={isLoading} 
            />
            
            {/* This field only shows in register mode - YOU NEED TO IMPLEMENT THIS */}
            {!isLoginMode && (
              <input
                type="text"
                placeholder="Username"
                className="border border-stone-400 p-2 mb-4 w-full rounded"
                value={formData.username}
                onChange={e => setFormData({ ...formData, username: e.target.value })}
                disabled={isLoading} 
              />
            )}
            
            <input
              type="password"
              placeholder="Password"
              className="border border-stone-400 p-2 mb-4 w-full rounded"
              value={formData.password}
              onChange={e => setFormData({ ...formData, password: e.target.value })}
              disabled={isLoading} 
            />
            
            {/* This field only shows in register mode - YOU NEED TO IMPLEMENT THIS */}
            {!isLoginMode && (
              <input
                type="password"
                placeholder="Confirm Password"
                className="border border-stone-400 p-2 mb-4 w-full rounded"
                value={formData.confirmPassword}
                onChange={e => setFormData({ ...formData, confirmPassword: e.target.value })}
                disabled={isLoading} 
              />
            )}

            {/* Error and success messages */}
            {error && (
              <div className="text-red-500 text-sm mb-4 p-2 bg-red-50 rounded">
                {String(error)}
              </div>
            )}

            {successMessage && (
              <div className="text-green-600 text-sm mb-4 p-2 bg-green-50 rounded">
                {successMessage}
              </div>
            )}

            <button 
              className={`w-full p-2 rounded-lg text-white font-medium ${
                isLoading 
                  ? 'bg-gray-400 cursor-not-allowed' 
                  : 'bg-blue-500 hover:bg-blue-600'
              }`}
              onClick={isLoginMode ? handleLogin : handleRegister}
              disabled={isLoading}
            >
              {isLoading 
                ? (isLoginMode ? "Logging in..." : "Signing up...") 
                : (isLoginMode ? "Log In" : "Sign Up")       
              }
            </button>
          </div>
          
          <div className="mt-6 text-center">
            {isLoginMode ? "Not registered yet?" : "Already have an account?"}
            <span 
              className="text-blue-500 cursor-pointer hover:underline ml-1" 
              onClick={() => setIsLoginMode(!isLoginMode)}
            >
              {isLoginMode ? "Sign Up" : "Log In"}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;