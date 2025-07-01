import axios, { AxiosResponse, AxiosError } from 'axios';
import { ApiError } from '../types/auth';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

// Request interceptor для добавления JWT токена
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor для обработки ошибок
apiClient.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Unauthorized - очищаем токен и перенаправляем на логин
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    
    return Promise.reject(error);
  }
);

// Функция для обработки API ошибок
export const handleApiError = (error: any): ApiError => {
  if (error.response?.data?.message) {
    return {
      message: error.response.data.message,
      errors: error.response.data.errors,
    };
  }
  
  if (error.message) {
    return { message: error.message };
  }
  
  return { message: 'Произошла неизвестная ошибка' };
};

export default apiClient; 