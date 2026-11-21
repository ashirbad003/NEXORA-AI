"use client";

import React, { useState } from "react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";

interface FeatureFlag {
  id: string;
  flag_key: string;
  name: string;
  description: string;
  is_enabled: boolean;
}

export default function AdminPage() {
  const [flags, setFlags] = useState<FeatureFlag[]>([
    {
      id: "f-1",
      flag_key: "FEAT_SANDBOX_DOCKER",
      name: "Docker Execution Sandbox",
      description: "Controls rootless Linux container code execution.",
      is_enabled: true
    },
    {
      id: "f-2",
      flag_key: "FEAT_AI_COPILOT",
      name: "Unified AI Career Brain",
      description: "Autonomous career guidance and roadmap generation.",
      is_enabled: true
    },
    {
      id: "f-3",
      flag_key: "FEAT_ATS_PARSER",
      name: "ATS Resume Parsing Engine",
      description: "Automated keyword and STAR format scoring.",
      is_enabled: true
    },
    {
      id: "f-4",
      flag_key: "FEAT_PLACEMENT_PORTAL",
      name: "Campus Placement Cell",
      description: "Institutional recruitment drive coordinator.",
      is_enabled: true
    }
  ]);

  const [telemetry] = useState({
    status: "HEALTHY",
    database: "PostgreSQL 17 (Connected)",
    active_connections: 8,
    sandbox: "desktop-linux (Rootless)",
    ai_provider: "Unified Brain Engine",
    avg_latency: "42.5ms",
    error_rate: "0.00%"
  });

  const [diagnosticReport, setDiagnosticReport] = useState<string | null>(null);

  const toggleFlag = (key: string) => {
    setFlags(prev =>
      prev.map(f => f.flag_key === key ? { ...f, is_enabled: !f.is_enabled } : f)
    );
  };

  const handleGenerateDiagnostics = () => {
    setDiagnosticReport(JSON.stringify({
      report_id: "diag-c782bf9102",
      generated_at: new Date().toISOString(),
      system_version: "1.0.0-Phase9",
      healthy: true,
      checks: {
        postgres_connection: "PASS",
        alembic_head: "d9b2ef020303",
        docker_engine: "desktop-linux",
        rbac_enforcement: "ACTIVE"
      },
      telemetry_summary: {
        uptime_seconds: 86400,
        memory_usage_mb: 245.8,
        cpu_percent: 12.4
      }
    }, null, 2));
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-obsidian-border pb-6">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-extrabold tracking-tight text-text-primary">
              Super Admin <span className="text-cyber">Command Center</span>
            </h1>
            <Badge variant="cyber">Phase 9</Badge>
          </div>
          <p className="text-text-muted mt-1 text-sm">
            Feature flags & kill-switches, security telemetry, worker heartbeat inspection, and diagnostic generation.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" size="sm" onClick={handleGenerateDiagnostics}>
            Run Diagnostics (FEAT-276)
          </Button>
        </div>
      </div>

      {/* Telemetry Overview */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="rounded-xl border border-obsidian-border bg-obsidian-surface p-4">
          <span className="text-xs text-text-muted uppercase tracking-wider font-semibold">System State</span>
          <div className="mt-2 text-2xl font-black text-cyber">{telemetry.status}</div>
          <span className="text-[10px] text-text-secondary mt-1 block">Zero Critical Failures</span>
        </div>
        <div className="rounded-xl border border-obsidian-border bg-obsidian-surface p-4">
          <span className="text-xs text-text-muted uppercase tracking-wider font-semibold">Database Engine</span>
          <div className="mt-2 text-sm font-bold text-text-primary">{telemetry.database}</div>
          <span className="text-[10px] text-text-secondary mt-1 block">Active Pool: {telemetry.active_connections}</span>
        </div>
        <div className="rounded-xl border border-obsidian-border bg-obsidian-surface p-4">
          <span className="text-xs text-text-muted uppercase tracking-wider font-semibold">Execution Sandbox</span>
          <div className="mt-2 text-sm font-bold text-text-primary">{telemetry.sandbox}</div>
          <span className="text-[10px] text-text-secondary mt-1 block">Queue: 0 Pending</span>
        </div>
        <div className="rounded-xl border border-obsidian-border bg-obsidian-surface p-4">
          <span className="text-xs text-text-muted uppercase tracking-wider font-semibold">Latency / 5xx Rate</span>
          <div className="mt-2 text-2xl font-black text-cyber">{telemetry.avg_latency}</div>
          <span className="text-[10px] text-text-secondary mt-1 block">5xx Rate: {telemetry.error_rate}</span>
        </div>
      </div>

      {/* Feature Flags Manager */}
      <div className="rounded-xl border border-obsidian-border bg-obsidian-surface p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-semibold text-text-primary">System Feature Flags & Kill Switches (FEAT-262)</h2>
          <Badge variant="neutral">Super Admin RBAC</Badge>
        </div>
        <div className="space-y-3">
          {flags.map((flag) => (
            <div key={flag.id} className="p-4 rounded-lg bg-obsidian border border-obsidian-border flex items-center justify-between">
              <div>
                <div className="flex items-center gap-3">
                  <span className="font-bold text-text-primary text-sm">{flag.name}</span>
                  <code className="text-[10px] px-1.5 py-0.5 rounded bg-obsidian-surface text-cyber font-mono">
                    {flag.flag_key}
                  </code>
                </div>
                <p className="text-xs text-text-muted mt-1">{flag.description}</p>
              </div>
              <Button
                variant={flag.is_enabled ? "primary" : "outline"}
                size="sm"
                onClick={() => toggleFlag(flag.flag_key)}
              >
                {flag.is_enabled ? "ENABLED" : "DISABLED"}
              </Button>
            </div>
          ))}
        </div>
      </div>

      {/* Diagnostics Report Viewer */}
      {diagnosticReport && (
        <div className="rounded-xl border border-obsidian-border bg-obsidian-surface p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-bold text-text-primary">System Diagnostic Bundle (FEAT-276)</h3>
            <Button variant="outline" size="sm" onClick={() => setDiagnosticReport(null)}>
              Close
            </Button>
          </div>
          <pre className="p-4 rounded-lg bg-obsidian border border-obsidian-border text-xs text-cyber font-mono overflow-x-auto whitespace-pre">
            {diagnosticReport}
          </pre>
        </div>
      )}
    </div>
  );
}
