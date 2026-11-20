"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/authContext";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";

interface ProfileData {
  id: string;
  institution?: string;
  department?: string;
  batch_year?: number;
  cgpa?: number;
  skills?: string;
  career_preferences?: string;
  readiness_score: number;
}

export default function StudentDashboardPage() {
  const router = useRouter();
  const { user, token, isAuthenticated } = useAuth();
  const [profile, setProfile] = useState<ProfileData | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);

  // Form states
  const [cgpa, setCgpa] = useState<number | "">("");
  const [skills, setSkills] = useState("");
  const [careerPreferences, setCareerPreferences] = useState("");

  useEffect(() => {
    if (!isAuthenticated) {
      router.push("/login");
      return;
    }

    const fetchProfile = async () => {
      try {
        const res = await fetch("http://localhost:8000/api/v1/students/my-profile", {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (res.ok) {
          const data = await res.json();
          setProfile(data);
          setCgpa(data.cgpa ?? "");
          setSkills(data.skills ?? "");
          setCareerPreferences(data.career_preferences ?? "");
        }
      } catch (err) {
        console.error("Failed to load profile:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchProfile();
  }, [isAuthenticated, token, router]);

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setStatusMsg(null);

    try {
      const res = await fetch("http://localhost:8000/api/v1/students/my-profile", {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          cgpa: cgpa === "" ? null : Number(cgpa),
          skills,
          career_preferences: careerPreferences,
        }),
      });

      if (!res.ok) {
        throw new Error("Failed to update profile");
      }

      const updated = await res.json();
      setProfile(updated);
      setStatusMsg("Profile updated successfully!");
    } catch {
      setStatusMsg("Error updating profile. Please try again.");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <main className="min-h-[70vh] flex items-center justify-center text-text-muted">
        Loading student profile...
      </main>
    );
  }

  return (
    <main className="max-w-6xl mx-auto px-4 py-8 space-y-8">
      {/* Welcome Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-6 bg-obsidian-surface border border-obsidian-border rounded-xl">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">
            Welcome back, {user?.full_name}
          </h1>
          <p className="text-sm text-text-secondary mt-1">
            {profile?.department || "Student"} • {profile?.institution || "Institution"} • Batch {profile?.batch_year || "2026"}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="text-right">
            <span className="text-xs uppercase tracking-wider text-text-muted font-bold block">
              Placement Readiness
            </span>
            <span className="text-3xl font-black text-cyber">
              {profile?.readiness_score ?? 0}%
            </span>
          </div>
          <Badge variant="cyber">Phase 3 Web Shell Active</Badge>
        </div>
      </div>

      {statusMsg && (
        <div className="p-3 text-sm rounded-lg bg-cyber/10 border border-cyber/30 text-cyber">
          {statusMsg}
        </div>
      )}

      {/* Main Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Left Column: Profile & Readiness Form */}
        <div className="md:col-span-2 space-y-6">
          <Card glow="cyber" className="p-6">
            <h2 className="text-lg font-bold text-text-primary mb-4">
              Academic & Skills Profile
            </h2>
            <form onSubmit={handleUpdate} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-text-muted mb-1" htmlFor="cgpa">
                  Cumulative GPA (0.0 - 10.0)
                </label>
                <input
                  id="cgpa"
                  type="number"
                  step="0.01"
                  min={0}
                  max={10}
                  value={cgpa}
                  onChange={(e) => setCgpa(e.target.value === "" ? "" : Number(e.target.value))}
                  className="w-full px-3 py-2 bg-obsidian border border-obsidian-border rounded-lg text-sm text-text-primary focus:outline-none focus:border-cyber"
                  placeholder="e.g. 8.75"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-text-muted mb-1" htmlFor="skills">
                  Technical Skills (comma-separated)
                </label>
                <input
                  id="skills"
                  type="text"
                  value={skills}
                  onChange={(e) => setSkills(e.target.value)}
                  className="w-full px-3 py-2 bg-obsidian border border-obsidian-border rounded-lg text-sm text-text-primary focus:outline-none focus:border-cyber"
                  placeholder="Python, React, TypeScript, PostgreSQL, Algorithms"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-text-muted mb-1" htmlFor="career">
                  Target Career Preferences / Roles
                </label>
                <input
                  id="career"
                  type="text"
                  value={careerPreferences}
                  onChange={(e) => setCareerPreferences(e.target.value)}
                  className="w-full px-3 py-2 bg-obsidian border border-obsidian-border rounded-lg text-sm text-text-primary focus:outline-none focus:border-cyber"
                  placeholder="Full-Stack Engineer, AI Research, Site Reliability"
                />
              </div>

              <Button type="submit" variant="primary" disabled={saving}>
                {saving ? "Saving Changes..." : "Update Profile & Recalculate"}
              </Button>
            </form>
          </Card>
        </div>

        {/* Right Column: Platform Sprints & Navigation */}
        <div className="space-y-6">
          <Card glow="violet" className="p-6 space-y-4">
            <h3 className="text-base font-bold text-violet-tech">Quick Navigation</h3>
            <div className="space-y-2 text-sm">
              <div className="p-3 bg-obsidian rounded-lg border border-obsidian-border flex justify-between items-center">
                <span>Learning Hub</span>
                <Badge variant="violet">Phase 4</Badge>
              </div>
              <div className="p-3 bg-obsidian rounded-lg border border-obsidian-border flex justify-between items-center">
                <span>Coding Arena</span>
                <Badge variant="neutral">Phase 5</Badge>
              </div>
              <div className="p-3 bg-obsidian rounded-lg border border-obsidian-border flex justify-between items-center">
                <span>Mock Interview Studio</span>
                <Badge variant="neutral">Phase 7</Badge>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </main>
  );
}
