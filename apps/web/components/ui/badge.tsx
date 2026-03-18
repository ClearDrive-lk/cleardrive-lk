import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center justify-center rounded-md border px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.16em] w-fit whitespace-nowrap shrink-0 [&>svg]:size-3 gap-1 [&>svg]:pointer-events-none focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px] aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40 aria-invalid:border-destructive transition-[color,box-shadow,transform] duration-200 hover:-translate-y-[1px] overflow-hidden relative before:absolute before:inset-0 before:bg-[linear-gradient(180deg,rgba(255,255,255,0.4),transparent_55%)] before:opacity-70 before:content-['']",
  {
    variants: {
      variant: {
        default:
          "border-[hsl(var(--bronze))] bg-[linear-gradient(135deg,hsl(var(--steel-soft))_0%,hsl(var(--card))_45%,hsl(var(--bronze-soft))_100%)] text-foreground shadow-[inset_0_1px_0_rgba(255,255,255,0.6),_0_8px_18px_rgba(57,61,63,0.25)] [a&]:hover:opacity-90",
        secondary:
          "border-[hsl(var(--steel))] bg-[linear-gradient(135deg,hsl(var(--card))_0%,hsl(var(--muted))_100%)] text-foreground [a&]:hover:opacity-90",
        destructive:
          "bg-destructive text-[#393d3f] [a&]:hover:bg-destructive/90 focus-visible:ring-destructive/20 dark:focus-visible:ring-destructive/40 dark:bg-destructive/60",
        outline:
          "border-[hsl(var(--steel))] text-foreground [a&]:hover:bg-accent [a&]:hover:text-accent-foreground",
        ghost: "[a&]:hover:bg-accent [a&]:hover:text-accent-foreground",
        link: "text-primary underline-offset-4 [a&]:hover:underline",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  },
);

function Badge({
  className,
  variant = "default",
  asChild = false,
  ...props
}: React.ComponentProps<"span"> &
  VariantProps<typeof badgeVariants> & { asChild?: boolean }) {
  const Comp = asChild ? Slot : "span";

  return (
    <Comp
      data-slot="badge"
      data-variant={variant}
      className={cn(badgeVariants({ variant }), className)}
      {...props}
    />
  );
}

export { Badge, badgeVariants };

