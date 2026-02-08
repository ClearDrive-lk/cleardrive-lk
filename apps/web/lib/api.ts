import axios from "axios";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

// Concurrency control for token refresh
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (value: string) => void;
  reject: (error: any) => void;
}> = [];

/**
 * Process all queued requests after token refresh completes
 * @param error - Error if refresh failed, null if successful
 * @param token - New access token if refresh succeeded
 */
const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token!);
    }
  });
  failedQueue = [];
};

/**
 * Refresh the access token using the refresh token
 * @returns New access token
 * @throws Error if refresh fails or no refresh token available
 */
const refreshAccessToken = async (): Promise<string> => {
  const refreshToken = localStorage.getItem("refresh_token");
  if (!refreshToken) {
    throw new Error("No refresh token available");
  }

  // Use vanilla axios to avoid interceptor loops
  const response = await axios.post(`${API_URL}/auth/refresh`, {
    refresh_token: refreshToken,
  });

  const { access_token, refresh_token: newRefreshToken } = response.data;

  // Update localStorage with new tokens
  localStorage.setItem("access_token", access_token);
  localStorage.setItem("refresh_token", newRefreshToken);

  // Update cookie for middleware
  document.cookie = `access_token=${access_token}; path=/; max-age=3600; SameSite=Strict`;

  return access_token;
};

export const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor: Add access token to all requests
apiClient.interceptors.request.use(
  (config) => {
    if (typeof window !== "undefined") {
      const token = localStorage.getItem("access_token");
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => Promise.reject(error),
);

// Response interceptor: Handle 401 with automatic token refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Check if this is a 401 error and we haven't already retried
    if (error.response?.status === 401 && !originalRequest._retry && typeof window !== "undefined") {
      // If already refreshing, queue this request
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            return apiClient(originalRequest);
          })
          .catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        // Attempt to refresh the token
        const newAccessToken = await refreshAccessToken();

        // Process all queued requests with the new token
        processQueue(null, newAccessToken);

        // Retry the original request with new token
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
        return apiClient(originalRequest);
      } catch (refreshError) {
        // Refresh failed - reject all queued requests
        processQueue(refreshError, null);

        // Clear all tokens and redirect to login
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        document.cookie = "access_token=; path=/; max-age=0";

        // Redirect to login page
        window.location.href = "/login";

        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  },
);

export default apiClient;
