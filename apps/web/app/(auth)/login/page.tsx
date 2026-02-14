'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation'; // Import Router
import Link from 'next/link';
import { GoogleLoginButton } from '@/components/auth/GoogleLoginButton';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Loader2 } from 'lucide-react';

export default function LoginPage() {
  const [loading, setLoading] = useState(false);
  const router = useRouter(); // Initialize Router

  const handleEmailLogin = (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    // --- FIX: GIVE THE USER A TICKET (COOKIE) ---
    // In a real app, your backend sends this. For now, we simulate it.
    document.cookie = "access_token=valid-vip-pass; path=/; max-age=86400"; 

    setTimeout(() => {
        setLoading(false);
        // Redirect to Dashboard
        router.push('/dashboard'); 
    }, 1500);
  };

  return (
    <div className="min-h-screen w-full flex bg-[#050505] relative overflow-hidden font-sans">
      
      {/* --- VISUAL SIDE (LEFT) --- */}
      <div className="hidden lg:flex w-1/2 relative flex-col justify-between p-12 z-10">
        <div className="absolute top-0 left-0 w-full h-full overflow-hidden z-0">
             <div className="absolute top-[-20%] left-[-20%] w-[800px] h-[800px] bg-[#FE7743]/10 rounded-full blur-[120px]" />
             <div className="absolute bottom-[-20%] right-[-20%] w-[600px] h-[600px] bg-[#273F4F]/20 rounded-full blur-[100px]" />
             <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:40px_40px]" />
        </div>

        <div className="relative z-10">
            <h1 className="text-4xl font-bold text-white tracking-tighter">
                ClearDrive<span className="text-[#FE7743]">.lk</span>
            </h1>
            <p className="text-gray-400 mt-2 text-sm uppercase tracking-widest font-mono">
                Direct Market Access Terminal v1.0
            </p>
        </div>

        <div className="relative z-10 space-y-6 max-w-lg">
            <h2 className="text-5xl font-bold text-white leading-tight">
                Import Vehicles <br/>
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#FE7743] to-orange-200">
                    Without The Middleman.
                </span>
            </h2>
            <p className="text-gray-400 text-lg leading-relaxed">
                Access real-time JPY auction data, calculate landed costs instantly, and secure your vehicle with blockchain-verified transparency.
            </p>
        </div>

        <div className="relative z-10 text-xs text-gray-600 font-mono">
            © 2026 CLEARDRIVE INC. // SECURE CONNECTION ESTABLISHED
        </div>
      </div>

      {/* --- FORM SIDE (RIGHT) --- */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-6 relative z-10">
        <div className="w-full max-w-md bg-white/5 backdrop-blur-xl border border-white/10 p-8 rounded-2xl shadow-2xl relative z-10">
            <div className="mb-8 text-center lg:text-left">
                <h3 className="text-2xl font-bold text-white mb-2">Welcome Back</h3>
                <p className="text-gray-400 text-sm">Enter your credentials to access the terminal.</p>
            </div>

            <form onSubmit={handleEmailLogin} className="space-y-4">
                <div className="space-y-2">
                    <Label htmlFor="email" className="text-xs font-mono text-gray-400 uppercase">Email Address</Label>
                    <Input id="email" placeholder="agent@cleardrive.lk" type="email" className="bg-black/40 border-white/10 text-white placeholder:text-gray-600 focus:border-[#FE7743] h-11" />
                </div>
                <div className="space-y-2">
                    <div className="flex justify-between items-center">
                        <Label htmlFor="password" className="text-xs font-mono text-gray-400 uppercase">Password</Label>
                        <Link href="#" className="text-xs text-[#FE7743] hover:text-[#FE7743]/80">Forgot?</Link>
                    </div>
                    <Input id="password" type="password" className="bg-black/40 border-white/10 text-white focus:border-[#FE7743] h-11" />
                </div>
                <Button type="submit" disabled={loading} className="w-full bg-[#FE7743] hover:bg-[#FE7743]/90 text-black font-bold h-11">
                    {loading ? <Loader2 className="animate-spin" /> : 'Sign In'}
                </Button>
            </form>

            <div className="relative my-8">
                <div className="absolute inset-0 flex items-center"><span className="w-full border-t border-white/10"></span></div>
                <div className="relative flex justify-center text-xs uppercase"><span className="bg-[#0A0A0A]/50 backdrop-blur px-2 text-gray-500">Or continue with</span></div>
            </div>

            <div className="w-full"><GoogleLoginButton /></div>
            <div className="mt-8 text-center text-sm text-gray-500">
                Don&apos;t have an account? <Link href="/register" className="text-white hover:text-[#FE7743] font-medium transition-colors">Request Access</Link>
            </div>
        </div>
      </div>
    </div>
  );
}
