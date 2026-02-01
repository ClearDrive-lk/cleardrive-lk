'use client';

import { useState, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
// I added 'Zap' to the import list below 👇
import { Loader2, ShieldCheck, ArrowRight, Zap } from 'lucide-react';
import Link from 'next/link';

export default function OTPPage() {
  const [otp, setOtp] = useState(['', '', '', '', '', '']);
  const [loading, setLoading] = useState(false);
  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);

  const handleChange = (index: number, value: string) => {
    if (isNaN(Number(value))) return;
    const newOtp = [...otp];
    newOtp[index] = value;
    setOtp(newOtp);
    if (value && index < 5) inputRefs.current[index + 1]?.focus();
  };

  const handleKeyDown = (index: number, e: React.KeyboardEvent) => {
    if (e.key === 'Backspace' && !otp[index] && index > 0) inputRefs.current[index - 1]?.focus();
  };

  const handleVerify = async () => {
    setLoading(true);
    setTimeout(() => {
        alert(`Verifying Code: ${otp.join('')}`);
        setLoading(false);
    }, 1500);
  };

  return (
    <div className="min-h-screen w-full flex bg-[#050505] relative overflow-hidden font-sans">
      <div className="hidden lg:flex w-1/2 relative flex-col justify-between p-12 z-10 border-r border-white/5">
        <div className="absolute top-0 left-0 w-full h-full overflow-hidden z-0">
             <div className="absolute top-[20%] left-[20%] w-[600px] h-[600px] bg-[#FE7743]/5 rounded-full blur-[120px]" />
             <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:40px_40px]" />
        </div>
        <div className="relative z-10">
            <h1 className="text-2xl font-bold text-white tracking-tighter flex items-center gap-2">
                <ShieldCheck className="text-[#FE7743]" /> Security Gateway
            </h1>
        </div>
        <div className="relative z-10 space-y-6 max-w-lg">
            <h2 className="text-4xl font-bold text-white leading-tight">Banking-Grade <br/> Security Standard.</h2>
            <div className="space-y-4">
                <div className="flex items-center gap-3 text-gray-400">
                    <div className="w-8 h-8 rounded-full bg-white/5 flex items-center justify-center text-[#FE7743]"><Zap className="w-4 h-4"/></div>
                    <p>Instant verification via SMS/Email</p>
                </div>
                <div className="flex items-center gap-3 text-gray-400">
                    <div className="w-8 h-8 rounded-full bg-white/5 flex items-center justify-center text-[#FE7743]"><ShieldCheck className="w-4 h-4"/></div>
                    <p>End-to-End Encrypted Session</p>
                </div>
            </div>
        </div>
        <div className="relative z-10 text-xs text-gray-600 font-mono">ID: AUTH-8829-XJ // ENCRYPTED SESSION</div>
      </div>

      <div className="w-full lg:w-1/2 flex items-center justify-center p-6 relative z-10">
        <div className="w-full max-w-md bg-white/5 backdrop-blur-xl border border-white/10 p-8 rounded-2xl shadow-2xl relative z-10">
            <div className="mb-8 text-center">
                <div className="mx-auto w-12 h-12 bg-[#FE7743]/10 rounded-full flex items-center justify-center mb-4 border border-[#FE7743]/20">
                    <ShieldCheck className="text-[#FE7743] w-6 h-6" />
                </div>
                <h3 className="text-2xl font-bold text-white mb-2">Verification Code</h3>
                <p className="text-gray-400 text-sm">Enter the 6-digit code sent to your device.</p>
            </div>
            <div className="space-y-8">
                <div className="flex gap-2 justify-center">
                    {otp.map((digit, index) => (
                        <Input key={index} ref={(el) => { inputRefs.current[index] = el }} type="text" maxLength={1} value={digit}
                            onChange={(e) => handleChange(index, e.target.value)} onKeyDown={(e) => handleKeyDown(index, e)}
                            className="w-12 h-14 text-center text-xl bg-black/40 border-white/10 focus:border-[#FE7743] transition-all text-white font-mono rounded-lg"
                        />
                    ))}
                </div>
                <Button onClick={handleVerify} disabled={loading || otp.some(d => !d)} className="w-full bg-[#FE7743] hover:bg-[#FE7743]/90 text-black font-bold h-11">
                    {loading ? <Loader2 className="animate-spin" /> : 'Verify Access'}
                </Button>
                <div className="text-center text-xs text-gray-500 font-mono">Didn&apos;t receive code? <button className="hover:text-white underline">Resend in 30s</button></div>
            </div>
        </div>
      </div>
    </div>
  );
}