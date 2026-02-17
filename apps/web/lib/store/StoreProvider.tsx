"use client";

<<<<<<< HEAD
import { useState } from "react";
import { Provider } from "react-redux";
import { makeStore, AppStore } from "./store";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { GoogleOAuthProvider } from "@react-oauth/google";
=======
import { Provider } from "react-redux";
import { store } from "./store";
>>>>>>> 2b6c4e0f3e2bdec671123c59cab390bd0dde93d7

export default function StoreProvider({
  children,
}: {
  children: React.ReactNode;
}) {
<<<<<<< HEAD
  // 1. Use useState for lazy initialization (Runs only once)
  // This fixes "Cannot access refs during render"
  const [store] = useState<AppStore>(() => makeStore());

  // 2. Do the same for QueryClient so it doesn't reset on re-renders
  const [queryClient] = useState(() => new QueryClient());

  // Get Client ID safely
  const clientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || "";

  return (
    <Provider store={store}>
      <QueryClientProvider client={queryClient}>
        <GoogleOAuthProvider clientId={clientId}>
          {children}
        </GoogleOAuthProvider>
      </QueryClientProvider>
    </Provider>
  );
=======
  // Simple and direct. No refs needed for now.
  return <Provider store={store}>{children}</Provider>;
>>>>>>> 2b6c4e0f3e2bdec671123c59cab390bd0dde93d7
}
