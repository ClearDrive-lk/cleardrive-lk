import { AuctionTicker } from "@/components/ui/ticker";
import { GridBackground } from "@/components/ui/grid-background";
import { HeroSearch } from "@/components/landing/hero-search";

export default function Home() {
  return (
    <main className="min-h-screen relative flex flex-col">
      <GridBackground />
      <AuctionTicker />
      
      <div className="flex-1 flex flex-col items-center justify-center px-4 py-20">
        <div className="max-w-4xl text-center space-y-8">
          <div className="space-y-4">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 text-xs font-mono text-[#FE7743]">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#FE7743] opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-[#FE7743]"></span>
              </span>
              SYSTEM ONLINE
            </div>
            
            <h1 className="text-6xl md:text-8xl font-bold tracking-tighter text-white">
              CLEAR<span className="text-transparent bg-clip-text bg-gradient-to-r from-[#FE7743] to-orange-200">DRIVE</span>
            </h1>
            
            <p className="text-xl text-gray-400 max-w-2xl mx-auto font-light leading-relaxed">
              The direct-access vehicle import terminal for Sri Lanka. 
              <br/><span className="text-gray-500">No middlemen. No hidden fees. Just code & logistics.</span>
            </p>
          </div>

          {/* The Holographic Search */}
          <div className="py-8">
            <HeroSearch />
          </div>

          <div className="flex gap-6 justify-center text-sm text-gray-500 font-mono">
            <span>• USS TOKYO DIRECT</span>
            <span>• REAL-TIME JPY</span>
            <span>• AI VERIFIED</span>
          </div>
        </div>
      </div>
    </main>
  );
}