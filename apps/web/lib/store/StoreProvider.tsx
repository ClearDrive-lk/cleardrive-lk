<<<<<<< HEAD
'use client'

import { useState } from 'react'
import { Provider } from 'react-redux'
import { makeStore, AppStore } from './store'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { GoogleOAuthProvider } from '@react-oauth/google'

export default function StoreProvider({
  children
}: {
  children: React.ReactNode
}) {
  // 1. Use useState for lazy initialization (Runs only once)
  // This fixes "Cannot access refs during render"
  const [store] = useState<AppStore>(() => makeStore())

  // 2. Do the same for QueryClient so it doesn't reset on re-renders
  const [queryClient] = useState(() => new QueryClient())

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
  )
=======
"use client";

import { Provider } from "react-redux";
import { store } from "./store";

export default function StoreProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  // Simple and direct. No refs needed for now.
  return <Provider store={store}>{children}</Provider>;
>>>>>>> 0162e2e977b9ad541379e696dbf240da260a5f98
}
