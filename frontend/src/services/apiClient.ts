import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from 'axios';
import { ENV } from '../config/environment';

export interface ApiError {
  message: string;
  statusCode?: number;
  details?: any;
  isNetworkError?: boolean;
}

export const apiClient: AxiosInstance = axios.create({
  baseURL: ENV.API_BASE_URL,
  timeout: 120000, // 2 minutes for LLM and Whisper processing
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
});

apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    let message = 'An unexpected error occurred.';
    const data = error.response?.data as any;

    if (data?.detail) {
      if (typeof data.detail === 'string') {
        message = data.detail;
      } else if (Array.isArray(data.detail)) {
        message = data.detail.map((d: any) => d.msg || JSON.stringify(d)).join('; ');
      } else {
        message = JSON.stringify(data.detail);
      }
    } else if (error.code === 'ECONNABORTED') {
      message = 'The request timed out. Please try again.';
    } else if (!error.response) {
      message = `Unable to connect to the backend at ${ENV.API_BASE_URL}. Ensure the FastAPI server is running.`;
    } else if (error.response.status === 404) {
      message = 'The requested resource was not found.';
    } else if (error.response.status === 422) {
      message = 'Invalid request parameters or payload format.';
    } else if (error.response.status >= 500) {
      message = 'Internal server error from backend processing.';
    }

    const formattedError: ApiError = {
      message,
      statusCode: error.response?.status,
      details: error.response?.data,
      isNetworkError: !error.response,
    };

    return Promise.reject(formattedError);
  }
);
