import React from "react";
import Link from "next/link";

export function Footer() {
  return (
    <footer className="border-t border-obsidian-border bg-obsidian py-8 px-4 text-xs text-text-muted">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-text-secondary">NEXORA AI</span>
          <span>&copy; {new Date().getFullYear()} — Intelligence That Moves You Forward.</span>
        </div>
        <div className="flex gap-6">
          <Link href="/privacy" className="hover:text-cyber transition-colors">
            Privacy Policy
          </Link>
          <Link href="/terms" className="hover:text-cyber transition-colors">
            Terms of Service
          </Link>
          <Link href="/security" className="hover:text-cyber transition-colors">
            Security Architecture
          </Link>
        </div>
      </div>
    </footer>
  );
}
