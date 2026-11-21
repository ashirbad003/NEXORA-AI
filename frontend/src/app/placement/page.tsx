"use client";

import React, { useState } from "react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";

interface PlacementDrive {
  id: string;
  company_name: string;
  role_title: string;
  ctc_lpa: number;
  tier: string;
  status: string;
  min_cgpa: number;
  allowed_branches: string[];
}

export default function PlacementPage() {
  const [drives] = useState<PlacementDrive[]>([
    {
      id: "drive-1",
      company_name: "Amazon AWS",
      role_title: "Cloud Support Associate",
      ctc_lpa: 19.5,
      tier: "Dream",
      status: "Scheduled",
      min_cgpa: 7.5,
      allowed_branches: ["CSE", "IT", "ECE"]
    },
    {
      id: "drive-2",
      company_name: "Tata Consultancy Services",
      role_title: "Systems Engineer (Digital)",
      ctc_lpa: 7.5,
      tier: "Standard",
      status: "Registration Open",
      min_cgpa: 6.5,
      allowed_branches: ["CSE", "IT", "ECE", "MECH", "CIVIL"]
    },
    {
      id: "drive-3",
      company_name: "Oracle Cloud Infrastructure",
      role_title: "Member of Technical Staff",
      ctc_lpa: 34.0,
      tier: "Super-Dream",
      status: "Ongoing",
      min_cgpa: 8.5,
      allowed_branches: ["CSE", "IT"]
    }
  ]);

  const [analytics] = useState({
    total_eligible_students: 120,
    placed_students_count: 88,
    placement_percentage: 73.3,
    average_ctc_lpa: 14.8,
    highest_ctc_lpa: 44.0,
    total_offers_extended: 112
  });

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-obsidian-border pb-6">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-extrabold tracking-tight text-text-primary">
              Placement Cell <span className="text-cyber">Command Center</span>
            </h1>
            <Badge variant="cyber">Phase 9</Badge>
          </div>
          <p className="text-text-muted mt-1 text-sm">
            Institutional cohort analytics, campus drive orchestrator, eligibility rule enforcement, and offer repository.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" size="sm">
            Export CSV / PDF
          </Button>
          <Button variant="primary" size="sm">
            + Schedule Drive
          </Button>
        </div>
      </div>

      {/* Institutional KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="rounded-xl border border-obsidian-border bg-obsidian-surface p-4">
          <span className="text-xs text-text-muted uppercase tracking-wider font-semibold">Placement Rate</span>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-3xl font-black text-cyber">{analytics.placement_percentage}%</span>
            <span className="text-xs text-text-secondary">({analytics.placed_students_count}/{analytics.total_eligible_students})</span>
          </div>
        </div>
        <div className="rounded-xl border border-obsidian-border bg-obsidian-surface p-4">
          <span className="text-xs text-text-muted uppercase tracking-wider font-semibold">Average CTC</span>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-3xl font-black text-text-primary">₹{analytics.average_ctc_lpa}</span>
            <span className="text-xs text-text-secondary">LPA</span>
          </div>
        </div>
        <div className="rounded-xl border border-obsidian-border bg-obsidian-surface p-4">
          <span className="text-xs text-text-muted uppercase tracking-wider font-semibold">Highest CTC</span>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-3xl font-black text-violet-tech">₹{analytics.highest_ctc_lpa}</span>
            <span className="text-xs text-text-secondary">LPA</span>
          </div>
        </div>
        <div className="rounded-xl border border-obsidian-border bg-obsidian-surface p-4">
          <span className="text-xs text-text-muted uppercase tracking-wider font-semibold">Offers Extended</span>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-3xl font-black text-cyber">{analytics.total_offers_extended}</span>
            <span className="text-xs text-text-secondary">Letters</span>
          </div>
        </div>
      </div>

      {/* Active Campus Drives Table */}
      <div className="rounded-xl border border-obsidian-border bg-obsidian-surface p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-semibold text-text-primary">Campus Recruitment Drives (FEAT-239)</h2>
          <Badge variant="neutral">Verified</Badge>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="border-b border-obsidian-border text-text-secondary uppercase tracking-wider">
              <tr>
                <th className="py-3 px-4">Company</th>
                <th className="py-3 px-4">Role Title</th>
                <th className="py-3 px-4">Package</th>
                <th className="py-3 px-4">Tier</th>
                <th className="py-3 px-4">Min CGPA</th>
                <th className="py-3 px-4">Branches</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y border-obsidian-border text-text-primary font-medium">
              {drives.map((d) => (
                <tr key={d.id} className="hover:bg-obsidian/40">
                  <td className="py-3.5 px-4 font-bold">{d.company_name}</td>
                  <td className="py-3.5 px-4 text-text-secondary">{d.role_title}</td>
                  <td className="py-3.5 px-4 text-cyber font-bold">₹{d.ctc_lpa} LPA</td>
                  <td className="py-3.5 px-4">
                    <Badge variant={d.tier === "Super-Dream" ? "cyber" : "neutral"}>
                      {d.tier}
                    </Badge>
                  </td>
                  <td className="py-3.5 px-4">{d.min_cgpa}</td>
                  <td className="py-3.5 px-4 text-text-muted">{d.allowed_branches.join(", ")}</td>
                  <td className="py-3.5 px-4">
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] bg-obsidian text-cyber border border-obsidian-border">
                      {d.status}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 text-right">
                    <Button variant="outline" size="sm">Manage</Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
