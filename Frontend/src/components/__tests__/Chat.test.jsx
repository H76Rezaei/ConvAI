import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import Chat from '../Chat';

// Mock scrollIntoView before any imports that might use it
Object.defineProperty(Element.prototype, 'scrollIntoView', {
  value: vi.fn(),
  writable: true,
});

// Mock localStorage
const mockLocalStorage = {
  getItem: vi.fn(() => 'mock-token'),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};
Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage,
});

// Mock router hooks
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => vi.fn(),
    useLocation: () => ({ state: null }),
  };
});

// Mock the API module
vi.mock('../../utils/api', () => ({
  default: {
    post: vi.fn(),
    get: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
    interceptors: {
      request: { use: vi.fn() },
      response: { use: vi.fn() }
    }
  }
}));

// Mock the auth utils
vi.mock('../../utils/authUtils', () => ({
  getCurrentUserId: vi.fn(() => 'test-user-123'),
}));

// Mock UploadService
vi.mock('../../utils/UploadService', () => ({
  default: {
    uploadDocument: vi.fn(() => Promise.resolve({
      document_id: 'mock-doc-id',
      filename: 'mock-file.pdf',
      status: 'ready'
    })),
    deleteDocument: vi.fn(() => Promise.resolve({ success: true }))
  }
}));

const MockedChat = () => (
  <BrowserRouter>
    <Chat />
  </BrowserRouter>
);

describe('Chat Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders chat interface', () => {
    render(<MockedChat />);
    
    // Check for the main chat elements based on actual component
    expect(screen.getByText(/new chat/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/type your message/i)).toBeInTheDocument();
    // Voice button should be visible when no text is entered
    expect(screen.getByLabelText(/voice message/i)).toBeInTheDocument();
  });

  it('allows user to type a message and shows send button', async () => {
    render(<MockedChat />);
    
    const input = screen.getByPlaceholderText(/type your message/i);
    fireEvent.change(input, { target: { value: 'Hello, AI!' } });
    
    expect(input.value).toBe('Hello, AI!');
    
    // The send button should appear when there's text (conditional rendering)
    await waitFor(() => {
      expect(screen.getByLabelText(/send message/i)).toBeInTheDocument();
    });
  });

  it('calls generateAIResponse when send button is clicked', async () => {
    const mockApi = (await import('../../utils/api')).default;
    vi.mocked(mockApi.post).mockResolvedValue({
      data: {
        ai_response: 'Hello! How can I help you?',
        session_id: 'test-session'
      }
    });

    render(<MockedChat />);
    
    const input = screen.getByPlaceholderText(/type your message/i);
    
    // Type a message to make send button appear
    fireEvent.change(input, { target: { value: 'Hello, AI!' } });
    
    // Wait for send button to appear
    const sendButton = await waitFor(() => 
      screen.getByLabelText(/send message/i)
    );
    
    fireEvent.click(sendButton);
    
    // Check that API was called with correct data structure
    await waitFor(() => {
      expect(mockApi.post).toHaveBeenCalledWith('/api/chat', expect.objectContaining({
        message: 'Hello, AI!',
        user_id: 'test-user-123',
        session_id: null, // First message has no session_id
      }));
    });
  });

  it('calls generateAIResponse when Enter key is pressed', async () => {
    const mockApi = (await import('../../utils/api')).default;
    vi.mocked(mockApi.post).mockResolvedValue({
      data: {
        ai_response: 'Hello! How can I help you?',
        session_id: 'test-session'
      }
    });

    render(<MockedChat />);
    
    const input = screen.getByPlaceholderText(/type your message/i);
    
    fireEvent.change(input, { target: { value: 'Hello, AI!' } });
    
    // Your ChatInput uses onKeyDown, so use keyDown event
    fireEvent.keyDown(input, { key: 'Enter', code: 'Enter' });
    
    await waitFor(() => {
      expect(mockApi.post).toHaveBeenCalledWith('/api/chat', expect.objectContaining({
        message: 'Hello, AI!',
        user_id: 'test-user-123',
      }));
    });
  });

  it('displays loading state while generating AI response', async () => {
    const mockApi = (await import('../../utils/api')).default;
    vi.mocked(mockApi.post).mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)));

    render(<MockedChat />);
    
    const input = screen.getByPlaceholderText(/type your message/i);
    
    fireEvent.change(input, { target: { value: 'Hello, AI!' } });
    
    const sendButton = await waitFor(() => 
      screen.getByLabelText(/send message/i)
    );
    
    fireEvent.click(sendButton);
    
    // Check for loading state - your component shows "Thinking..."
    await waitFor(() => {
      expect(screen.getByText(/thinking/i)).toBeInTheDocument();
    });
  });

  it('displays error message when API call fails', async () => {
    const mockApi = (await import('../../utils/api')).default;
    vi.mocked(mockApi.post).mockRejectedValue(new Error('API Error'));

    render(<MockedChat />);
    
    const input = screen.getByPlaceholderText(/type your message/i);
    
    fireEvent.change(input, { target: { value: 'Hello, AI!' } });
    
    const sendButton = await waitFor(() => 
      screen.getByLabelText(/send message/i)
    );
    
    fireEvent.click(sendButton);
    
    await waitFor(() => {
      expect(screen.getByText(/sorry, there was an error getting ai response/i)).toBeInTheDocument();
    });
  });
});