"use client";

import Image from "next/image";

import { cn } from "@/lib/utils";

type BrandMarkProps = {
  className?: string;
  size?: number;
};

type BrandWordmarkProps = {
  className?: string;
  dotClassName?: string;
};

export function BrandMark({ className, size = 32 }: BrandMarkProps) {
  return (
    <Image
      src="/cleardrive-logo.png"
      alt="ClearDrive logo"
      width={size}
      height={size}
      className={cn("rounded-md object-contain", className)}
    />
  );
}

export function BrandWordmark({ className, dotClassName }: BrandWordmarkProps) {
  return (
    <span className={cn("inline-flex items-baseline", className)}>
      <span className="leading-none">ClearDrive</span>
      <span className={cn("leading-none text-[#62929e]", dotClassName)}>
        .lk
      </span>
    </span>
  );
}
