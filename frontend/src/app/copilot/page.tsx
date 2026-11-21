"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";

interface WeekMilestone {
  week_number: number;
  title: string;
  focus_area: string;
  key_topics: string[];
  target_problems_count: number;
  status: string;
}

interface RoadmapData {
  id: string;
  target_role: string;
  duration_weeks: number;
  weeks: WeekMilestone[];
  milestone_badges: string[];
  readiness_index_target: number;
}

interface SprintTask {
  id: string;
  title: string;
  category: string;
  estimated_minutes: number;
  is_completed: boolean;
  date_assigned: string;
}

interface InsightsData {
  readiness: {
    readiness_index: number;
    readiness_tier: string;
    breakdown: {
      curriculum_score: number;
      coding_score: number;
      consistency_score: number;
    };
    recommendation: string;
  };
  skill_gap: {
    target_role: string;
    match_score_pct: number;
    gap_score_pct: number;
    matched_skills: string[];
    missing_skills: { skill: string; priority: string }[];
  };
  salary_insights: {
    india_range_lpa: string;
    tier1_median_lpa: string;
    global_range_usd: string;
    disclaimer: string;
  };
  campus_eligibility: {
    is_eligible: boolean;
    criteria: string;
    current_cgpa: number;
    status: string;
  };
  internship_readiness_pct: number;
  fatigue_warning: {
    detected: boolean;
    message: string;
  };
  project_recommendations: { title: string; tags: string[]; difficulty: string }[];
  interview_countdown: { target_event: string; days_remaining: number; readiness_target_date: string };
  certifications: { name: string; provider: string; importance: string }[];
}

interface ChatMessage {
  id?: string;
  role: "user" | "assistant";
  content: string;
  confidence_score?: number;
  explainability_rationale?: string;
}

