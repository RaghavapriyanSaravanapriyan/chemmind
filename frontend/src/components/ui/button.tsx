import * as React from "react"
import { cn } from "@/lib/utils"

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "default" | "secondary" | "outline" | "ghost";
  size?: "default" | "sm" | "lg" | "icon";
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "default", size = "default", ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(
          "inline-flex items-center justify-center gap-1 whitespace-nowrap rounded-lg text-sm font-semibold transition-[transform,background-color,color,box-shadow,border-color] duration-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/40 disabled:pointer-events-none disabled:opacity-50",
          {
            "bg-foreground text-background shadow-sm hover:-translate-y-px hover:shadow-md active:translate-y-0": variant === "default",
            "bg-surface text-foreground shadow-sm hover:-translate-y-px hover:bg-background hover:shadow-md border border-border active:translate-y-0": variant === "secondary",
            "border border-border bg-transparent shadow-sm hover:bg-surface text-foreground active:scale-[0.98]": variant === "outline",
            "hover:bg-surface hover:text-foreground active:scale-[0.98] text-muted hover:text-foreground": variant === "ghost",
            "h-10 px-4 py-2": size === "default",
            "h-8 rounded-md px-3 text-xs": size === "sm",
            "h-12 rounded-xl px-8 text-base": size === "lg",
            "h-9 w-9": size === "icon",
          },
          className
        )}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"

export { Button }
