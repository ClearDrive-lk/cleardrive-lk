const ACCESS_TOKEN_KEY = "access_token";
const REFRESH_TOKEN_KEY = "refresh_token";
const PERSIST_ACCESS_KEY = "auth:persist_access";

const getCookieValue = (name: string) => {
  if (typeof window === "undefined") return null;
  const match = document.cookie
    .split("; ")
    .find((row) => row.startsWith(`${name}=`));
  return match ? decodeURIComponent(match.split("=")[1]) : null;
};

const buildRefreshCookie = (token: string) => {
  const base = `${REFRESH_TOKEN_KEY}=${encodeURIComponent(token)}; path=/; SameSite=Lax`;
  if (typeof window !== "undefined" && window.location.protocol === "https:") {
    return `${base}; Secure`;
  }
  return base;
};

export const saveTokens = (tokens: {
  access_token: string;
  refresh_token?: string;
}, options?: { persistAccess?: boolean }) => {
  if (typeof window !== "undefined") {
    const persistAccess =
      options?.persistAccess ??
      (localStorage.getItem(PERSIST_ACCESS_KEY) ?? "true") === "true";

    sessionStorage.setItem(ACCESS_TOKEN_KEY, tokens.access_token);
    if (persistAccess) {
      localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access_token);
    } else {
      localStorage.removeItem(ACCESS_TOKEN_KEY);
    }
    if (tokens.refresh_token) {
      localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token);
      document.cookie = buildRefreshCookie(tokens.refresh_token);
    }
  }
};

export const getAccessToken = () => {
  if (typeof window === "undefined") return null;
  return (
    sessionStorage.getItem(ACCESS_TOKEN_KEY) ||
    localStorage.getItem(ACCESS_TOKEN_KEY)
  );
};

export const getRefreshToken = () => {
  if (typeof window === "undefined") return null;
  return (
    localStorage.getItem(REFRESH_TOKEN_KEY) ||
    getCookieValue(REFRESH_TOKEN_KEY)
  );
};

export const getPersistAccessPreference = () => {
  if (typeof window === "undefined") return true;
  return (localStorage.getItem(PERSIST_ACCESS_KEY) ?? "true") === "true";
};

export const setPersistAccessPreference = (value: boolean) => {
  if (typeof window !== "undefined") {
    localStorage.setItem(PERSIST_ACCESS_KEY, value ? "true" : "false");
  }
};

export const removeTokens = () => {
  if (typeof window !== "undefined") {
    sessionStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    document.cookie = `${REFRESH_TOKEN_KEY}=; path=/; Max-Age=0`;
  }
};
