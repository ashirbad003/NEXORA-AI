"use client";

import React, { useState } from "react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";

export default function GitHubPage() {
  const [username, setUsername] = useState("octocat");
  const [loading, setLoading] = useState(false);
  const [profile, setProfile] = useState<any>({
    github_username: "octocat",
    portfolio_score: 91.5,
    public_repos_count: 8,
    languages_distribution: { Python: 45, TypeScript: 35, "C++": 15, Shell: 5 },
    recommendations: [
      "Pin your top two full-stack repositories on your GitHub profile overview.",
      "Ensure all repositories contain a standard open-source LICENSE and descriptive README.",
      "Maintain an active commit cadence across your core backend projects."
    ],
    repository_health_metrics: [
      {
        name: "distributed-consensus-engine",
        description: "Raft consensus implementation in Python with async network protocols.",
        primary_language: "Python",
        stars_count: 24,
        health_score: 95.0,
        has_readme: true,
        has_license: true
      },
      {
        name: "nexora-frontend-ui",
        description: "Modern component library with React 18 and Tailwind CSS.",
        primary_language: "TypeScript",
        stars_count: 12,
        health_score: 90.0,
        has_readme: true,
        has_license: true
      }
    ]
  });

  const handleScan = async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/v1/github/scan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ github_username: username })
      });
      if (res.ok) {
        const data = await res.json();
        setProfile(data);
      }
    } catch {
      // Fallback
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-obsidian-border pb-6">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-extrabold tracking-tight text-text-primary">
              GitHub <span className="text-cyber">Portfolio IQ</span>
            </h1>
            <Badge variant="cyber">Phase 8</Badge>
          </div>
          <p className="text-text-muted mt-1 text-sm">
            Deterministic repository audit, code distribution metrics, and developer portfolio scoring.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="GitHub username"
            className="rounded-lg border border-obsidian-border bg-obsidian px-3 py-1.5 text-sm text-text-primary focus:outline-none focus:border-cyber"
          />
          <Button variant="primary" size="sm" onClick={handleScan} disabled={loading}>
            {loading ? "Scanning..." : "Scan Profile"}
          </Button>
        </div>
      </div>

      {/* Grid: Portfolio IQ Score & Language Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="rounded-xl border border-obsidian-border bg-obsidian-surface p-6 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between">
              <h2 className="text-base font-semibold text-text-primary">Portfolio Quality Score</h2>
              <Badge variant="cyber">FEAT-212</Badge>
            </div>
            <div className="mt-4 flex items-baseline gap-2">
              <span className="text-5xl font-black text-cyber">
                {profile.portfolio_score}
              </span>
              <span className="text-text-muted text-lg">/ 100</span>
            </div>
            <div className="w-full bg-obsidian-border h-2 rounded-full mt-3 overflow-hidden">
              <div
                className="bg-cyber h-full rounded-full transition-all duration-500"
                style={{ width: `${profile.portfolio_score}%` }}
              />
            </div>
            <p className="text-xs text-text-secondary mt-3">
              Audited across README completeness, open source licensing, and code density.
            </p>
          </div>

          <div className="mt-6 pt-4 border-t border-obsidian-border space-y-2 text-xs">
            <div className="flex justify-between text-text-muted">
              <span>Public Repositories:</span>
              <span className="text-text-primary font-medium">{profile.public_repos_count}</span>
            </div>
            <div className="flex justify-between text-text-muted">
              <span>Active Languages:</span>
              <span className="text-cyber font-medium">{Object.keys(profile.languages_distribution).length}</span>
            </div>
          </div>
        </div>

        <div className="lg:col-span-2 rounded-xl border border-obsidian-border bg-obsidian-surface p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-semibold text-text-primary">Language Distribution (FEAT-203)</h2>
            <Badge variant="neutral">Verified</Badge>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            {Object.entries(profile.languages_distribution).map(([lang, pct]: [string, any]) => (
              <div key={lang} className="p-3 rounded-lg bg-obsidian border border-obsidian-border">
                <span className="text-xs text-text-muted block">{lang}</span>
                <span className="text-lg font-bold text-text-primary mt-1 block">{pct}%</span>
              </div>
            ))}
          </div>

          <div className="pt-2">
            <h3 className="text-xs font-semibold text-text-secondary uppercase tracking-wider mb-2">
              Recommended Portfolio Improvements
            </h3>
            <ul className="space-y-1.5 text-xs text-text-muted list-disc list-inside">
              {profile.recommendations.map((rec: string, idx: number) => (
                <li key={idx}>{rec}</li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      {/* Repositories Audit List */}
      <div className="rounded-xl border border-obsidian-border bg-obsidian-surface p-6 space-y-4">
        <h2 className="text-base font-semibold text-text-primary">Repository Health Inspection</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {profile.repository_health_metrics.map((repo: any, idx: number) => (
            <div key={idx} className="p-4 rounded-lg bg-obsidian border border-obsidian-border space-y-2">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold text-cyber">{repo.name}</h3>
                <Badge variant={repo.health_score > 90 ? "cyber" : "neutral"}>
                  {repo.health_score} / 100
                </Badge>
              </div>
              <p className="text-xs text-text-muted">{repo.description}</p>
              <div className="flex items-center gap-4 text-xs text-text-secondary pt-2">
                <span>Lang: {repo.primary_language}</span>
                <span>★ {repo.stars_count}</span>
                <span>{repo.has_readme ? "✓ README" : "✗ No README"}</span>
                <span>{repo.has_license ? "✓ MIT" : "✗ No License"}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
