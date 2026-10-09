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
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
});

apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Allows setting auth headers if needed in the future
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    const formattedError: ApiError = {
      message: 'An unexpected error occurred.',
      statusCode: error.response?.status,
      details: error.response?.data,
      isNetworkError: !error.response,
    };

    if (error.code === 'ECONNABORTED') {
      formattedError.message = 'The request timed out. Please try again.';
    } else if (!error.response) {
      formattedError.message = `Unable to connect to the MeetMind backend at ${ENV.API_BASE_URL}. Ensure the FastAPI server is running.`;
    } else if (error.response.status === 404) {
      formattedError.message = 'The requested resource was not found.';
    } else if (error.response.status === 422) {
      formattedError.message = 'Invalid request parameters or payload format.';
    } else if (error.response.status >= 500) {
      formattedError.message = 'Internal server error from backend processing.';
    }

    return Promise.reject(formattedError);
  }
);
