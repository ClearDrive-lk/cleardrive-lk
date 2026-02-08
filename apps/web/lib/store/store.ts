import { configureStore } from '@reduxjs/toolkit'
import authReducer from './features/auth/authSlice'

// 1. Create a function that returns a NEW store instance
export const makeStore = () => {
  return configureStore({
    reducer: {
      auth: authReducer,
    },
  })
}

// 2. Export types based on the return type of makeStore
export type AppStore = ReturnType<typeof makeStore>
export type RootState = ReturnType<AppStore['getState']>
export type AppDispatch = AppStore['dispatch']

// 3. Custom hooks (Optional but good practice)
import { useDispatch, useSelector, useStore } from 'react-redux'
import type { TypedUseSelectorHook } from 'react-redux'

export const useAppDispatch: () => AppDispatch = useDispatch
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector
export const useAppStore: () => AppStore = useStore