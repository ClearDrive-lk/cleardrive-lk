export const saveTokens = (tokens: {
  access_token: string;
  refresh_token?: string;
}) => {
  if (typeof window !== "undefined") {
    sessionStorage.setItem("access_token", tokens.access_token);
    if (tokens.refresh_token) {
      localStorage.setItem("refresh_token", tokens.refresh_token);
      document.cookie = `refresh_token=${tokens.refresh_token}; path=/; SameSite=Lax`;
    }
  }
};

export const getAccessToken = () => {
  if (typeof window !== "undefined")
    return sessionStorage.getItem("access_token");
  return null;
};

export const removeTokens = () => {
  if (typeof window !== "undefined") {
    sessionStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    document.cookie = "refresh_token=; path=/; Max-Age=0";
  }
};
