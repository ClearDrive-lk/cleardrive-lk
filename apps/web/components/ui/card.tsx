import * as React from "react";

import { cn } from "@/lib/utils";

function Card({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="card"
      className={cn(
        "bg-card/95 text-card-foreground relative flex flex-col gap-6 overflow-hidden rounded-2xl border border-[#546a7b]/60 py-6 shadow-[0_22px_55px_rgba(57,61,63,0.28)] ring-1 ring-black/10 transition-[transform,box-shadow] duration-200 hover:-translate-y-1 hover:shadow-[0_26px_60px_rgba(57,61,63,0.32)] before:pointer-events-none before:absolute before:inset-0 before:bg-[linear-gradient(180deg,rgba(255,255,255,0.45),transparent_55%)] before:opacity-60 after:pointer-events-none after:absolute after:inset-0 after:bg-[radial-gradient(circle_at_18px_18px,rgba(57,61,63,0.28)_0_2px,transparent_3px),radial-gradient(circle_at_calc(100%-18px)_18px,rgba(57,61,63,0.28)_0_2px,transparent_3px),radial-gradient(circle_at_18px_calc(100%-18px),rgba(57,61,63,0.28)_0_2px,transparent_3px),radial-gradient(circle_at_calc(100%-18px)_calc(100%-18px),rgba(57,61,63,0.28)_0_2px,transparent_3px)]",
        className,
      )}
      {...props}
    />
  );
}

function CardHeader({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="card-header"
      className={cn(
        "@container/card-header grid auto-rows-min grid-rows-[auto_auto] items-start gap-2 px-6 has-data-[slot=card-action]:grid-cols-[1fr_auto] [.border-b]:pb-6",
        className,
      )}
      {...props}
    />
  );
}

function CardTitle({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="card-title"
      className={cn("leading-none font-semibold", className)}
      {...props}
    />
  );
}

function CardDescription({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="card-description"
      className={cn("text-muted-foreground text-sm", className)}
      {...props}
    />
  );
}

function CardAction({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="card-action"
      className={cn(
        "col-start-2 row-span-2 row-start-1 self-start justify-self-end",
        className,
      )}
      {...props}
    />
  );
}

function CardContent({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="card-content"
      className={cn("px-6", className)}
      {...props}
    />
  );
}

function CardFooter({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="card-footer"
      className={cn("flex items-center px-6 [.border-t]:pt-6", className)}
      {...props}
    />
  );
}

export {
  Card,
  CardHeader,
  CardFooter,
  CardTitle,
  CardAction,
  CardDescription,
  CardContent,
};
