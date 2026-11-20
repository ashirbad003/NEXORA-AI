"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/authContext";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";

export function Navbar() {
  const { user, isAuthenticated, logout, hasRole } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 w-full border-b border-obsidian-border bg-obsidian/80 backdrop-blur-md">
      <div className="max-w-7xl mx-auto flex h-16 items-center justify-between px-4 sm:px-6 lg:px-8">
        {/* Brand */}
        <div className="flex items-center gap-3">
          <Link href="/" className="flex items-center gap-2 group">
            <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-cyber to-violet-tech flex items-center justify-center font-black text-obsidian text-lg">
              N
            </div>
            <span className="font-extrabold text-xl tracking-tight text-text-primary group-hover:text-cyber transition-colors">
              NEXORA <span className="text-cyber">AI</span>
            </span>
          </Link>
          <Badge variant="cyber">v1.0-Phase4</Badge>
        </div>

        {/* Navigation Links */}
        <nav className="hidden md:flex items-center gap-6 text-sm font-medium text-text-secondary">
          <Link href="/" className="hover:text-cyber transition-colors">
            Home
          </Link>
          <Link href="/learn" className="hover:text-cyber transition-colors">
            Learning Hub
          </Link>
          <Link href="/visualizer" className="hover:text-cyber transition-colors">
            DSA Visualizer
          </Link>
          <Link href="/coding" className="hover:text-cyber transition-colors">
            Coding Arena
          </Link>
          {isAuthenticated && (
            <>
              {hasRole("STUDENT") && (
                <Link href="/student/dashboard" className="hover:text-cyber transition-colors">
                  Dashboard
                </Link>
              )}
              {hasRole("PLACEMENT_CELL") && (
                <Link href="/placement" className="hover:text-cyber transition-colors">
                  Placement Cell
                </Link>
              )}
              {hasRole("ADMIN") && (
                <Link href="/admin" className="hover:text-cyber transition-colors">
                  Admin Console
                </Link>
              )}
            </>
          )}
        </nav>

        {/* User / Actions */}
        <div className="hidden md:flex items-center gap-4">
          {isAuthenticated && user ? (
            <div className="flex items-center gap-3">
              <div className="text-right">
                <p className="text-sm font-semibold text-text-primary leading-none">{user.full_name}</p>
                <p className="text-xs text-text-muted mt-1">{user.email}</p>
              </div>
              <Button variant="outline" size="sm" onClick={logout}>
                Sign Out
              </Button>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <Link href="/login">
                <Button variant="outline" size="sm">
                  Sign In
                </Button>
              </Link>
              <Link href="/register">
                <Button variant="primary" size="sm">
                  Get Started
                </Button>
              </Link>
            </div>
          )}
        </div>

        {/* Mobile menu button */}
        <div className="flex md:hidden">
          <button
            type="button"
            className="text-text-secondary hover:text-text-primary p-2"
            onClick={() => setMenuOpen(!menuOpen)}
          >
            <span className="sr-only">Toggle Menu</span>
            ☰
          </button>
        </div>
      </div>

      {/* Mobile Menu Dropdown */}
      {menuOpen && (
        <div className="md:hidden border-b border-obsidian-border bg-obsidian-surface px-4 py-4 space-y-3 text-sm">
          <Link href="/" className="block text-text-secondary hover:text-cyber">
            Home
          </Link>
          {isAuthenticated ? (
            <>
              <div className="pt-2 border-t border-obsidian-border text-xs text-text-muted">
                Signed in as {user?.email}
              </div>
              <Button variant="outline" size="sm" className="w-full" onClick={logout}>
                Sign Out
              </Button>
            </>
          ) : (
            <div className="flex flex-col gap-2 pt-2 border-t border-obsidian-border">
              <Link href="/login">
                <Button variant="outline" size="sm" className="w-full">
                  Sign In
                </Button>
              </Link>
              <Link href="/register">
                <Button variant="primary" size="sm" className="w-full">
                  Get Started
                </Button>
              </Link>
            </div>
          )}
        </div>
      )}
    </header>
  );
}
