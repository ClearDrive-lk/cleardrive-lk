import { configureStore } from "@reduxjs/toolkit";
import authReducer from "./features/auth/authSlice";

<<<<<<< HEAD
// 1. Create a function that returns a NEW store instance
export const makeStore = () => {
  return configureStore({
    reducer: {
      auth: authReducer,
    },
  });
};

// 2. Export types based on the return type of makeStore
export type AppStore = ReturnType<typeof makeStore>;
export type RootState = ReturnType<AppStore["getState"]>;
export type AppDispatch = AppStore["dispatch"];

// 3. Custom hooks (Optional but good practice)
import { useDispatch, useSelector, useStore } from "react-redux";
import type { TypedUseSelectorHook } from "react-redux";

export const useAppDispatch: () => AppDispatch = useDispatch;
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector;
export const useAppStore: () => AppStore = useStore;
=======
export const store = configureStore({
  reducer: {
    auth: authReducer,
  },
  devTools: process.env.NODE_ENV !== "production",
});

export type AppStore = typeof store;

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
>>>>>>> 2b6c4e0f3e2bdec671123c59cab390bd0dde93d7
