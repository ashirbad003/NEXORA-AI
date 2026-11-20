"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";

export default function RegisterPage() {
  const router = useRouter();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [institution, setInstitution] = useState("");
  const [department, setDepartment] = useState("");
  const [batchYear, setBatchYear] = useState<number>(2026);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const res = await fetch("http://localhost:8000/api/v1/auth/register/student", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email,
          password,
          full_name: fullName,
          institution,
          department,
          batch_year: Number(batchYear),
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || "Registration failed.");
      }

      router.push("/login?registered=true");
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Network error connecting to backend.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-[85vh] flex items-center justify-center px-4 py-12">
      <Card glow="cyber" className="max-w-lg w-full p-8 space-y-6">
        <div className="text-center space-y-2">
          <h1 className="text-2xl font-bold text-text-primary">Create Student Account</h1>
          <p className="text-sm text-text-secondary">Join NEXORA AI career ecosystem</p>
        </div>

        {error && (
          <div className="p-3 text-xs bg-red-950/50 border border-red-500/50 text-red-200 rounded-lg">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-text-muted mb-1" htmlFor="fullName">
              Full Name
            </label>
            <input
              id="fullName"
              type="text"
              required
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              className="w-full px-3 py-2 bg-obsidian border border-obsidian-border rounded-lg text-sm text-text-primary focus:outline-none focus:border-cyber"
              placeholder="Alex Johnson"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-text-muted mb-1" htmlFor="email">
              Email Address
            </label>
            <input
              id="email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-3 py-2 bg-obsidian border border-obsidian-border rounded-lg text-sm text-text-primary focus:outline-none focus:border-cyber"
              placeholder="alex@institution.edu"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-text-muted mb-1" htmlFor="password">
              Password (min. 8 characters)
            </label>
            <input
              id="password"
              type="password"
              required
              minLength={8}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-3 py-2 bg-obsidian border border-obsidian-border rounded-lg text-sm text-text-primary focus:outline-none focus:border-cyber"
              placeholder="••••••••"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-text-muted mb-1" htmlFor="institution">
                Institution
              </label>
              <input
                id="institution"
                type="text"
                value={institution}
                onChange={(e) => setInstitution(e.target.value)}
                className="w-full px-3 py-2 bg-obsidian border border-obsidian-border rounded-lg text-sm text-text-primary focus:outline-none focus:border-cyber"
                placeholder="MIT / Stanford"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-text-muted mb-1" htmlFor="department">
                Department
              </label>
              <input
                id="department"
                type="text"
                value={department}
                onChange={(e) => setDepartment(e.target.value)}
                className="w-full px-3 py-2 bg-obsidian border border-obsidian-border rounded-lg text-sm text-text-primary focus:outline-none focus:border-cyber"
                placeholder="Computer Science"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-text-muted mb-1" htmlFor="batchYear">
              Graduation Batch Year
            </label>
            <input
              id="batchYear"
              type="number"
              min={2020}
              max={2035}
              value={batchYear}
              onChange={(e) => setBatchYear(Number(e.target.value))}
              className="w-full px-3 py-2 bg-obsidian border border-obsidian-border rounded-lg text-sm text-text-primary focus:outline-none focus:border-cyber"
            />
          </div>

          <Button type="submit" variant="primary" className="w-full" disabled={loading}>
            {loading ? "Registering..." : "Create Account"}
          </Button>
        </form>

        <p className="text-center text-xs text-text-muted">
          Already have an account?{" "}
          <Link href="/login" className="text-cyber hover:underline font-semibold">
            Sign In
          </Link>
        </p>
      </Card>
    </main>
  );
}
