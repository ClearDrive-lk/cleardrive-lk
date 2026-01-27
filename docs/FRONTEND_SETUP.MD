FRONTEND_SETUP.md
markdown# Frontend Setup Guide - For Lehan

## 🎯 Your Tasks (Sprint 1)

### Week 1-2:
- [ ] CD-80: Next.js 14 Project Setup
- [ ] CD-81: Authentication UI (Login, OTP, Protected Routes)

### Week 3-4:
- [ ] CD-82: Vehicle Browse & Search UI
- [ ] CD-90: Nonce-Based CSP Implementation (collaborate with Malith)

## 📋 Prerequisites

1. **Backend is running** ✅
   - Malith has already set this up
   - API running at: `http://localhost:8000`
   - Swagger docs: `http://localhost:8000/api/v1/docs`

2. **Install Node.js**
```bash
   # Install Node.js 18+ (LTS)
   # Download from: https://nodejs.org/
   
   # Verify installation
   node --version  # Should be 18+
   npm --version
```

## 🚀 Step 1: Setup Next.js Project (CD-80)

### Create Next.js App
```bash
# Navigate to apps directory
cd apps

# Create Next.js 14 app with App Router
npx create-next-app@latest web

# Choose these options:
# ✔ Would you like to use TypeScript? Yes
# ✔ Would you like to use ESLint? Yes
# ✔ Would you like to use Tailwind CSS? Yes
# ✔ Would you like to use `src/` directory? No
# ✔ Would you like to use App Router? Yes
# ✔ Would you like to customize the default import alias? No

# Navigate to web app
cd web

# Install additional dependencies
npm install axios @tanstack/react-query zustand
npm install @radix-ui/react-dialog @radix-ui/react-dropdown-menu
npm install class-variance-authority clsx tailwind-merge
npm install lucide-react

# Install shadcn/ui CLI
npx shadcn-ui@latest init

# Choose these options:
# ✔ Which style? Default
# ✔ Which color? Slate
# ✔ Would you like to use CSS variables? Yes

# Install useful shadcn components
npx shadcn-ui@latest add button
npx shadcn-ui@latest add input
npx shadcn-ui@latest add card
npx shadcn-ui@latest add dialog
npx shadcn-ui@latest add dropdown-menu
npx shadcn-ui@latest add toast
```

### Create Environment File

**apps/web/.env.local**
```bash
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1

# Google OAuth (get from Malith)
NEXT_PUBLIC_GOOGLE_CLIENT_ID=your-google-client-id

# App Configuration
NEXT_PUBLIC_APP_NAME=ClearDrive.lk
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

### Update next.config.js

**apps/web/next.config.js**
```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    domains: ['localhost', 'your-supabase-project.supabase.co'],
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/v1/:path*',
      },
    ];
  },
};

module.exports = nextConfig;
```

### Test the Setup
```bash
# Start development server
npm run dev

# Open browser
# http://localhost:3000

# You should see the default Next.js page
```

## 🔐 Step 2: Authentication UI (CD-81)

### File Structure to Create
```
apps/web/
├── app/
│   ├── (auth)/
│   │   ├── login/
│   │   │   └── page.tsx          # Login page with Google button
│   │   └── verify-otp/
│   │       └── page.tsx          # OTP verification page
│   ├── (dashboard)/
│   │   ├── layout.tsx            # Protected layout
│   │   ├── page.tsx              # Dashboard home
│   │   └── vehicles/
│   │       └── page.tsx          # Vehicle list
│   └── layout.tsx                # Root layout
├── components/
│   ├── auth/
│   │   ├── GoogleLoginButton.tsx
│   │   ├── OTPForm.tsx
│   │   └── ProtectedRoute.tsx
│   └── ui/                       # shadcn components
├── lib/
│   ├── api.ts                    # Axios client
│   ├── auth.ts                   # Auth utilities
│   └── store.ts                  # Zustand store
└── types/
    └── index.ts                  # TypeScript types
```

### Create API Client

**apps/web/lib/api.ts**
```typescript
import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - add auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor - handle token refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // If 401 and not already retried
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        
        if (!refreshToken) {
          // No refresh token, redirect to login
          window.location.href = '/login';
          return Promise.reject(error);
        }

        // Try to refresh token
        const { data } = await axios.post(`${API_URL}/auth/refresh`, {
          refresh_token: refreshToken,
        });

        // Save new tokens
        localStorage.setItem('access_token', data.access_token);
        localStorage.setItem('refresh_token', data.refresh_token);

        // Retry original request with new token
        originalRequest.headers.Authorization = `Bearer ${data.access_token}`;
        return apiClient(originalRequest);
      } catch (refreshError) {
        // Refresh failed, redirect to login
        localStorage.clear();
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export default apiClient;
```

### Create Auth Store

**apps/web/lib/store.ts**
```typescript
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface User {
  id: string;
  email: string;
  name: string;
  role: string;
}

interface AuthStore {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  setAuth: (user: User, accessToken: string, refreshToken: string) => void;
  clearAuth: () => void;
  isAuthenticated: () => boolean;
}

export const useAuthStore = create()(
  persist(
    (set, get) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      
      setAuth: (user, accessToken, refreshToken) => {
        set({ user, accessToken, refreshToken });
        localStorage.setItem('access_token', accessToken);
        localStorage.setItem('refresh_token', refreshToken);
      },
      
      clearAuth: () => {
        set({ user: null, accessToken: null, refreshToken: null });
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
      },
      
      isAuthenticated: () => {
        const { accessToken } = get();
        return !!accessToken;
      },
    }),
    {
      name: 'auth-storage',
    }
  )
);
```

### Create Google Login Button Component

**apps/web/components/auth/GoogleLoginButton.tsx**
```typescript
'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import apiClient from '@/lib/api';

