export function AuctionTicker() {
    return (
      <div className="w-full bg-[#0F0F0F] border-b border-white/5 overflow-hidden py-2 select-none">
        {/* We use Array(10) to ensure the content is WAY wider than any screen.
           The animation moves -50% of the total width. 
           Since we have repeating patterns, as long as the pattern repeats seamlessly, 
           the snap back to 0% is invisible.
        */}
        <div className="flex animate-marquee whitespace-nowrap w-max">
          {[...Array(10)].map((_, i) => (
            <div key={i} className="flex items-center pr-12"> {/* pr-12 handles the gap */}
              <span className="flex items-center gap-2 mr-12">
                <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse shadow-[0_0_8px_rgba(34,197,94,0.5)]" />
                <span className="text-gray-400 font-mono text-xs">TOYOTA PRIUS 2020</span>
                <span className="text-white font-bold text-xs">¥1.85M</span>
              </span>
              
              <span className="flex items-center gap-2 mr-12">
                <span className="w-1.5 h-1.5 rounded-full bg-orange-500 shadow-[0_0_8px_rgba(249,115,22,0.5)]" />
                <span className="text-gray-400 font-mono text-xs">HONDA VEZEL</span>
                <span className="text-white font-bold text-xs">¥2.1M</span>
              </span>
              
              <span className="flex items-center gap-2 mr-12">
                <span className="text-gray-500 font-mono text-xs">JPY/LKR</span>
                <span className="text-[#FE7743] font-bold text-xs">2.25</span>
              </span>
              
              <span className="flex items-center gap-2 mr-12">
                <span className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse" />
                <span className="text-gray-400 font-mono text-xs">USS TOKYO</span>
                <span className="text-white font-bold text-xs">LIVE</span>
              </span>
              
              <span className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.5)]" />
                <span className="text-gray-400 font-mono text-xs">LAND CRUISER PRADO</span>
                <span className="text-white font-bold text-xs">¥4.2M</span>
              </span>
            </div>
          ))}
        </div>
      </div>
    );
  }