"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";

interface Module {
  id: string;
  slug: string;
  title: string;
  category: string;
  summary: string;
  estimated_read_time_minutes: number;
  difficulty_level: string;
  order_index: number;
}

interface CaseStudy {
  id: string;
  system_name: string;
  title: string;
  scale_metrics: string;
  architecture_overview: string;
  dsa_patterns_used: string[];
  deep_dive_markdown: string;
}

interface ChangelogEntry {
  version: string;
  released_at: string;
  changes: string[];
  affected_topics: string[];
}

export default function LearningHubPage() {
  const [modules, setModules] = useState<Module[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>("ALL");
  const [selectedDifficulty, setSelectedDifficulty] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(true);
  const [activeTab, setActiveTab] = useState<"concepts" | "casestudies" | "changelog">("concepts");

  // FEAT-137: Case Studies
  const [caseStudies, setCaseStudies] = useState<CaseStudy[]>([]);
  // FEAT-144: Changelog
  const [changelog, setChangelog] = useState<ChangelogEntry[]>([]);

  const categories = ["ALL", "DSA", "OS", "DBMS", "CN", "OOPS"];
  const difficulties = ["ALL", "Easy", "Medium", "Hard"];

  useEffect(() => {
    async function fetchModules() {
      try {
        setLoading(true);
        let url = "http://localhost:8000/api/v1/learn/modules";
        const params = new URLSearchParams();
        if (selectedCategory !== "ALL") params.append("category", selectedCategory);
        if (selectedDifficulty !== "ALL") params.append("difficulty", selectedDifficulty);
        if (searchQuery) params.append("search", searchQuery);
        if (params.toString()) url += `?${params.toString()}`;

        const res = await fetch(url);
        if (res.ok) {
          const data = await res.json();
          setModules(data.modules || []);
          // FEAT-134: Cache to LocalStorage for Offline Mode
          try {
            localStorage.setItem("nexora_cached_modules", JSON.stringify(data.modules || []));
          } catch (e) {}
        } else {
          loadOfflineFallback();
        }
      } catch (err) {
        loadOfflineFallback();
      } finally {
        setLoading(false);
      }
    }

    function loadOfflineFallback() {
      // FEAT-134: Offline Fallback from LocalStorage or static
      try {
        const cached = localStorage.getItem("nexora_cached_modules");
        if (cached) {
          setModules(JSON.parse(cached));
          return;
        }
      } catch (e) {}
      setModules([
        {
          id: "1",
          slug: "arrays-and-hashing",
          title: "Arrays & Dynamic Hashing",
          category: "DSA",
          summary: "Core array operations, amortized resizing, and hash map collision resolution strategies.",
          estimated_read_time_minutes: 8,
          difficulty_level: "Easy",
          order_index: 1
        },
        {
          id: "2",
          slug: "graph-traversal-bfs-dfs",
          title: "Graph Traversal: BFS & DFS Foundations",
          category: "DSA",
          summary: "Queue-based level-order search and recursive backtracking traversal across graphs.",
          estimated_read_time_minutes: 12,
          difficulty_level: "Medium",
          order_index: 2
        },
        {
          id: "3",
          slug: "operating-systems-concurrency",
          title: "OS: Concurrency, Semaphores & Mutexes",
          category: "OS",
          summary: "Process synchronization, critical section problems, and deadlock conditions.",
          estimated_read_time_minutes: 15,
          difficulty_level: "Hard",
          order_index: 3
        },
        {
          id: "4",
          slug: "dbms-indexing-b-trees",
          title: "DBMS: B+ Tree Indexing & Query Plans",
          category: "DBMS",
          summary: "Disk-based data structures, balanced search trees, and execution plan cost estimation.",
          estimated_read_time_minutes: 14,
          difficulty_level: "Medium",
          order_index: 4
        }
      ]);
    }

    fetchModules();
  }, [selectedCategory, selectedDifficulty, searchQuery]);

  // Load Case studies & changelog
  useEffect(() => {
    async function loadAuxiliaryData() {
      try {
        const csRes = await fetch("http://localhost:8000/api/v1/learn/case-studies");
        if (csRes.ok) {
          const csData = await csRes.json();
          setCaseStudies(csData);
        }
        const clRes = await fetch("http://localhost:8000/api/v1/learn/changelog");
        if (clRes.ok) {
          const clData = await clRes.json();
          setChangelog(clData);
        }
      } catch (e) {}
    }
    loadAuxiliaryData();
  }, []);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
      {/* Header */}
      <div className="space-y-3">
        <div className="flex items-center gap-3">
          <Badge variant="cyber">Phase 4</Badge>
          <Badge variant="violet">Smart Learning Hub</Badge>
          <span className="text-xs text-text-muted">FEAT-123..144 Fully Integrated</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-extrabold text-text-primary tracking-tight">
          Computer Science & <span className="text-cyber">DSA Learning Hub</span>
        </h1>
        <p className="text-text-secondary max-w-3xl text-sm sm:text-base">
          Master foundational data structures, algorithmic paradigms, real-world distributed architectures, and systems engineering concepts with
          interactive visualizations, concept checkpoints, and multilingual guides.
        </p>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-obsidian-border gap-6">
        <button
          onClick={() => setActiveTab("concepts")}
          className={`pb-3 text-sm font-bold border-b-2 transition-colors ${
            activeTab === "concepts"
              ? "border-cyber text-cyber"
              : "border-transparent text-text-secondary hover:text-text-primary"
          }`}
        >
          Curriculum Concepts
        </button>
        <button
          onClick={() => setActiveTab("casestudies")}
          className={`pb-3 text-sm font-bold border-b-2 transition-colors ${
            activeTab === "casestudies"
              ? "border-cyber text-cyber"
              : "border-transparent text-text-secondary hover:text-text-primary"
          }`}
        >
          System Architectures (FEAT-137)
        </button>
        <button
          onClick={() => setActiveTab("changelog")}
          className={`pb-3 text-sm font-bold border-b-2 transition-colors ${
            activeTab === "changelog"
              ? "border-cyber text-cyber"
              : "border-transparent text-text-secondary hover:text-text-primary"
          }`}
        >
          Curriculum Versioning (FEAT-144)
        </button>
      </div>

      {activeTab === "concepts" && (
        <div className="space-y-8">
          {/* Multi-parameter Filter & Search Bar (FEAT-134 & FEAT-135) */}
          <div className="flex flex-col lg:flex-row gap-4 justify-between items-start lg:items-center border-b border-obsidian-border pb-6">
            <div className="flex flex-wrap items-center gap-4">
              {/* Category Filter */}
              <div className="flex flex-wrap gap-2 items-center">
                <span className="text-xs text-text-muted mr-1">Category:</span>
                {categories.map((cat) => (
                  <button
                    key={cat}
                    onClick={() => setSelectedCategory(cat)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
                      selectedCategory === cat
                        ? "bg-cyber text-obsidian"
                        : "bg-obsidian-card text-text-secondary hover:text-text-primary border border-obsidian-border"
                    }`}
                  >
                    {cat}
                  </button>
                ))}
              </div>

              {/* Difficulty Level Filter (FEAT-135) */}
              <div className="flex flex-wrap gap-2 items-center">
                <span className="text-xs text-text-muted mr-1">Difficulty:</span>
                {difficulties.map((diff) => (
                  <button
                    key={diff}
                    onClick={() => setSelectedDifficulty(diff)}
                    className={`px-2.5 py-1 rounded text-xs font-medium transition-colors ${
                      selectedDifficulty === diff
                        ? "bg-violet text-white"
                        : "bg-obsidian-card text-text-muted hover:text-text-primary border border-obsidian-border"
                    }`}
                  >
                    {diff}
                  </button>
                ))}
              </div>
            </div>

            {/* Topic Search Bar (FEAT-134) */}
            <div className="w-full lg:w-72">
              <input
                type="text"
                placeholder="Search topics, algorithms, systems..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-obsidian-card border border-obsidian-border rounded-lg px-3 py-2 text-sm text-text-primary placeholder-text-muted focus:outline-none focus:border-cyber"
              />
            </div>
          </div>

          {/* Modules Grid */}
          {loading ? (
            <div className="text-center py-16 text-text-muted">Loading curriculum concepts...</div>
          ) : modules.length === 0 ? (
            <div className="text-center py-16 text-text-muted">No concepts found matching your filters.</div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {modules.map((mod) => (
                <Card key={mod.id} className="flex flex-col justify-between hover:border-cyber transition-all group">
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <Badge variant={mod.category === "DSA" ? "cyber" : "violet"}>{mod.category}</Badge>
                      <div className="flex items-center gap-2">
                        <span className={`text-[10px] px-2 py-0.5 rounded font-bold uppercase ${
                          mod.difficulty_level === "Easy" ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" :
                          mod.difficulty_level === "Hard" ? "bg-rose-500/10 text-rose-400 border border-rose-500/20" :
                          "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                        }`}>
                          {mod.difficulty_level}
                        </span>
                        <span className="text-xs text-text-muted">{mod.estimated_read_time_minutes} min read</span>
                      </div>
                    </div>
                    <h3 className="font-bold text-lg text-text-primary group-hover:text-cyber transition-colors">
                      {mod.title}
                    </h3>
                    <p className="text-text-secondary text-sm line-clamp-3 leading-relaxed">
                      {mod.summary}
                    </p>
                  </div>

                  <div className="mt-6 pt-4 border-t border-obsidian-border/50 flex items-center justify-between">
                    <span className="text-xs font-mono text-cyber">Interactive Guide</span>
                    <Link href={`/learn/${mod.slug}`}>
                      <Button variant="outline" size="sm">
                        Study Concept →
                      </Button>
                    </Link>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}

      {/* FEAT-137: Real-World Architecture Case Studies */}
      {activeTab === "casestudies" && (
        <div className="space-y-6">
          <div className="border-b border-obsidian-border pb-4">
            <h2 className="text-xl font-bold text-text-primary">Production System Architectures</h2>
            <p className="text-xs text-text-muted">How Netflix, Uber, and WhatsApp apply DSA & distributed patterns at scale.</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {caseStudies.map((cs) => (
              <Card key={cs.id} className="p-6 space-y-4 border-obsidian-border hover:border-violet transition-colors">
                <div className="flex items-center justify-between">
                  <Badge variant="violet">{cs.system_name}</Badge>
                  <span className="text-[11px] font-mono text-cyber">{cs.scale_metrics.split("|")[0]}</span>
                </div>
                <h3 className="text-lg font-bold text-text-primary">{cs.title}</h3>
                <p className="text-xs text-text-secondary leading-relaxed">{cs.architecture_overview}</p>
                <div className="space-y-1.5 pt-2">
                  <span className="text-[10px] font-semibold text-text-muted uppercase tracking-wider">DSA Patterns Used:</span>
                  <div className="flex flex-wrap gap-1.5">
                    {cs.dsa_patterns_used.map((p, i) => (
                      <span key={i} className="text-[11px] px-2 py-0.5 rounded bg-obsidian border border-obsidian-border text-text-primary">
                        {p}
                      </span>
                    ))}
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* FEAT-144: Curriculum Versioning & Changelog */}
      {activeTab === "changelog" && (
        <div className="space-y-6 max-w-4xl">
          <div className="border-b border-obsidian-border pb-4">
            <h2 className="text-xl font-bold text-text-primary">Curriculum Version History</h2>
            <p className="text-xs text-text-muted">Audited release log and educational modifications.</p>
          </div>
          <div className="space-y-6">
            {changelog.map((entry, idx) => (
              <Card key={idx} className="p-6 space-y-3 border-obsidian-border">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-sm font-bold text-cyber">{entry.version}</span>
                  <span className="text-xs text-text-muted">{entry.released_at}</span>
                </div>
                <ul className="space-y-1.5 list-disc list-inside text-xs text-text-secondary leading-relaxed">
                  {entry.changes.map((c, i) => (
                    <li key={i}>{c}</li>
                  ))}
                </ul>
                <div className="pt-2 text-[11px] text-text-muted font-mono">
                  Topics touched: {entry.affected_topics.join(", ")}
                </div>
              </Card>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
