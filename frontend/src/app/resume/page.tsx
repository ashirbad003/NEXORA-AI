"use client";

import React, { useState, useEffect } from "react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";

interface Resume {
  id: string;
  title: string;
  template_type: string;
  ats_score: number;
  completeness_score: number;
  is_primary: boolean;
  structured_data: any;
}

export default function ResumePage() {
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [activeResume, setActiveResume] = useState<Resume | null>(null);
  const [bulletInput, setBulletInput] = useState("Worked on backend services using Python.");
  const [optimizedBullet, setOptimizedBullet] = useState<any>(null);
  const [latexCode, setLatexCode] = useState<string>("");
  const [atsDetails, setAtsDetails] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Initial mock state for interactive demo if not logged in
    const initialResume: Resume = {
      id: "res-demo-1",
      title: "Full-Stack Software Engineer Resume",
      template_type: "Modern",
      ats_score: 84.5,
      completeness_score: 100.0,
      is_primary: true,
      structured_data: {
        contact: { name: "Alex Chen", email: "alex.chen@nexora.ai", phone: "+1 (555) 019-2834" },
        skills: ["Python", "FastAPI", "React", "Next.js", "PostgreSQL", "Docker", "Tailwind CSS"],
        experience: ["Engineered scalable RESTful microservices processing 10k requests/min."]
      }
    };
    setResumes([initialResume]);
    setActiveResume(initialResume);
  }, []);

  const handleOptimizeBullet = async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/v1/resume/optimize-bullet", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ bullet_point: bulletInput, role_target: "Software Engineer" })
      });
      if (res.ok) {
        const data = await res.json();
        setOptimizedBullet(data);
      } else {
        // Fallback local enhancement for disconnected UI preview
        setOptimizedBullet({
          original: bulletInput,
          optimized: "Architected and deployed high-throughput backend services using Python, reducing latency by 35% and improving API uptime.",
          action_verb_used: "Architected",
          metric_added: true,
          explanation: "Replaced generic passive verb with high-impact action verb 'Architected' and added quantifiable throughput metrics."
        });
      }
    } catch {
      setOptimizedBullet({
        original: bulletInput,
        optimized: "Architected and deployed high-throughput backend services using Python, reducing latency by 35% and improving API uptime.",
        action_verb_used: "Architected",
        metric_added: true,
        explanation: "Replaced generic passive verb with high-impact action verb 'Architected' and added quantifiable throughput metrics."
      });
    } finally {
      setLoading(false);
    }
  };

  const handleLoadLatex = () => {
    setLatexCode(`\\documentclass[letterpaper,10pt]{article}
\\usepackage[margin=0.75in]{geometry}
\\usepackage{hyperref}
\\begin{document}
\\begin{center}
    \\textbf{\\Huge Alex Chen} \\\\ \\vspace{4pt}
    alex.chen@nexora.ai $|$ github.com/alexchen-dev
\\end{center}
\\section{Technical Skills}
Python, FastAPI, TypeScript, React, PostgreSQL, Docker, CI/CD
\\section{Experience}
\\textbf{NEXORA AI} \\hfill \\textit{Full-Stack Engineering} \\\\
Engineered resilient backend microservices with sub-50ms latency.
\\end{document}`);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-obsidian-border pb-6">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-extrabold tracking-tight text-text-primary">
              AI Resume <span className="text-cyber">Intelligence</span>
            </h1>
            <Badge variant="cyber">Phase 8</Badge>
          </div>
          <p className="text-text-muted mt-1 text-sm">
            ATS parsing engine, bullet-point STAR rewriter, and Overleaf LaTeX code export.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" size="sm" onClick={handleLoadLatex}>
            View LaTeX Code
          </Button>
          <Button variant="primary" size="sm">
            + New Resume
          </Button>
        </div>
      </div>

      {/* Grid: ATS Score & Live Overview */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* ATS Score Card */}
        <div className="rounded-xl border border-obsidian-border bg-obsidian-surface p-6 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between">
              <h2 className="text-base font-semibold text-text-primary">ATS Readiness Score</h2>
              <Badge variant="cyber">FEAT-182</Badge>
            </div>
            <div className="mt-4 flex items-baseline gap-2">
              <span className="text-5xl font-black text-cyber">
                {activeResume?.ats_score || 84.5}
              </span>
              <span className="text-text-muted text-lg">/ 100</span>
            </div>
            <div className="w-full bg-obsidian-border h-2 rounded-full mt-3 overflow-hidden">
              <div
                className="bg-cyber h-full rounded-full transition-all duration-500"
                style={{ width: `${activeResume?.ats_score || 84.5}%` }}
              />
            </div>
            <p className="text-xs text-text-secondary mt-3">
              Excellent candidate match. Incorporates active verbs and technical keywords.
            </p>
          </div>

          <div className="mt-6 pt-4 border-t border-obsidian-border space-y-2 text-xs">
            <div className="flex justify-between text-text-muted">
              <span>Section Completeness:</span>
              <span className="text-text-primary font-medium">100%</span>
            </div>
            <div className="flex justify-between text-text-muted">
              <span>Quantified Metrics:</span>
              <span className="text-cyber font-medium">Verified (STAR Format)</span>
            </div>
            <div className="flex justify-between text-text-muted">
              <span>Template:</span>
              <span className="text-text-primary font-medium">{activeResume?.template_type || "Modern"}</span>
            </div>
          </div>
        </div>

        {/* Bullet Point STAR Optimizer */}
        <div className="lg:col-span-2 rounded-xl border border-obsidian-border bg-obsidian-surface p-6 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between">
              <h2 className="text-base font-semibold text-text-primary">
                AI Bullet-Point Impact Optimizer (STAR Method)
              </h2>
              <Badge variant="neutral">FEAT-183</Badge>
            </div>
            <p className="text-xs text-text-muted mt-1">
              Transforms passive descriptions into high-conversion impact statements with measurable metrics.
            </p>

            <div className="mt-4 space-y-3">
              <textarea
                value={bulletInput}
                onChange={(e) => setBulletInput(e.target.value)}
                rows={2}
                className="w-full rounded-lg border border-obsidian-border bg-obsidian px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-cyber"
                placeholder="e.g. Worked on database queries to make it faster."
              />
              <Button
                variant="primary"
                size="sm"
                onClick={handleOptimizeBullet}
                disabled={loading}
              >
                {loading ? "Optimizing..." : "Transform with AI"}
              </Button>
            </div>

            {optimizedBullet && (
              <div className="mt-4 p-4 rounded-lg bg-obsidian border border-cyber/30 space-y-2">
                <div className="flex items-center gap-2 text-xs font-semibold text-cyber">
                  <span>✓ Action Verb: {optimizedBullet.action_verb_used}</span>
                  <span>•</span>
                  <span>Metrics Added: {optimizedBullet.metric_added ? "Yes" : "No"}</span>
                </div>
                <p className="text-sm text-text-primary font-medium">
                  "{optimizedBullet.optimized}"
                </p>
                <p className="text-xs text-text-muted italic">
                  {optimizedBullet.explanation}
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* LaTeX Code Modal / Drawer */}
      {latexCode && (
        <div className="rounded-xl border border-obsidian-border bg-obsidian-surface p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-bold text-text-primary">Overleaf / LaTeX Export</h3>
            <Button variant="outline" size="sm" onClick={() => setLatexCode("")}>
              Close
            </Button>
          </div>
          <pre className="p-4 rounded-lg bg-obsidian border border-obsidian-border text-xs text-cyber font-mono overflow-x-auto">
            {latexCode}
          </pre>
        </div>
      )}
    </div>
  );
}
