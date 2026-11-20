import React from "react";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";

export default function HomePage() {
  return (
    <main className="min-h-screen flex flex-col items-center justify-center px-4 py-16 bg-gradient-to-b from-obsidian via-obsidian-surface to-obsidian">
      <div className="max-w-4xl w-full text-center space-y-8">
        <div className="inline-flex items-center gap-2">
          <Badge variant="cyber">Phase 1 Foundation Ready</Badge>
          <Badge variant="violet">346 Features Verified</Badge>
        </div>

        <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-text-primary via-cyber to-violet-tech">
          NEXORA AI
        </h1>

        <p className="text-xl md:text-2xl text-text-secondary font-light max-w-2xl mx-auto">
          Intelligence That Moves You Forward.
        </p>

        <p className="text-sm md:text-base text-text-muted max-w-xl mx-auto">
          Unified AI-powered career development, competitive coding arena, automated mock interview studio, and campus placement ecosystem.
        </p>

        <div className="flex flex-wrap items-center justify-center gap-4 pt-4">
          <Button variant="primary" size="lg">
            Explore Ecosystem
          </Button>
          <Button variant="outline" size="lg">
            System Architecture
          </Button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-12 text-left">
          <Card glow="cyber">
            <h3 className="text-lg font-bold text-cyber mb-2">Unified AI Brain</h3>
            <p className="text-sm text-text-secondary">
              Provider-independent intelligence with deterministic local fallback and student context memory.
            </p>
          </Card>

          <Card glow="violet">
            <h3 className="text-lg font-bold text-violet-tech mb-2">Coding Arena</h3>
            <p className="text-sm text-text-secondary">
              Process-isolated sandbox runner supporting Python, C++, Java, and algorithms visualizer.
            </p>
          </Card>

          <Card glow="none">
            <h3 className="text-lg font-bold text-text-primary mb-2">Placement Intelligence</h3>
            <p className="text-sm text-text-secondary">
              Institutional portal with batch eligibility filtering, mock drives, and accreditation reporting.
            </p>
          </Card>
        </div>
      </div>
    </main>
  );
}
