"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";

interface Problem {
  id: string;
  slug: string;
  title: string;
  difficulty: string;
  category: string;
  tags?: string;
  companies?: string;
  time_limit_ms: number;
  memory_limit_mb: number;
}

interface CodingStats {
  total_solved: number;
  easy_solved: number;
  medium_solved: number;
  hard_solved: number;
  current_streak_days: number;
  longest_streak_days: number;
}

export default function CodingArenaCatalogPage() {
  const [problems, setProblems] = useState<Problem[]>([]);
  const [stats, setStats] = useState<CodingStats | null>(null);
  const [selectedDifficulty, setSelectedDifficulty] = useState<string>("ALL");
  const [selectedCategory, setSelectedCategory] = useState<string>("ALL");
  const [selectedCompany, setSelectedCompany] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(true);

  const difficulties = ["ALL", "Easy", "Medium", "Hard"];
  const categories = ["ALL", "Arrays", "Stacks", "Sliding Window", "Dynamic Programming", "Graphs"];
  const companies = ["ALL", "Google", "Amazon", "Microsoft", "Meta", "Apple"];

  useEffect(() => {
    async function fetchProblems() {
      try {
        setLoading(true);
        let url = "http://localhost:8000/api/v1/coding/problems";
        const params = new URLSearchParams();
        if (selectedDifficulty !== "ALL") params.append("difficulty", selectedDifficulty);
        if (selectedCategory !== "ALL") params.append("category", selectedCategory);
        if (selectedCompany !== "ALL") params.append("company", selectedCompany);
        if (searchQuery) params.append("search", searchQuery);
        if (params.toString()) url += `?${params.toString()}`;

        const res = await fetch(url);
        if (res.ok) {
          const data = await res.json();
          setProblems(data.problems || []);
        } else {
          loadFallbackProblems();
        }
      } catch (err) {
        loadFallbackProblems();
      } finally {
        setLoading(false);
      }
    }

    function loadFallbackProblems() {
      setProblems([
        {
          id: "1",
          slug: "two-sum",
          title: "Two Sum",
          difficulty: "Easy",
          category: "Arrays",
          tags: "Array, Hash Table",
          companies: "Google, Amazon, Microsoft, Meta",
          time_limit_ms: 2000,
          memory_limit_mb: 128
        },
        {
          id: "2",
          slug: "valid-parentheses",
          title: "Valid Parentheses",
          difficulty: "Easy",
          category: "Stacks",
          tags: "String, Stack",
          companies: "Amazon, Microsoft, Bloomberg",
          time_limit_ms: 2000,
          memory_limit_mb: 128
        },
        {
          id: "3",
          slug: "longest-substring-without-repeating-characters",
          title: "Longest Substring Without Repeating Characters",
          difficulty: "Medium",
          category: "Sliding Window",
          tags: "Hash Table, String, Sliding Window",
          companies: "Google, Meta, Apple",
          time_limit_ms: 2000,
          memory_limit_mb: 128
        }
      ]);
    }

    fetchProblems();
  }, [selectedDifficulty, selectedCategory, selectedCompany, searchQuery]);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
      {/* Header & Stats Banner (FEAT-074) */}
      <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-6 border-b border-obsidian-border pb-6">
        <div className="space-y-2">
          <div className="flex items-center gap-3">
            <Badge variant="cyber">Phase 5</Badge>
            <Badge variant="violet">Coding Arena & Sandbox</Badge>
            <span className="text-xs text-text-muted">FEAT-063..086 Live</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-text-primary tracking-tight">
            Algorithmic <span className="text-cyber">Coding Arena</span>
          </h1>
          <p className="text-text-secondary text-sm max-w-2xl">
            Solve curated interview problems, compile across multiple languages, test custom edge inputs,
            and submit solutions to the isolated verification sandbox.
          </p>
        </div>

        {/* Activity & Streak Metrics (FEAT-074) */}
        <div className="grid grid-cols-3 gap-3 w-full lg:w-auto">
          <div className="p-3 bg-obsidian-card rounded-xl border border-obsidian-border text-center">
            <div className="text-xs text-text-muted">Solved</div>
            <div className="text-lg font-bold text-cyber">3 / 1000+</div>
          </div>
          <div className="p-3 bg-obsidian-card rounded-xl border border-obsidian-border text-center">
            <div className="text-xs text-text-muted">Streak</div>
            <div className="text-lg font-bold text-violet-400">🔥 1 Day</div>
          </div>
          <div className="p-3 bg-obsidian-card rounded-xl border border-obsidian-border text-center">
            <div className="text-xs text-text-muted">Acceptance</div>
            <div className="text-lg font-bold text-text-primary">100%</div>
          </div>
        </div>
      </div>

      {/* Multi-Dimensional Filters (FEAT-065, FEAT-066) */}
      <div className="space-y-4 bg-obsidian-card/60 p-5 rounded-xl border border-obsidian-border">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          {/* Difficulty Filter */}
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs text-text-muted mr-1">Difficulty:</span>
            {difficulties.map((d) => (
              <button
                key={d}
                onClick={() => setSelectedDifficulty(d)}
                className={`px-3 py-1 rounded text-xs font-semibold transition-colors ${
                  selectedDifficulty === d
                    ? "bg-cyber text-obsidian"
                    : "bg-obsidian text-text-secondary hover:text-text-primary border border-obsidian-border"
                }`}
              >
                {d}
              </button>
            ))}
          </div>

          {/* Search Input */}
          <div className="w-full md:w-72">
            <input
              type="text"
              placeholder="Search problem title, tags..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-obsidian border border-obsidian-border rounded-lg px-3 py-2 text-xs text-text-primary placeholder-text-muted focus:outline-none focus:border-cyber"
            />
          </div>
        </div>

        {/* Categories & Company Filters (FEAT-066) */}
        <div className="flex flex-wrap gap-4 pt-2 border-t border-obsidian-border/50 text-xs">
          <div className="flex items-center gap-2">
            <span className="text-text-muted">Category:</span>
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="bg-obsidian border border-obsidian-border rounded px-2.5 py-1 text-xs text-text-primary focus:outline-none focus:border-cyber"
            >
              {categories.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-text-muted">Target Company (FEAT-066):</span>
            <select
              value={selectedCompany}
              onChange={(e) => setSelectedCompany(e.target.value)}
              className="bg-obsidian border border-obsidian-border rounded px-2.5 py-1 text-xs text-text-primary focus:outline-none focus:border-cyber"
            >
              {companies.map((co) => (
                <option key={co} value={co}>{co}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Problem Table / List (FEAT-065) */}
      <div className="overflow-x-auto border border-obsidian-border rounded-xl bg-obsidian-card/40">
        <table className="w-full text-left text-xs">
          <thead className="bg-obsidian/80 text-text-muted uppercase text-[10px] tracking-wider border-b border-obsidian-border">
            <tr>
              <th className="py-3 px-4">Status</th>
              <th className="py-3 px-4">Title</th>
              <th className="py-3 px-4">Difficulty</th>
              <th className="py-3 px-4">Category</th>
              <th className="py-3 px-4">Interview Tags</th>
              <th className="py-3 px-4 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-obsidian-border/50">
            {loading ? (
              <tr>
                <td colSpan={6} className="py-12 text-center text-text-muted">
                  Loading coding problems...
                </td>
              </tr>
            ) : problems.length === 0 ? (
              <tr>
                <td colSpan={6} className="py-12 text-center text-text-muted">
                  No coding problems found matching your filters.
                </td>
              </tr>
            ) : (
              problems.map((p) => (
                <tr key={p.id} className="hover:bg-obsidian/60 transition-colors">
                  <td className="py-3 px-4">
                    <span className="text-cyber">● Ready</span>
                  </td>
                  <td className="py-3 px-4 font-bold text-text-primary hover:text-cyber">
                    <Link href={`/coding/${p.slug}`}>
                      {p.title}
                    </Link>
                  </td>
                  <td className="py-3 px-4">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                      p.difficulty === "Easy" ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" :
                      p.difficulty === "Hard" ? "bg-rose-500/10 text-rose-400 border border-rose-500/20" :
                      "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                    }`}>
                      {p.difficulty}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-text-secondary">{p.category}</td>
                  <td className="py-3 px-4 text-text-muted font-mono text-[11px]">
                    {p.tags || "General DSA"}
                  </td>
                  <td className="py-3 px-4 text-right">
                    <Link href={`/coding/${p.slug}`}>
                      <Button variant="outline" size="sm">
                        Solve ↗
                      </Button>
                    </Link>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