export function GoogleLoginButton() {
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleGoogleLogin = async () => {
    setLoading(true);
    
    try {
      // Initialize Google Sign-In
      // (This is a simplified version - you'll need to implement Google OAuth properly)
      
      // For now, let's just redirect to OTP page for testing
      // In production, you'd get the Google ID token here
      
      const response = await apiClient.post('/auth/google', {
        id_token: 'dummy-token-for-testing',
      });
      
      // Store email for OTP verification
      sessionStorage.setItem('auth_email', response.data.email);
      
      // Redirect to OTP page
      router.push('/verify-otp');
      
    } catch (error) {
      console.error('Google login failed:', error);
      alert('Login failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    
      {loading ? 'Loading...' : 'Continue with Google'}
    
  );
}
```

### Create Login Page

**apps/web/app/(auth)/login/page.tsx**
```typescript
import { GoogleLoginButton } from '@/components/auth/GoogleLoginButton';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

export default function LoginPage() {
  return (
    
      
        
          
            Welcome to ClearDrive.lk
          
          
            Import your dream vehicle from Japan
          
        
        
          
          
            By continuing, you agree to our Terms of Service and Privacy Policy
          
        
      
    
  );
}
```

## 📚 API Endpoints You'll Use

### Authentication
```typescript
// Google Login
POST /auth/google
Body: { id_token: string }

// Verify OTP
POST /auth/verify-otp
Body: { email: string, otp: string }

// Refresh Token
POST /auth/refresh
Body: { refresh_token: string }

// Logout
POST /auth/logout
Headers: { Authorization: Bearer {token} }
```

### Vehicles
```typescript
// List Vehicles
GET /vehicles?search=Toyota&page=1&limit=20

// Get Vehicle
GET /vehicles/{id}

// Calculate Cost
GET /vehicles/{id}/cost?exchange_rate=2.25
```

## 🧪 Testing

### Manual Testing Steps

1. **Start backend** (should already be running)
```bash
   docker-compose up -d
```

2. **Start frontend**
```bash
   cd apps/web
   npm run dev
```

3. **Test flow:**
   - Visit `http://localhost:3000/login`
   - Click "Continue with Google"
   - Check console for OTP (in development mode)
   - Enter OTP
   - Should redirect to dashboard

### Test API Connection

**Test script: `apps/web/test-api.js`**
```javascript
const axios = require('axios');

async function testAPI() {
  try {
    // Test 1: Get vehicles
    const response = await axios.get('http://localhost:8000/api/v1/vehicles');
    console.log('✅ API Connected');
    console.log(`Found ${response.data.total} vehicles`);
  } catch (error) {
    console.error('❌ API Connection Failed:', error.message);
  }
}

testAPI();
```

Run: `node test-api.js`

## 🎨 Design System

### Colors (Tailwind)
```
- Primary: Blue (slate-700)
- Success: Green
- Warning: Yellow
- Error: Red
- Background: Gray-50
- Text: Gray-900
```

### Typography
```
- Headings: font-bold
- Body: font-normal
- Small: text-sm
```

### Components (shadcn/ui)
Already installed:
- Button
- Card
- Dialog
- Dropdown Menu
- Input
- Toast

## 📞 Need Help?

### Contact Malith:
- Backend API issues
- Authentication problems
- CORS issues
- Database/Redis questions

### Resources:
- Backend API: http://localhost:8000/api/v1/docs
- Next.js Docs: https://nextjs.org/docs
- shadcn/ui: https://ui.shadcn.com
- Tailwind: https://tailwindcss.com

## ✅ Checklist Before Starting

- [ ] Backend is running (`docker-compose up -d`)
- [ ] Can access API docs (`http://localhost:8000/api/v1/docs`)
- [ ] Node.js 18+ installed
- [ ] Read this document completely
- [ ] Have Google Client ID (ask Malith)

## 🚀 Let's Go!

Once you complete CD-80 and CD-81, we'll have:
- ✅ Working authentication flow
- ✅ Protected routes
- ✅ User session management
- ✅ Ready for vehicle browsing UI (CD-82)

Good luck! 🎉