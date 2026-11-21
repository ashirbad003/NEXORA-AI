"use client";

import React, { useState } from "react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";

interface Job {
  id: string;
  company_name: string;
  role_title: string;
  opportunity_type: string;
  location: string;
  stipend_or_salary: string;
  description: string;
  required_skills: string[];
  match_score: number;
  is_on_campus: boolean;
}

interface Application {
  id: string;
  job_id: string;
  status: "Wishlist" | "Applied" | "Interview" | "Offer" | "Rejected";
  company_name: string;
  role_title: string;
  match_score: number;
}

const KANBAN_COLUMNS: Array<"Wishlist" | "Applied" | "Interview" | "Offer" | "Rejected"> = [
  "Wishlist", "Applied", "Interview", "Offer", "Rejected"
];

export default function JobsPage() {
  const [activeTab, setActiveTab] = useState<"board" | "kanban">("kanban");
  const [coldEmailModal, setColdEmailModal] = useState<any>(null);

  const [jobs] = useState<Job[]>([
    {
      id: "job-1",
      company_name: "Google",
      role_title: "Software Engineering Intern",
      opportunity_type: "Internship",
      location: "Bengaluru, India / Hybrid",
      stipend_or_salary: "₹1,25,000 / month",
      description: "Build scalable distributed infrastructure and cloud systems.",
      required_skills: ["Python", "C++", "Data Structures", "Algorithms", "System Design"],
      match_score: 92.0,
      is_on_campus: true
    },
    {
      id: "job-2",
      company_name: "Microsoft",
      role_title: "Full-Stack Software Engineer",
      opportunity_type: "Full-Time",
      location: "Hyderabad, India / Remote",
      stipend_or_salary: "₹24,00,000 / year",
      description: "Work on Azure AI tools and modern web applications.",
      required_skills: ["React", "TypeScript", "Next.js", "PostgreSQL", "Docker"],
      match_score: 88.5,
      is_on_campus: true
    },
    {
      id: "job-3",
      company_name: "Stripe",
      role_title: "Backend Infrastructure Engineer",
      opportunity_type: "Full-Time",
      location: "Remote",
      stipend_or_salary: "$140,000 / year",
      description: "Architect high reliability payment routing microservices.",
      required_skills: ["Python", "FastAPI", "PostgreSQL", "Redis", "Docker"],
      match_score: 94.0,
      is_on_campus: false
    }
  ]);

  const [applications, setApplications] = useState<Application[]>([
    {
      id: "app-1",
      job_id: "job-1",
      company_name: "Google",
      role_title: "Software Engineering Intern",
      status: "Interview",
      match_score: 92.0
    },
    {
      id: "app-2",
      job_id: "job-2",
      company_name: "Microsoft",
      role_title: "Full-Stack Software Engineer",
      status: "Applied",
      match_score: 88.5
    },
    {
      id: "app-3",
      job_id: "job-3",
      company_name: "Stripe",
      role_title: "Backend Infrastructure Engineer",
      status: "Wishlist",
      match_score: 94.0
    }
  ]);

  const moveStatus = (appId: string, newStatus: Application["status"]) => {
    setApplications(prev =>
      prev.map(a => a.id === appId ? { ...a, status: newStatus } : a)
    );
  };

  const handleDraftColdEmail = (job: Job) => {
    setColdEmailModal({
      company: job.company_name,
      role: job.role_title,
      subject: `Inquiry regarding ${job.role_title} opening at ${job.company_name}`,
      body: `Dear Hiring Team,\n\nI hope this email finds you well. I have been following ${job.company_name}'s recent work in scalable systems, and I am excited to apply for the ${job.role_title} position.\n\nWith extensive experience building resilient asynchronous Python/FastAPI microservices and Next.js applications, I recently engineered architectures that improved throughput by 35%.\n\nI would love to connect for 10 minutes to discuss how my background matches your team's goals.\n\nBest regards,\nCandidate\nPortfolio: github.com/nexora-developer`
    });
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-obsidian-border pb-6">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-extrabold tracking-tight text-text-primary">
              Jobs & <span className="text-cyber">Application Kanban</span>
            </h1>
            <Badge variant="cyber">Phase 8</Badge>
          </div>
          <p className="text-text-muted mt-1 text-sm">
            Curated on-campus drives, match scores, cold-email generator, and visual status tracking.
          </p>
        </div>
        <div className="flex items-center gap-2 bg-obsidian-surface p-1 rounded-lg border border-obsidian-border">
          <Button
            variant={activeTab === "kanban" ? "primary" : "ghost"}
            size="sm"
            onClick={() => setActiveTab("kanban")}
          >
            Kanban Board (FEAT-219)
          </Button>
          <Button
            variant={activeTab === "board" ? "primary" : "ghost"}
            size="sm"
            onClick={() => setActiveTab("board")}
          >
            Job Directory ({jobs.length})
          </Button>
        </div>
      </div>

      {/* Kanban Board View */}
      {activeTab === "kanban" && (
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          {KANBAN_COLUMNS.map(col => {
            const colApps = applications.filter(a => a.status === col);
            return (
              <div key={col} className="rounded-xl border border-obsidian-border bg-obsidian-surface p-4 flex flex-col gap-3">
                <div className="flex items-center justify-between pb-2 border-b border-obsidian-border">
                  <h2 className="text-xs font-bold uppercase tracking-wider text-text-secondary">
                    {col}
                  </h2>
                  <span className="text-xs px-2 py-0.5 rounded-full bg-obsidian text-cyber font-mono font-bold">
                    {colApps.length}
                  </span>
                </div>

                <div className="space-y-3 min-h-[350px]">
                  {colApps.map(app => (
                    <div key={app.id} className="p-3 rounded-lg bg-obsidian border border-obsidian-border space-y-2 text-xs">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-text-primary">{app.company_name}</span>
                        <span className="text-cyber font-medium">{app.match_score}% match</span>
                      </div>
                      <p className="text-text-muted line-clamp-2">{app.role_title}</p>
                      <div className="flex items-center justify-between pt-2 border-t border-obsidian-border">
                        <select
                          value={app.status}
                          onChange={(e) => moveStatus(app.id, e.target.value as any)}
                          className="bg-obsidian-surface text-[10px] text-text-secondary rounded px-1.5 py-0.5 border border-obsidian-border focus:outline-none"
                        >
                          {KANBAN_COLUMNS.map(c => (
                            <option key={c} value={c}>{c}</option>
                          ))}
                        </select>
                      </div>
                    </div>
                  ))}
                  {colApps.length === 0 && (
                    <div className="h-24 flex items-center justify-center text-xs text-text-muted border border-dashed border-obsidian-border rounded-lg">
                      No applications
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Job Directory View */}
      {activeTab === "board" && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {jobs.map(job => (
            <div key={job.id} className="rounded-xl border border-obsidian-border bg-obsidian-surface p-6 flex flex-col justify-between space-y-4">
              <div>
                <div className="flex items-center justify-between">
                  <h3 className="text-base font-bold text-text-primary">{job.company_name}</h3>
                  <Badge variant={job.is_on_campus ? "cyber" : "neutral"}>
                    {job.is_on_campus ? "On-Campus Drive" : "Direct"}
                  </Badge>
                </div>
                <h4 className="text-sm font-semibold text-cyber mt-1">{job.role_title}</h4>
                <p className="text-xs text-text-muted mt-2">{job.description}</p>
                <div className="flex flex-wrap gap-1.5 mt-3">
                  {job.required_skills.map(s => (
                    <span key={s} className="px-2 py-0.5 rounded bg-obsidian text-[10px] text-text-secondary border border-obsidian-border">
                      {s}
                    </span>
                  ))}
                </div>
              </div>

              <div className="pt-4 border-t border-obsidian-border space-y-3 text-xs">
                <div className="flex justify-between text-text-muted">
                  <span>Compensation:</span>
                  <span className="text-text-primary font-medium">{job.stipend_or_salary}</span>
                </div>
                <div className="flex justify-between text-text-muted">
                  <span>Skill Match Score:</span>
                  <span className="text-cyber font-bold">{job.match_score}%</span>
                </div>
                <div className="flex gap-2 pt-2">
                  <Button variant="outline" size="sm" className="w-1/2" onClick={() => handleDraftColdEmail(job)}>
                    Cold Email
                  </Button>
                  <Button variant="primary" size="sm" className="w-1/2">
                    Apply Now
                  </Button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Cold Email Modal */}
      {coldEmailModal && (
        <div className="rounded-xl border border-obsidian-border bg-obsidian-surface p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-bold text-text-primary">
              AI Cold Email Generator ({coldEmailModal.company})
            </h3>
            <Button variant="outline" size="sm" onClick={() => setColdEmailModal(null)}>
              Close
            </Button>
          </div>
          <div className="p-3 rounded bg-obsidian border border-obsidian-border text-xs text-text-secondary">
            <strong>Subject:</strong> {coldEmailModal.subject}
          </div>
          <pre className="p-4 rounded-lg bg-obsidian border border-obsidian-border text-xs text-text-primary font-mono whitespace-pre-wrap">
            {coldEmailModal.body}
          </pre>
        </div>
      )}
    </div>
  );
}