export default function CareerCopilotPage() {
  const [activeTab, setActiveTab] = useState<"roadmap" | "sprints" | "mentor" | "insights">("roadmap");
  const [roadmap, setRoadmap] = useState<RoadmapData | null>(null);
  const [sprints, setSprints] = useState<SprintTask[]>([]);
  const [insights, setInsights] = useState<InsightsData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  // Chat State
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "assistant",
      content: "Hello! I am your NEXORA AI Career Copilot. Ask me anything about your 90-day placement roadmap, technical DSA strategies, or interview preparation.",
      confidence_score: 1.0,
      explainability_rationale: "Default onboarding mentor prompt."
    }
  ]);
  const [inputMsg, setInputMsg] = useState("");
  const [chatLoading, setChatLoading] = useState(false);
  const [persona, setPersona] = useState("friendly_mentor");

  useEffect(() => {
    fetchInitialData();
  }, []);

  const fetchInitialData = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem("access_token");
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (token) headers["Authorization"] = `Bearer ${token}`;

      // 1. Fetch Roadmap
      const rRes = await fetch("http://127.0.0.1:8000/api/v1/copilot/roadmap", { headers });
      if (rRes.ok) {
        const rData = await rRes.json();
        setRoadmap(rData);
      }

      // 2. Fetch Sprints
      const sRes = await fetch("http://127.0.0.1:8000/api/v1/copilot/sprints/today", { headers });
      if (sRes.ok) {
        const sData = await sRes.json();
        setSprints(sData);
      }

      // 3. Fetch Insights
      const iRes = await fetch("http://127.0.0.1:8000/api/v1/copilot/insights", { headers });
      if (iRes.ok) {
        const iData = await iRes.json();
        setInsights(iData);
      }
    } catch (err) {
      console.error("Failed to fetch copilot data:", err);
    } finally {
      setLoading(false);
    }
  };

  const toggleTask = async (taskId: string, currentStatus: boolean) => {
    try {
      const token = localStorage.getItem("access_token");
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (token) headers["Authorization"] = `Bearer ${token}`;

      const res = await fetch(`http://127.0.0.1:8000/api/v1/copilot/sprints/${taskId}`, {
        method: "PATCH",
        headers,
        body: JSON.stringify({ is_completed: !currentStatus })
      });
      if (res.ok) {
        setSprints((prev) =>
          prev.map((t) => (t.id === taskId ? { ...t, is_completed: !currentStatus } : t))
        );
      }
    } catch (err) {
      console.error("Failed to toggle sprint task:", err);
    }
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputMsg.trim() || chatLoading) return;

    const userText = inputMsg.trim();
    setInputMsg("");
    setMessages((prev) => [...prev, { role: "user", content: userText }]);
    setChatLoading(true);

    try {
      const token = localStorage.getItem("access_token");
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (token) headers["Authorization"] = `Bearer ${token}`;

      const res = await fetch("http://127.0.0.1:8000/api/v1/copilot/chat", {
        method: "POST",
        headers,
        body: JSON.stringify({ message: userText, persona })
      });

      if (res.ok) {
        const data = await res.json();
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: data.content,
            confidence_score: data.confidence_score,
            explainability_rationale: data.explainability_rationale
          }
        ]);
      } else {
        const errData = await res.json();
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: `⚠️ ${errData.detail || "Unable to complete request."}`
          }
        ]);
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "⚠️ Network connection interrupted. Please try again."
        }
      ]);
    } finally {
      setChatLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#060913] text-slate-100 flex flex-col font-sans">
      {/* Header */}
      <header className="border-b border-slate-800 bg-[#060913]/90 backdrop-blur sticky top-0 z-20 px-6 py-4 flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <span className="bg-[#a3e635]/10 text-[#a3e635] border border-[#a3e635]/30 text-xs px-2.5 py-1 rounded-full font-semibold uppercase tracking-wider">
              Phase 6 Active
            </span>
            <h1 className="text-xl md:text-2xl font-bold tracking-tight text-white flex items-center gap-2">
              AI Career Copilot <span className="text-[#a3e635]">.</span>
            </h1>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Unified AI Brain & 90-Day Placement Intelligence
          </p>
        </div>

        {/* Tab Controls */}
        <nav className="flex items-center gap-1 bg-slate-900/80 p-1 rounded-lg border border-slate-800 text-xs font-medium">
          <button
            onClick={() => setActiveTab("roadmap")}
            className={`px-3 py-1.5 rounded-md transition-all ${
              activeTab === "roadmap"
                ? "bg-[#a3e635] text-[#060913] font-bold shadow"
                : "text-slate-400 hover:text-white"
            }`}
          >
            Roadmap (90D)
          </button>
          <button
            onClick={() => setActiveTab("sprints")}
            className={`px-3 py-1.5 rounded-md transition-all ${
              activeTab === "sprints"
                ? "bg-[#a3e635] text-[#060913] font-bold shadow"
                : "text-slate-400 hover:text-white"
            }`}
          >
            Daily Sprints
          </button>
          <button
            onClick={() => setActiveTab("mentor")}
            className={`px-3 py-1.5 rounded-md transition-all ${
              activeTab === "mentor"
                ? "bg-[#a3e635] text-[#060913] font-bold shadow"
                : "text-slate-400 hover:text-white"
            }`}
          >
            AI Mentor Q&A
          </button>
          <button
            onClick={() => setActiveTab("insights")}
            className={`px-3 py-1.5 rounded-md transition-all ${
              activeTab === "insights"
                ? "bg-[#a3e635] text-[#060913] font-bold shadow"
                : "text-slate-400 hover:text-white"
            }`}
          >
            Readiness & Insights
          </button>
        </nav>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-6 md:p-8">
        {loading ? (
          <div className="flex flex-col items-center justify-center min-h-[400px]">
            <div className="w-10 h-10 border-4 border-[#a3e635] border-t-transparent rounded-full animate-spin"></div>
            <p className="mt-4 text-sm text-slate-400">Loading AI Career Copilot Intelligence...</p>
          </div>
        ) : (
          <>
            {/* TAB 1: 90-DAY PLACEMENT ROADMAP */}
            {activeTab === "roadmap" && (
              <div className="space-y-6">
                <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 flex flex-wrap items-center justify-between gap-4">
                  <div>
                    <h2 className="text-lg font-bold text-white">
                      Target Role: <span className="text-[#a3e635]">{roadmap?.target_role || "Software Development Engineer"}</span>
                    </h2>
                    <p className="text-xs text-slate-400 mt-1">
                      12-Week Strategic Timeline curated for Tier-1 Product Companies.
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    {roadmap?.milestone_badges?.map((badge, idx) => (
                      <span
                        key={idx}
                        className="bg-purple-950/40 text-purple-300 border border-purple-800/50 text-xs px-2.5 py-1 rounded-full font-medium"
                      >
                        🏅 {badge}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {roadmap?.weeks?.map((week) => (
                    <div
                      key={week.week_number}
                      className="bg-slate-900/40 border border-slate-800 hover:border-slate-700 rounded-xl p-5 flex flex-col justify-between transition-all"
                    >
                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-xs font-semibold px-2 py-0.5 rounded bg-slate-800 text-[#a3e635]">
                            Week {week.week_number}
                          </span>
                          <span className="text-[10px] text-slate-400 uppercase tracking-wider">
                            {week.target_problems_count} Problems
                          </span>
                        </div>
                        <h3 className="text-sm font-bold text-white mb-1">{week.title}</h3>
                        <p className="text-xs text-slate-300 mb-3">{week.focus_area}</p>
                      </div>

                      <div>
                        <div className="text-[11px] text-slate-400 mb-1 font-medium">Core Concepts:</div>
                        <div className="flex flex-wrap gap-1">
                          {week.key_topics?.map((topic, i) => (
                            <span
                              key={i}
                              className="text-[10px] bg-slate-800/70 text-slate-300 px-2 py-0.5 rounded border border-slate-700"
                            >
                              {topic}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* TAB 2: DAILY SPRINTS */}
            {activeTab === "sprints" && (
              <div className="max-w-3xl mx-auto space-y-6">
                <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6">
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <h2 className="text-lg font-bold text-white">Today&apos;s Actionable Sprints</h2>
                      <p className="text-xs text-slate-400">
                        Bite-sized high-yield milestones to maintain placement consistency.
                      </p>
                    </div>
                    <div className="text-xs font-medium bg-[#a3e635]/10 text-[#a3e635] px-3 py-1 rounded-full border border-[#a3e635]/20">
                      {sprints.filter((s) => s.is_completed).length} / {sprints.length} Completed
                    </div>
                  </div>

                  <div className="space-y-3">
                    {sprints.map((task) => (
                      <div
                        key={task.id}
                        onClick={() => toggleTask(task.id, task.is_completed)}
                        className={`p-4 rounded-lg border transition-all cursor-pointer flex items-center justify-between ${
                          task.is_completed
                            ? "bg-slate-950/40 border-slate-800/50 opacity-60 line-through"
                            : "bg-slate-900/40 border-slate-800 hover:border-slate-700"
                        }`}
                      >
                        <div className="flex items-center gap-3">
                          <input
                            type="checkbox"
                            checked={task.is_completed}
                            onChange={() => {}}
                            className="w-4 h-4 accent-[#a3e635] cursor-pointer"
                          />
                          <div>
                            <span className="text-sm font-medium text-white">{task.title}</span>
                            <div className="text-[11px] text-slate-400 capitalize mt-0.5">
                              {task.category} • ~{task.estimated_minutes} mins
                            </div>
                          </div>
                        </div>
                        <span className="text-xs text-slate-400">
                          {task.is_completed ? "✅ Done" : "⏳ Pending"}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* TAB 3: AI MENTOR DIRECT Q&A */}
            {activeTab === "mentor" && (
              <div className="max-w-4xl mx-auto flex flex-col h-[650px] bg-slate-900/40 border border-slate-800 rounded-xl overflow-hidden">
                {/* Mentor Header */}
                <div className="p-4 border-b border-slate-800 bg-slate-900/80 flex items-center justify-between">
                  <div>
                    <h2 className="text-sm font-bold text-white flex items-center gap-2">
                      <span>🤖</span> NEXORA AI Mentor
                    </h2>
                    <p className="text-[11px] text-slate-400">
                      Context-Aware Placement Guidance with Guardrails & Latency Protection
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <label className="text-xs text-slate-400 font-medium">Persona:</label>
                    <select
                      value={persona}
                      onChange={(e) => setPersona(e.target.value)}
                      className="bg-slate-800 text-xs text-white border border-slate-700 rounded px-2.5 py-1 focus:outline-none focus:border-[#a3e635]"
                    >
                      <option value="friendly_mentor">Friendly Mentor</option>
                      <option value="strict_interviewer">Strict Interviewer</option>
                      <option value="technical_architect">Technical Architect</option>
                    </select>
                  </div>
                </div>

                {/* Messages Body */}
                <div className="flex-1 overflow-y-auto p-4 space-y-4">
                  {messages.map((m, idx) => (
                    <div
                      key={idx}
                      className={`flex flex-col ${
                        m.role === "user" ? "items-end" : "items-start"
                      }`}
                    >
                      <div
                        className={`max-w-[85%] rounded-xl px-4 py-3 text-xs leading-relaxed whitespace-pre-wrap ${
                          m.role === "user"
                            ? "bg-[#a3e635] text-[#060913] font-medium"
                            : "bg-slate-800/80 text-slate-100 border border-slate-700/60"
                        }`}
                      >
                        {m.content}
                      </div>
                      {m.role === "assistant" && m.confidence_score && (
                        <div className="flex items-center gap-3 text-[10px] text-slate-500 mt-1 px-1">
                          <span>Confidence: {(m.confidence_score * 100).toFixed(0)}%</span>
                          {m.explainability_rationale && (
                            <span className="italic truncate max-w-sm">
                              💡 {m.explainability_rationale}
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  ))}
                  {chatLoading && (
                    <div className="flex items-center gap-2 text-xs text-[#a3e635] p-2">
                      <div className="w-3 h-3 border-2 border-[#a3e635] border-t-transparent rounded-full animate-spin"></div>
                      <span>NEXORA AI Brain is synthesizing response...</span>
                    </div>
                  )}
                </div>

                {/* Input Bar */}
                <form
                  onSubmit={handleSendMessage}
                  className="p-3 border-t border-slate-800 bg-slate-900/90 flex items-center gap-2"
                >
                  <input
                    type="text"
                    value={inputMsg}
                    onChange={(e) => setInputMsg(e.target.value)}
                    placeholder="Ask about dynamic programming, system design, or interview behavioral tactics..."
                    className="flex-1 bg-slate-800 border border-slate-700 rounded-lg px-4 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-[#a3e635]"
                  />
                  <button
                    type="submit"
                    disabled={chatLoading}
                    className="bg-[#a3e635] text-[#060913] font-bold text-xs px-5 py-2.5 rounded-lg hover:bg-[#8fd128] transition disabled:opacity-50"
                  >
                    Send
                  </button>
                </form>
              </div>
            )}

            {/* TAB 4: READINESS & INSIGHTS */}
            {activeTab === "insights" && insights && (
              <div className="space-y-6">
                {/* Top Metrics Row */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {/* Readiness Index */}
                  <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5">
                    <span className="text-[11px] text-slate-400 font-medium uppercase tracking-wider">
                      Career Readiness Index (FEAT-016)
                    </span>
                    <div className="flex items-baseline gap-2 mt-2">
                      <span className="text-3xl font-extrabold text-[#a3e635]">
                        {insights.readiness.readiness_index}
                      </span>
                      <span className="text-xs text-slate-400">/ 100</span>
                    </div>
                    <p className="text-xs font-semibold text-purple-400 mt-1">
                      {insights.readiness.readiness_tier}
                    </p>
                    <p className="text-[11px] text-slate-400 mt-2">
                      {insights.readiness.recommendation}
                    </p>
                  </div>

                  {/* Salary Insights */}
                  <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5">
                    <span className="text-[11px] text-slate-400 font-medium uppercase tracking-wider">
                      Salary Benchmark (FEAT-036)
                    </span>
                    <div className="text-xl font-bold text-white mt-2">
                      {insights.salary_insights.india_range_lpa}
                    </div>
                    <div className="text-xs text-slate-400 mt-1">
                      Tier-1 Median: {insights.salary_insights.tier1_median_lpa}
                    </div>
                    <p className="text-[10px] text-slate-500 mt-3 italic">
                      {insights.salary_insights.disclaimer}
                    </p>
                  </div>

                  {/* Campus Eligibility */}
                  <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5">
                    <span className="text-[11px] text-slate-400 font-medium uppercase tracking-wider">
                      Campus Eligibility (FEAT-038)
                    </span>
                    <div className="text-base font-bold text-emerald-400 mt-2">
                      {insights.campus_eligibility.status}
                    </div>
                    <p className="text-xs text-slate-400 mt-1">
                      Criteria: {insights.campus_eligibility.criteria}
                    </p>
                    <div className="text-xs text-slate-300 mt-2">
                      Current CGPA: <span className="font-semibold">{insights.campus_eligibility.current_cgpa}</span>
                    </div>
                  </div>
                </div>

                {/* Skill Gap Analysis */}
                <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6">
                  <h3 className="text-sm font-bold text-white mb-2">
                    Skill Gap Vector Matcher (FEAT-012, FEAT-025)
                  </h3>
                  <div className="flex items-center gap-4 mb-4">
                    <div className="text-xs text-slate-300">
                      Match: <span className="font-bold text-[#a3e635]">{insights.skill_gap.match_score_pct}%</span>
                    </div>
                    <div className="text-xs text-slate-300">
                      Gap: <span className="font-bold text-rose-400">{insights.skill_gap.gap_score_pct}%</span>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <div className="text-xs font-semibold text-emerald-400 mb-2">Mastered Skills:</div>
                      <div className="flex flex-wrap gap-1.5">
                        {insights.skill_gap.matched_skills.map((s, idx) => (
                          <span
                            key={idx}
                            className="text-xs bg-emerald-950/40 text-emerald-300 border border-emerald-800 px-2.5 py-1 rounded"
                          >
                            ✓ {s}
                          </span>
                        ))}
                      </div>
                    </div>

                    <div>
                      <div className="text-xs font-semibold text-rose-400 mb-2">Target Role Missing Skills:</div>
                      <div className="flex flex-wrap gap-1.5">
                        {insights.skill_gap.missing_skills.map((ms, idx) => (
                          <span
                            key={idx}
                            className="text-xs bg-rose-950/40 text-rose-300 border border-rose-800 px-2.5 py-1 rounded"
                          >
                            ! {ms.skill} ({ms.priority})
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}
