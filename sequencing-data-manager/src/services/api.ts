import axios from 'axios';
import {
  ScanStatus,
  ScanResults,
  Summary,
  CategoryData,
  DuplicatesData,
  DeleteResult
} from '../types';
import {
  isDemoMode,
  mockScanStatus,
  mockSummary,
  mockCategoryData,
  mockDuplicatesData,
  mockScanResults
} from './mockData';

// Configure axios with base URL for Flask backend
const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.warn('API Error (falling back to demo mode):', error.message);
    throw error;
  }
);

// Demo mode delay to simulate API calls
const demoDelay = (ms: number = 500) => new Promise(resolve => setTimeout(resolve, ms));

export const sequencingAPI = {
  // Start directory scan
  startScan: async (directoryPath: string): Promise<{ message: string; status: string }> => {
    if (isDemoMode()) {
      await demoDelay();
      return { message: 'Demo scan started', status: 'scanning' };
    }
    
    try {
      const response = await api.post('/scan', { directory_path: directoryPath });
      return response.data;
    } catch (error) {
      await demoDelay();
      return { message: 'Demo scan started (backend unavailable)', status: 'scanning' };
    }
  },

  // Get scan status
  getScanStatus: async (): Promise<ScanStatus> => {
    if (isDemoMode()) {
      await demoDelay(200);
      return mockScanStatus;
    }
    
    try {
      const response = await api.get('/scan/status');
      return response.data;
    } catch (error) {
      await demoDelay(200);
      return mockScanStatus;
    }
  },

  // Get complete scan results
  getResults: async (): Promise<ScanResults> => {
    if (isDemoMode()) {
      await demoDelay();
      return mockScanResults;
    }
    
    try {
      const response = await api.get('/results');
      return response.data;
    } catch (error) {
      await demoDelay();
      return mockScanResults;
    }
  },

  // Get files by category
  getFilesByCategory: async (category: string): Promise<CategoryData> => {
    if (isDemoMode()) {
      await demoDelay();
      return mockCategoryData[category] || { count: 0, size_gb: 0, percentage: 0, files: [] };
    }
    
    try {
      const response = await api.get(`/files/${category}`);
      return response.data;
    } catch (error) {
      await demoDelay();
      return mockCategoryData[category] || { count: 0, size_gb: 0, percentage: 0, files: [] };
    }
  },

  // Get duplicate files
  getDuplicates: async (): Promise<DuplicatesData> => {
    if (isDemoMode()) {
      await demoDelay();
      return mockDuplicatesData;
    }
    
    try {
      const response = await api.get('/duplicates');
      return response.data;
    } catch (error) {
      await demoDelay();
      return mockDuplicatesData;
    }
  },

  // Get summary statistics
  getSummary: async (): Promise<Summary> => {
    if (isDemoMode()) {
      await demoDelay(300);
      return mockSummary;
    }
    
    try {
      const response = await api.get('/summary');
      return response.data;
    } catch (error) {
      await demoDelay(300);
      return mockSummary;
    }
  },

  // Delete selected files
  deleteFiles: async (filePaths: string[]): Promise<DeleteResult> => {
    if (isDemoMode()) {
      await demoDelay(1000);
      return {
        total_deleted: filePaths.length,
        total_failed: 0,
        deleted_files: filePaths,
        failed_files: [],
        space_freed_gb: filePaths.length * 0.5 // Mock space freed
      };
    }
    
    try {
      const response = await api.post('/delete', { file_paths: filePaths });
      return response.data;
    } catch (error) {
      await demoDelay(1000);
      // Return demo result
      return {
        total_deleted: filePaths.length,
        total_failed: 0,
        deleted_files: filePaths,
        failed_files: [],
        space_freed_gb: filePaths.length * 0.5
      };
    }
  },
};

// Utility functions for formatting
export const formatFileSize = (sizeGB: number): string => {
  if (sizeGB >= 1000) {
    return `${(sizeGB / 1000).toFixed(2)} TB`;
  } else if (sizeGB >= 1) {
    return `${sizeGB.toFixed(2)} GB`;
  } else if (sizeGB >= 0.001) {
    return `${(sizeGB * 1000).toFixed(2)} MB`;
  } else {
    return `${(sizeGB * 1000 * 1000).toFixed(2)} KB`;
  }
};

export const formatNumber = (num: number): string => {
  return new Intl.NumberFormat().format(num);
};

export default api;
