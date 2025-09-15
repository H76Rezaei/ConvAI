// Mock for UploadService to handle import.meta syntax
const mockUploadService = {
  uploadDocument: jest.fn(() => Promise.resolve({
    document_id: 'mock-doc-id',
    filename: 'mock-file.pdf',
    status: 'ready'
  })),
  deleteDocument: jest.fn(() => Promise.resolve({ success: true }))
};

export default mockUploadService;
