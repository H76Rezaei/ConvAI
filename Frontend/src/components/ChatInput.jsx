import { useState, useRef, useEffect } from 'react';
import { IoIosSend } from "react-icons/io";
import { Paperclip, X, FileText, File } from 'lucide-react';
import { RiVoiceprintFill } from "react-icons/ri";
import UploadService from '../utils/UploadService';
import { getCurrentUserId } from '../utils/authUtils';

const ChatInput = ({ 
  onSendMessage, 
  onFileUploaded, 
  placeholder = "Type your message...",
  showUploadFeature = true,
  disabled = false,
}) => {
  const [message, setMessage] = useState("");
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef(null);
  const textareaRef = useRef(null);

  // Auto-resize textarea based on content
  useEffect(() => {
    if (textareaRef.current) {
      const textarea = textareaRef.current;
      textarea.style.height = 'auto';
      const scrollHeight = textarea.scrollHeight;
      // Max height equivalent to about 6-7 lines (similar to Claude)
      const maxHeight = 160;
      textarea.style.height = Math.min(scrollHeight, maxHeight) + 'px';
    }
  }, [message]);

  const handleSend = () => {
    if (message.trim() && !disabled) {
      onSendMessage(message.trim());
      setMessage("");
      setUploadedFiles([]);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const validateFile = (file) => {
    const allowedTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain'];
    const maxSize = 10 * 1024 * 1024; // 10MB

    if (!allowedTypes.includes(file.type)) {
      return 'Only PDF, DOCX, and TXT files are supported.';
    }
    if (file.size > maxSize) {
      return 'File must be smaller than 10MB.';
    }
    return null;
  };

  const handleFileSelect = () => {
    if (disabled || uploading) return;
    fileInputRef.current?.click();
  };

  const handleFileInputChange = (e) => {
    const files = [...e.target.files];
    files.forEach(handleFileUpload);
    e.target.value = '';
  };

  const handleFileUpload = async (file) => {
    const error = validateFile(file);
    if (error) {
      alert(error);
      return;
    }

    const userId = getCurrentUserId();
    if (!userId) {
      alert('User not authenticated. Please login again.');
      return;
    }

    const tempFile = {
      id: `temp_${Date.now()}`,
      name: file.name,
      status: 'uploading',
      progress: 0
    };
    
    setUploadedFiles(prev => [...prev, tempFile]);
    setUploading(true);
    
    try {
      const result = await UploadService.uploadDocument(file, userId);
      
      if (result.success) {
        setUploadedFiles(prev => 
          prev.map(f => 
            f.id === tempFile.id 
              ? {
                  id: result.data.document_id,
                  name: result.data.filename,
                  status: 'completed',
                  size: result.data.file_size,
                  chunks: result.data.total_chunks
                }
              : f
          )
        );
        
        if (onFileUploaded) {
          onFileUploaded(result.data);
        }
      } else {
        setUploadedFiles(prev => prev.filter(f => f.id !== tempFile.id));
        alert(result.error);
      }
    } catch (error) {
      console.error('Upload failed:', error);
      setUploadedFiles(prev => prev.filter(f => f.id !== tempFile.id));
      alert('Upload failed. Please try again.');
    } finally {
      setUploading(false);
    }
  };

  const removeFile = (fileId) => {
    setUploadedFiles(prev => prev.filter(f => f.id !== fileId));
  };

  const getFileIcon = (fileName) => {
    const ext = fileName.split('.').pop()?.toLowerCase();
    if (ext === 'pdf') return <FileText className="w-4 h-4 text-red-500" />;
    if (ext === 'docx' || ext === 'doc') return <File className="w-4 h-4 text-blue-500" />;
    return <File className="w-4 h-4 text-gray-500" />;
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  return (
    <div className="w-full max-w-5xl mx-auto">
      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept=".pdf,.docx,.txt"
        onChange={handleFileInputChange}
        className="hidden"
      />

      {/* Uploaded files display */}
      {uploadedFiles.length > 0 && (
        <div className="mb-3 flex flex-wrap gap-2">
          {uploadedFiles.map(file => (
            <div 
              key={file.id} 
              className="flex items-center bg-gray-100 rounded-lg px-3 py-2 text-sm border"
            >
              {getFileIcon(file.name)}
              <span className="ml-2 font-medium text-gray-700 max-w-32 truncate">
                {file.name}
              </span>
              
              {file.status === 'uploading' && (
                <div className="ml-2 w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
              )}
              
              {file.status === 'completed' && file.size && (
                <span className="ml-2 text-xs text-gray-500">
                  {formatFileSize(file.size)}
                </span>
              )}
              
              <button
                onClick={() => removeFile(file.id)}
                className="ml-2 p-1 hover:bg-gray-200 rounded"
                disabled={file.status === 'uploading'}
              >
                <X className="w-3 h-3 text-gray-500" />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Main input container */}
      <div className={`
        relative bg-white rounded-3xl border border-gray-200 shadow-sm
        max-w-4xl mx-auto
        ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
        focus-within:border-gray-400 focus-within:shadow-md transition-all
      `}>
        
        {/* Textarea container with proper positioning */}
        <div className="relative">
          <textarea
            ref={textareaRef}
            placeholder={placeholder}
            className={`
              w-full px-4 pt-4 pb-12 bg-transparent border-none resize-none focus:outline-none
              text-gray-900 placeholder-gray-500
              ${disabled ? 'cursor-not-allowed' : ''}
            `}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyPress}
            disabled={disabled}
            style={{ 
              minHeight: '60px',
              lineHeight: '1.5'
            }}
          />
          
          {/* Bottom button row */}
          <div className="absolute bottom-2 left-0 right-0 flex justify-between items-center px-4">
            
            {/* Left side - Upload button */}
            <div className="flex items-center">
              {showUploadFeature && (
                <button
                  onClick={handleFileSelect}
                  disabled={disabled || uploading}
                  className={`
                    p-2 rounded-lg text-gray-400 hover:text-indigo-500 hover:bg-gray-50 transition-colors
                    ${disabled || uploading ? 'cursor-not-allowed opacity-50' : 'cursor-pointer'}
                  `}
                  aria-label="Attach file"
                >
                  <Paperclip className="w-5 h-5" />
                </button>
              )}
            </div>

            {/* Right side - Action buttons */}
            <div className="flex items-center space-x-2">
              {/* Send button */}
              
              {message.trim() ? (
                <button
                  onClick={handleSend}
                  disabled={disabled}
                  className={`
                    p-2 rounded-lg bg-indigo-500 text-white hover:bg-indigo-600 transition-colors
                    ${disabled ? 'cursor-not-allowed opacity-50' : ''}
                  `}
                  aria-label="Send message"
                >
                  <IoIosSend className="w-5 h-5" />
                </button>
              ) : (
                <button
                  className={`
                    p-2 rounded-lg text-gray-400 hover:text-indigo-500 hover:bg-gray-50 transition-colors
                    ${disabled ? 'cursor-not-allowed opacity-50' : 'cursor-pointer'}
                  `}
                  disabled={disabled}
                  aria-label="Voice message"
                >
                  <RiVoiceprintFill className="w-5 h-5" />
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatInput;