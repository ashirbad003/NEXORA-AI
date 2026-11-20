import React from "react";
import { cn } from "@/lib/utils";

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  glow?: "cyber" | "violet" | "none";
}

export const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className, glow = "none", children, ...props }, ref) => {
    const glowStyles = {
      none: "border-obsidian-border",
      cyber: "border-cyber/30 shadow-cyber-glow",
      violet: "border-violet-tech/30 shadow-tech-glow",
    };

    return (
      <div
        ref={ref}
        className={cn(
          "bg-obsidian-card border rounded-xl p-6 transition-all duration-200",
          glowStyles[glow],
          className
        )}
        {...props}
      >
        {children}
      </div>
    );
  }
);
Card.displayName = "Card";
