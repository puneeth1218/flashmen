import axios from 'axios';

// The base API client configuration will go here
export const apiClient = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptors can be added below
