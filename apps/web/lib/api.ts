import axios from "axios";
import {
  getAccessToken,
  getPersistAccessPreference,
  getRefreshToken,
  removeTokens,
  saveTokens,
} from "./auth";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

let refreshPromise: Promise<string | null> | null = null;

const refreshAccessToken = async () => {
  const refreshToken = getRefreshToken();
  if (!refreshToken) {
    return null;
  }

  if (refreshPromise) {
    return refreshPromise;
  }

  refreshPromise = axios
    .post(`${API_URL}/auth/refresh`, {
      refresh_token: refreshToken,
    })
    .then((response) => {
      const { access_token, refresh_token } = response.data as {
        access_token: string;
        refresh_token: string;
      };
      saveTokens(
        { access_token, refresh_token },
        { persistAccess: getPersistAccessPreference() },
      );
      return access_token;
    })
    .catch(() => {
      removeTokens();
      return null;
    })
    .finally(() => {
      refreshPromise = null;
    });

  return refreshPromise;
};

apiClient.interceptors.request.use(
  (config) => {
    if (typeof window !== "undefined") {
      const token = getAccessToken();
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => Promise.reject(error),
);

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401 && typeof window !== "undefined") {
      const originalRequest = error.config as
        | (typeof error.config & { _retry?: boolean })
        | undefined;
      if (!originalRequest || originalRequest._retry) {
        return Promise.reject(error);
      }
      originalRequest._retry = true;

      const newAccessToken = await refreshAccessToken();
      if (newAccessToken) {
        originalRequest.headers = originalRequest.headers ?? {};
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
        return apiClient(originalRequest);
      }

      window.location.href = "/login";
    }
    return Promise.reject(error);
  },
);

export default apiClient;
