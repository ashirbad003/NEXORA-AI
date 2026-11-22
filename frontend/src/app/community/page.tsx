"use client";

import React, { useState, useEffect } from "react";
import { Navbar } from "@/components/layout/Navbar";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { apiGet, apiPost } from "@/lib/api";

interface Thread {
  id: string;
  user_id: string;
  author_name: string;
  title: string;
  content: string;
  category: string;
  upvotes: number;
  reply_count: number;
  is_resolved: boolean;
  created_at: string;
}

interface Reply {
  id: string;
  thread_id: string;
  author_name: string;
  content: string;
  code_snippet?: string;
  upvotes: number;
  is_accepted: boolean;
  created_at: string;
}

interface StudyGroup {
  id: string;
  name: string;
  description?: string;
  goal_description?: string;
  member_count: number;
  is_member: boolean;
}

interface LeaderboardUser {
  user_id: string;
  full_name: string;
  karma_points: number;
  accepted_answers: number;
  threads_started: number;
}

export default function CommunityPage() {
  const [threads, setThreads] = useState<Thread[]>([]);
  const [selectedThread, setSelectedThread] = useState<Thread | null>(null);
  const [replies, setReplies] = useState<Reply[]>([]);
  const [groups, setGroups] = useState<StudyGroup[]>([]);
  const [leaderboard, setLeaderboard] = useState<LeaderboardUser[]>([]);
  const [activeTab, setActiveTab] = useState<"forum" | "groups" | "leaderboard">("forum");
  const [newThreadTitle, setNewThreadTitle] = useState("");
  const [newThreadContent, setNewThreadContent] = useState("");
  const [newReplyContent, setNewReplyContent] = useState("");
  const [newReplyCode, setNewReplyCode] = useState("");
  const [showNewModal, setShowNewModal] = useState(false);

  useEffect(() => {
    loadCommunityData();
  }, []);

  const loadCommunityData = async () => {
    try {
      const [threadsRes, groupsRes, lbRes] = await Promise.all([
        apiGet<Thread[]>("/community/threads"),
        apiGet<StudyGroup[]>("/community/groups"),
        apiGet<LeaderboardUser[]>("/community/leaderboard")
      ]);
      setThreads(threadsRes || []);
      setGroups(groupsRes || []);
      setLeaderboard(lbRes || []);
    } catch (e) {
      console.error("Failed to load community data:", e);
    }
  };

  const openThread = async (thread: Thread) => {
    setSelectedThread(thread);
    try {
      const repliesRes = await apiGet<Reply[]>(`/community/threads/${thread.id}/replies`);
      setReplies(repliesRes || []);
    } catch (e) {
      console.error("Failed to load replies:", e);
    }
  };

  const handleCreateThread = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newThreadTitle || !newThreadContent) return;
    try {
      await apiPost("/community/threads", {
        title: newThreadTitle,
        content: newThreadContent,
        category: "General"
      });
      setNewThreadTitle("");
      setNewThreadContent("");
      setShowNewModal(false);
      loadCommunityData();
    } catch (e) {
      console.error("Failed to create thread:", e);
    }
  };

  const handleAddReply = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedThread || !newReplyContent) return;
    try {
      await apiPost(`/community/threads/${selectedThread.id}/replies`, {
        content: newReplyContent,
        code_snippet: newReplyCode || undefined
      });
      setNewReplyContent("");
      setNewReplyCode("");
      openThread(selectedThread);
    } catch (e) {
      console.error("Failed to add reply:", e);
    }
  };

  return (
    <div className="min-h-screen bg-obsidian text-text-primary">
      <Navbar />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between pb-6 border-b border-obsidian-border gap-4">
          <div>
            <h1 className="text-3xl font-extrabold tracking-tight flex items-center gap-3">
              Peer Learning & Community <Badge variant="cyber">Discussions & Circles</Badge>
            </h1>
            <p className="text-text-muted mt-1">
              Collaborate with fellow engineers, resolve technical doubts, and join study circles.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <Button
              variant={activeTab === "forum" ? "primary" : "outline"}
              size="sm"
              onClick={() => { setActiveTab("forum"); setSelectedThread(null); }}
            >
              Doubt Forum
            </Button>
            <Button
              variant={activeTab === "groups" ? "primary" : "outline"}
              size="sm"
              onClick={() => setActiveTab("groups")}
            >
              Study Circles
            </Button>
            <Button
              variant={activeTab === "leaderboard" ? "primary" : "outline"}
              size="sm"
              onClick={() => setActiveTab("leaderboard")}
            >
              Karma Leaderboard
            </Button>
          </div>
        </div>

        {/* FORUM TAB */}
        {activeTab === "forum" && (
          <div className="mt-6">
            {!selectedThread ? (
              <div>
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-xl font-bold">Recent Technical Discussions</h2>
                  <Button variant="primary" size="sm" onClick={() => setShowNewModal(true)}>
                    + Ask Question
                  </Button>
                </div>

                <div className="space-y-4">
                  {threads.length === 0 ? (
                    <Card className="p-8 text-center text-text-muted bg-obsidian-card border-obsidian-border">
                      No discussions found. Be the first to start a thread!
                    </Card>
                  ) : (
                    threads.map((t) => (
                      <Card
                        key={t.id}
                        className="p-5 bg-obsidian-card border-obsidian-border hover:border-cyber cursor-pointer transition-all flex justify-between items-center"
                        onClick={() => openThread(t)}
                      >
                        <div>
                          <div className="flex items-center gap-2">
                            <Badge variant="cyber">{t.category}</Badge>
                            {t.is_resolved && <Badge variant="cyber">Solved</Badge>}
                            <span className="text-xs text-text-muted">by {t.author_name}</span>
                          </div>
                          <h3 className="text-lg font-bold mt-2 text-text-primary">{t.title}</h3>
                          <p className="text-sm text-text-muted line-clamp-1 mt-1">{t.content}</p>
                        </div>
                        <div className="flex items-center gap-4 text-xs font-mono text-text-muted">
                          <span>▲ {t.upvotes}</span>
                          <span>💬 {t.reply_count}</span>
                        </div>
                      </Card>
                    ))
                  )}
                </div>
              </div>
            ) : (
              <div>
                <Button variant="outline" size="sm" className="mb-4" onClick={() => setSelectedThread(null)}>
                  ← Back to Discussions
                </Button>

                <Card className="p-6 bg-obsidian-card border-obsidian-border">
                  <div className="flex items-center gap-2 mb-2">
                    <Badge variant="cyber">{selectedThread.category}</Badge>
                    <span className="text-xs text-text-muted">Asked by {selectedThread.author_name}</span>
                  </div>
                  <h2 className="text-2xl font-bold text-text-primary">{selectedThread.title}</h2>
                  <div className="text-sm text-text-secondary mt-4 whitespace-pre-wrap">{selectedThread.content}</div>
                </Card>

                {/* Replies List */}
                <h3 className="text-lg font-bold mt-8 mb-4">Replies ({replies.length})</h3>
                <div className="space-y-4">
                  {replies.map((r) => (
                    <Card key={r.id} className={`p-5 bg-obsidian-card border ${r.is_accepted ? "border-emerald-500/80 bg-emerald-950/20" : "border-obsidian-border"}`}>
                      <div className="flex justify-between items-start">
                        <span className="text-xs font-bold text-cyber">{r.author_name}</span>
                        {r.is_accepted && <Badge variant="cyber">✓ Accepted Answer</Badge>}
                      </div>
                      <p className="text-sm mt-2 whitespace-pre-wrap">{r.content}</p>
                      {r.code_snippet && (
                        <pre className="p-3 mt-3 rounded-lg bg-obsidian font-mono text-xs overflow-x-auto text-emerald-400">
                          {r.code_snippet}
                        </pre>
                      )}
                    </Card>
                  ))}
                </div>

                {/* Add Reply */}
                <form onSubmit={handleAddReply} className="mt-8 space-y-3">
                  <h4 className="text-sm font-bold uppercase text-text-muted">Your Answer</h4>
                  <textarea
                    className="w-full p-3 rounded-xl bg-obsidian-card border border-obsidian-border text-sm focus:border-cyber outline-none"
                    rows={4}
                    placeholder="Provide detailed, technical solution..."
                    value={newReplyContent}
                    onChange={(e) => setNewReplyContent(e.target.value)}
                  />
                  <input
                    type="text"
                    className="w-full p-2 rounded-xl bg-obsidian-card border border-obsidian-border text-xs font-mono focus:border-cyber outline-none"
                    placeholder="Optional code snippet or function..."
                    value={newReplyCode}
                    onChange={(e) => setNewReplyCode(e.target.value)}
                  />
                  <Button variant="primary" size="sm" type="submit">
                    Post Answer
                  </Button>
                </form>
              </div>
            )}
          </div>
        )}

        {/* STUDY CIRCLES TAB */}
        {activeTab === "groups" && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-6">
            {groups.map((g) => (
              <Card key={g.id} className="p-6 bg-obsidian-card border-obsidian-border flex flex-col justify-between">
                <div>
                  <h3 className="text-lg font-bold text-text-primary">{g.name}</h3>
                  <p className="text-sm text-text-muted mt-2">{g.description || "Active peer study circle."}</p>
                  {g.goal_description && (
                    <div className="mt-3 text-xs bg-obsidian p-2 rounded-lg text-cyber">
                      🎯 Goal: {g.goal_description}
                    </div>
                  )}
                </div>
                <div className="mt-6 flex justify-between items-center">
                  <span className="text-xs text-text-muted">👥 {g.member_count} Members</span>
                  <Button variant={g.is_member ? "outline" : "primary"} size="sm">
                    {g.is_member ? "Entered" : "Join Circle"}
                  </Button>
                </div>
              </Card>
            ))}
          </div>
        )}

        {/* LEADERBOARD TAB */}
        {activeTab === "leaderboard" && (
          <Card className="mt-6 bg-obsidian-card border-obsidian-border p-6">
            <h2 className="text-xl font-bold mb-4">Peer Contribution & Karma Leaderboard</h2>
            <div className="divide-y divide-obsidian-border">
              {leaderboard.map((user, idx) => (
                <div key={user.user_id} className="py-4 flex justify-between items-center">
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-sm font-bold text-cyber w-6">#{idx + 1}</span>
                    <span className="font-semibold text-text-primary">{user.full_name}</span>
                  </div>
                  <div className="flex items-center gap-6 text-xs text-text-muted">
                    <span>{user.accepted_answers} Accepted</span>
                    <span>{user.threads_started} Threads</span>
                    <span className="font-bold text-amber-400 text-sm">{user.karma_points} Karma</span>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        )}
      </main>
    </div>
  );
}
