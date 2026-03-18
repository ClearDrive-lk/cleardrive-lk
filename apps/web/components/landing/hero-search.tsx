import { Search } from "lucide-react";
import { Button } from "@/components/ui/button";

export function HeroSearch() {
  return (
    <div className="relative group w-full max-w-xl mx-auto">
      <div className="absolute -inset-0.5 bg-gradient-to-r from-[#62929e] to-[#546a7b] rounded-full blur opacity-30 group-hover:opacity-60 transition duration-500" />
      <div className="relative flex items-center bg-[#fdfdff] rounded-full border border-[#546a7b]/65 p-2 pr-2">
        <Search className="ml-4 w-5 h-5 text-[#546a7b]" />
        <input
          type="text"
          placeholder="Search by chassis (e.g. CBA-ZE2)..."
          className="w-full bg-transparent border-none focus:ring-0 text-[#393d3f] placeholder-gray-500 px-4 outline-none h-10"
        />
        <Button className="rounded-full bg-[#62929e] hover:bg-[#546a7b] text-[#fdfdff] font-bold px-6">
          Search
        </Button>
      </div>
    </div>
  );
}

