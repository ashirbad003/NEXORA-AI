import React from "react";
import { cn } from "@/lib/utils";

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: "cyber" | "violet" | "neutral" | "danger";
}

export const Badge: React.FC<BadgeProps> = ({
  className,
  variant = "cyber",
  children,
  ...props
}) => {
  const variants = {
    cyber: "bg-cyber/10 text-cyber border-cyber/30",
    violet: "bg-violet-tech/10 text-violet-tech border-violet-tech/30",
    neutral: "bg-obsidian-surface text-text-secondary border-obsidian-border",
    danger: "bg-red-500/10 text-red-400 border-red-500/30",
  };

  return (
    <span
      className={cn(
        "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border",
        variants[variant],
        className
      )}
      {...props}
    >
      {children}
    </span>
  );
};
