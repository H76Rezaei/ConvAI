import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

export class UploadService {
  static async uploadDocument(file, userId) {
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('user_id', userId);

      const response = await axios.post(`${API_URL}/api/documents/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 30000, // 30 seconds for large files
        // You could add progress tracking here later
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          console.log(`Upload Progress: ${percentCompleted}%`);
          // TODO: Emit progress events if needed
        }
      });

      return {
        success: true,
        data: response.data
      };

    } catch (error) {
      console.error('Upload failed:', error);
      let errorMessage = 'Upload failed. Please try again.';
      
      if (error.response?.status === 413) {
        errorMessage = 'File too large. Please try a smaller file.';
      } else if (error.response?.status === 415) {
        errorMessage = 'File type not supported.';
      } else if (error.code === 'ECONNABORTED') {
        errorMessage = 'Upload timeout. Please try again.';
      }

      return {
        success: false,
        error: errorMessage,
        originalError: error
      };
    }
  }

  static async deleteDocument(documentId, userId) {
    try {
      const response = await axios.delete(`${API_URL}/api/documents/${documentId}`, {
        data: { user_id: userId },
        timeout: 10000
      });

      return {
        success: true,
        data: response.data
      };

    } catch (error) {
      console.error('Delete failed:', error);
      return {
        success: false,
        error: 'Failed to delete document. Please try again.',
        originalError: error
      };
    }
  }

  static async getUserDocuments(userId) {
    try {
      const response = await axios.get(`${API_URL}/api/documents/${userId}`, {
        timeout: 10000
      });

      return {
        success: true,
        data: response.data
      };

    } catch (error) {
      console.error('Failed to fetch documents:', error);
      return {
        success: false,
        error: 'Failed to load documents.',
        originalError: error
      };
    }
  }
  static async searchDocuments(query, userId, options = {}) {
    try {
      const response = await axios.post(`${API_URL}/api/documents/search`, {
        query,
        user_id: userId,
        ...options
      }, {
        timeout: 15000
      });

      return {
        success: true,
        data: response.data
      };

    } catch (error) {
      console.error('Document search failed:', error);
      return {
        success: false,
        error: 'Search failed. Please try again.',
        originalError: error
      };
    }
  }
}

export const uploadDocument = UploadService.uploadDocument;
export const deleteDocument = UploadService.deleteDocument;
export const getUserDocuments = UploadService.getUserDocuments;
export const searchDocuments = UploadService.searchDocuments;
export default UploadService;