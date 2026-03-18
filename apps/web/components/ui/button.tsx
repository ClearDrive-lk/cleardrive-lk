import { Slot } from "@radix-ui/react-slot";
import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center whitespace-nowrap rounded-lg text-sm font-semibold tracking-wide ring-offset-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 relative overflow-hidden",
  {
    variants: {
      variant: {
        default:
          "border border-[hsl(var(--bronze))] bg-[linear-gradient(135deg,hsl(var(--steel-soft))_0%,hsl(var(--primary))_45%,hsl(var(--bronze))_100%)] text-primary-foreground shadow-[0_16px_32px_rgba(57,61,63,0.28)] before:absolute before:inset-0 before:bg-[linear-gradient(180deg,rgba(255,255,255,0.4),transparent_55%)] before:opacity-70 before:content-[''] after:absolute after:inset-0 after:bg-[radial-gradient(140%_120%_at_10%_0%,rgba(255,255,255,0.45),transparent_60%)] after:opacity-70 after:content-[''] hover:shadow-[0_20px_40px_rgba(57,61,63,0.35)]",
        destructive:
          "bg-destructive text-destructive-foreground hover:bg-destructive/90",
        outline:
          "border border-[hsl(var(--steel))] bg-background hover:bg-accent hover:text-accent-foreground",
        secondary:
          "border border-[hsl(var(--steel))] bg-[linear-gradient(135deg,hsl(var(--secondary))_0%,hsl(var(--steel))_100%)] text-secondary-foreground hover:opacity-90",
        ghost:
          "hover:bg-accent hover:text-accent-foreground",
        link: "text-primary underline-offset-4 hover:underline",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-9 rounded-md px-3",
        lg: "h-11 rounded-md px-8",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  },
);

export interface ButtonProps
  extends
    React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    );
  },
);
Button.displayName = "Button";

export { Button, buttonVariants };
