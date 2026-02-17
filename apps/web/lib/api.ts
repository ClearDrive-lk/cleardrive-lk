import axios from "axios";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

apiClient.interceptors.request.use(
  (config) => {
    if (typeof window !== "undefined") {
<<<<<<< HEAD
      const token = sessionStorage.getItem("access_token");
=======
      const token = localStorage.getItem("access_token");
>>>>>>> 2b6c4e0f3e2bdec671123c59cab390bd0dde93d7
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
<<<<<<< HEAD
      sessionStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      document.cookie = "access_token=; path=/; max-age=0";
      document.cookie = "refresh_token=; path=/; max-age=0";
=======
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      document.cookie = "access_token=; path=/; max-age=0";
>>>>>>> 2b6c4e0f3e2bdec671123c59cab390bd0dde93d7
      window.location.href = "/login";
    }
    return Promise.reject(error);
  },
);

export default apiClient;
