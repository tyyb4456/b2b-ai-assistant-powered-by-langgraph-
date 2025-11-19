import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000, // 2 minutes for quote generation
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor (for auth tokens later)
api.interceptors.request.use(
  (config) => {
    // You can add auth tokens here later
    // const token = localStorage.getItem('token');
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`;
    // }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor (for error handling)
api.interceptors.response.use(
  (response) => {
    // Return the data directly for cleaner usage
    return response.data;
  },
  (error) => {
    // Handle errors consistently
    const message = error.response?.data?.error?.message || error.message || 'An error occurred';
    
    console.error('API Error:', {
      status: error.response?.status,
      message,
      url: error.config?.url,
    });
    
    return Promise.reject({
      message,
      status: error.response?.status,
      data: error.response?.data,
    });
  }
);

export default api;