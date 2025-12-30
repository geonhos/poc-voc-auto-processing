/**
 * Base API Service
 */

import axios, { type AxiosInstance, type AxiosError } from 'axios';

const BASE_URL = 'http://localhost:8000';

export const apiClient: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.code === 'ECONNABORTED') {
      throw new Error('요청 시간이 초과되었습니다. 다시 시도해주세요.');
    }

    if (!error.response) {
      throw new Error('네트워크 연결을 확인해주세요. 입력 내용은 저장되어 있습니다.');
    }

    const status = error.response.status;

    if (status >= 500) {
      throw new Error('서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요.');
    }

    if (status >= 400) {
      throw new Error('입력 정보를 다시 확인해주세요.');
    }

    throw error;
  }
);
