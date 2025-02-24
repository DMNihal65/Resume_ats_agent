import { create } from 'zustand';
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

const useResumeStore = create((set, get) => ({
  apiKey: null,
  jobUrl: '',
  resumeContent: null,
  jobAnalysis: null,
  comparison: null,
  modifiedResume: null,
  loading: false,
  error: null,
  currentStep: 0,

  setApiKey: (key) => set({ apiKey: key }),
  
  validateApiKey: async (key) => {
    try {
      set({ loading: true, error: null });
      await axios.post(`${API_BASE_URL}/set-api-key`, { api_key: key });
      set({ apiKey: key, currentStep: 1 });
    } catch (err) {
      set({ error: err.response?.data?.detail || 'Failed to validate API key' });
      throw err;
    } finally {
      set({ loading: false });
    }
  },

  analyzeJobUrl: async (url, companyName = '') => {
    try {
      set({ loading: true, error: null });
      const { data } = await axios.post(`${API_BASE_URL}/analyze-job-url`, {
        url,
        api_key: get().apiKey,
        company_name: companyName
      });
      set({ jobAnalysis: data });
      return data;
    } catch (err) {
      set({ error: err.response?.data?.detail || 'Failed to analyze job posting' });
      throw err;
    } finally {
      set({ loading: false });
    }
  },

  compareResume: async () => {
    try {
      set({ loading: true, error: null });
      const { resumeContent, jobAnalysis, apiKey } = get();
      
      const response = await axios.post(`${API_BASE_URL}/optimize-resume`, {
        resume_content: resumeContent,
        job_analysis: jobAnalysis,
        api_key: apiKey
      });
      
      set({ 
        comparison: response.data,
        currentStep: 3
      });
      return response.data;
    } catch (error) {
      set({ error: error.response?.data?.detail || 'Error comparing resume' });
      throw error;
    } finally {
      set({ loading: false });
    }
  },

  setCurrentStep: (step) => set({ currentStep: step }),
  goBack: () => set((state) => ({ currentStep: Math.max(0, state.currentStep - 1) })),
  goNext: () => set((state) => ({ currentStep: Math.min(4, state.currentStep + 1) })),

  uploadResume: async (file) => {
    try {
      set({ loading: true, error: null });
      const formData = new FormData();
      formData.append('file', file);
      formData.append('api_key', get().apiKey);
      
      const response = await axios.post(`${API_BASE_URL}/upload-resume`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        validateStatus: (status) => status < 500,
      });

      if (response.data.status === 'success') {
        set({ 
          resumeContent: response.data.content,
          currentStep: 2
        });
        return response.data;
      } else {
        throw new Error(response.data.detail || 'Upload failed');
      }
    } catch (error) {
      const errorMessage = error.response?.data?.detail || error.message || 'Error uploading resume';
      set({ 
        error: errorMessage,
        resumeContent: null
      });
      throw error;
    } finally {
      set({ loading: false });
    }
  },

  optimizeResume: async () => {
    try {
      set({ loading: true, error: null });
      const { resumeContent, jobAnalysis, apiKey } = get();
      
      const response = await axios.post(`${API_BASE_URL}/optimize-resume`, {
        resume_content: resumeContent,
        job_analysis: jobAnalysis,
        api_key: apiKey
      });
      
      set({ comparison: response.data });
      return response.data;
    } catch (error) {
      set({ error: error.response?.data?.detail || 'Error optimizing resume' });
      throw error;
    } finally {
      set({ loading: false });
    }
  },

  generateModifiedResume: async () => {
    try {
      set({ loading: true, error: null });
      const { resumeContent, comparison, apiKey } = get();
      
      if (!comparison) {
        throw new Error("No comparison data available");
      }

      const response = await axios.post(`${API_BASE_URL}/generate-modified-resume`, {
        resume_content: resumeContent,
        comparison: comparison,
        api_key: apiKey,
        company_name: "Company"
      });
      
      if (!response.data.modified_content) {
        throw new Error("No modified content received");
      }

      set({ 
        modifiedResume: response.data,
        currentStep: 4
      });
      return response.data;
    } catch (error) {
      const errorMessage = error.response?.data?.detail || error.message || 'Error generating modified resume';
      set({ error: errorMessage });
      throw error;
    } finally {
      set({ loading: false });
    }
  },

  reset: () => set({
    jobUrl: '',
    resumeContent: null,
    jobAnalysis: null,
    comparison: null,
    modifiedResume: null,
    error: null,
    currentStep: 0
  })
}));

export default useResumeStore; 