import { Search } from "lucide-react";
import { Button } from "@/components/ui/button";

export function HeroSearch() {
  return (
    <div className="relative group w-full max-w-xl mx-auto">
      <div className="absolute -inset-0.5 bg-gradient-to-r from-[#FE7743] to-[#273F4F] rounded-full blur opacity-30 group-hover:opacity-60 transition duration-500" />
      <div className="relative flex items-center bg-black rounded-full border border-white/10 p-2 pr-2">
        <Search className="ml-4 w-5 h-5 text-gray-400" />
        <input
          type="text"
          placeholder="Search by chassis (e.g. CBA-ZE2)..."
          className="w-full bg-transparent border-none focus:ring-0 text-white placeholder-gray-500 px-4 outline-none h-10"
        />
        <Button className="rounded-full bg-[#FE7743] hover:bg-[#ff8a5c] text-black font-bold px-6">
          Search
        </Button>
      </div>
    </div>
  );
}
