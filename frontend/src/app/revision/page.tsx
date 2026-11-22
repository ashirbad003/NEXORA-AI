"use client";

import React, { useState, useEffect, useRef } from "react";
import { Navbar } from "@/components/layout/Navbar";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { apiGet, apiPost } from "@/lib/api";

interface Flashcard {
  id: string;
  deck_id: string;
  prompt: string;
  answer: string;
  explanation?: string;
  repetition: number;
  interval_days: number;
  ease_factor: number;
  stability: number;
}

interface Deck {
  id: string;
  user_id: string;
  title: string;
  description?: string;
  category: string;
  tags?: string[];
  is_public: boolean;
  is_approved: boolean;
  card_count: number;
  due_card_count: number;
}

interface HeatmapDay {
  date: string;
  count: number;
}

interface DashboardStats {
  total_decks: number;
  total_cards: number;
  due_cards_count: number;
  cards_reviewed_today: number;
  retention_rate_pct: number;
  current_streak_days: number;
  heatmap: HeatmapDay[];
}

interface AnkiExportData {
  deck_title: string;
  description?: string;
  category: string;
  cards: Array<{
    prompt: string;
    answer: string;
    explanation?: string;
    code_snippet?: string;
  }>;
}

export default function RevisionPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [decks, setDecks] = useState<Deck[]>([]);
  const [pendingDecks, setPendingDecks] = useState<Deck[]>([]);
  const [dueCards, setDueCards] = useState<Flashcard[]>([]);
  const [currentCardIndex, setCurrentCardIndex] = useState(0);
  const [isFlipped, setIsFlipped] = useState(false);
  const [selectedDeckId, setSelectedDeckId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"study" | "decks" | "focus" | "moderation">("study");
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  // Focus Timer state
  const [timerRunning, setTimerRunning] = useState(false);
  const [timeLeft, setTimeLeft] = useState(25 * 60);

  // Import Modal state
  const [showImportModal, setShowImportModal] = useState(false);
  const [importJsonText, setImportJsonText] = useState("");
  const [importTitle, setImportTitle] = useState("");
  const [importCategory, setImportCategory] = useState("Technical");
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    loadData();
  }, [selectedDeckId]);

  useEffect(() => {
    let interval: any = null;
    if (timerRunning && timeLeft > 0) {
      interval = setInterval(() => {
        setTimeLeft((prev) => prev - 1);
      }, 1000);
    } else if (timeLeft === 0) {
      setTimerRunning(false);
    }
    return () => clearInterval(interval);
  }, [timerRunning, timeLeft]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [statsRes, decksRes, dueRes] = await Promise.all([
        apiGet<DashboardStats>("/revision/dashboard/stats?timezone=UTC").catch(() => null),
        apiGet<Deck[]>("/revision/decks").catch(() => []),
        apiGet<Flashcard[]>(selectedDeckId ? `/revision/cards/due?deck_id=${selectedDeckId}` : "/revision/cards/due").catch(() => [])
      ]);
      setStats(statsRes);
      setDecks(decksRes || []);
      setDueCards(dueRes || []);
      setCurrentCardIndex(0);
      setIsFlipped(false);

      // Check admin pending decks silently
      try {
        const modRes = await apiGet<Deck[]>("/revision/admin/moderation/pending");
        setPendingDecks(modRes || []);
      } catch {
        setPendingDecks([]);
      }
    } catch (e) {
      console.error("Failed to load revision data:", e);
    } finally {
      setLoading(false);
    }
  };

  const submitGrade = async (grade: number) => {
    if (dueCards.length === 0) return;
    const card = dueCards[currentCardIndex];
    try {
      const idempotencyKey = "rev-" + Math.random().toString(36).substring(2, 15) + Date.now();
      await apiPost("/revision/reviews/submit", {
        card_id: card.id,
        grade: grade,
        idempotency_key: idempotencyKey,
        time_spent_ms: 2500,
        user_timezone: "UTC"
      });

      // Advance
      setIsFlipped(false);
      if (currentCardIndex + 1 < dueCards.length) {
        setCurrentCardIndex(currentCardIndex + 1);
      } else {
        // Reload cards
        loadData();
      }
    } catch (e) {
      console.error("Failed to submit review:", e);
    }
  };

  const handleExportAnki = async (deckId: string, deckTitle: string) => {
    try {
      const exportData = await apiGet<AnkiExportData>(`/revision/decks/${deckId}/export/anki`);
      const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${deckTitle.replace(/\s+/g, "_")}_anki_export.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      setActionMessage(`Deck "${deckTitle}" exported successfully!`);
      setTimeout(() => setActionMessage(null), 4000);
    } catch (e: any) {
      alert(`Export failed: ${e.message || e}`);
    }
  };

  const handleImportAnki = async () => {
    try {
      if (!importTitle.trim()) {
        alert("Please provide a deck title.");
        return;
      }
      let cards = [];
      try {
        const parsed = JSON.parse(importJsonText);
        cards = Array.isArray(parsed) ? parsed : parsed.cards || [];
      } catch (parseErr) {
        alert("Invalid JSON format. Please paste valid card JSON array.");
        return;
      }

      if (cards.length === 0) {
        alert("No valid cards found in JSON.");
        return;
      }

      await apiPost("/revision/decks/import/anki", {
        title: importTitle,
        category: importCategory,
        cards: cards
      });

      setShowImportModal(false);
      setImportJsonText("");
      setImportTitle("");
      setActionMessage("Deck imported successfully!");
      setTimeout(() => setActionMessage(null), 4000);
      loadData();
    } catch (e: any) {
      alert(`Import failed: ${e.message || e}`);
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (event) => {
      const content = event.target?.result as string;
      setImportJsonText(content);
      try {
        const parsed = JSON.parse(content);
        if (parsed.deck_title || parsed.title) {
          setImportTitle(parsed.deck_title || parsed.title);
        }
        if (parsed.category) {
          setImportCategory(parsed.category);
        }
      } catch {}
    };
    reader.readAsText(file);
  };

  const handleForkDeck = async (deckId: string) => {
    try {
      await apiPost(`/revision/decks/${deckId}/fork`, {});
      setActionMessage("Deck forked into your library successfully!");
      setTimeout(() => setActionMessage(null), 4000);
      loadData();
    } catch (e: any) {
      alert(`Fork failed: ${e.message || e}`);
    }
  };

  const handleApproveDeck = async (deckId: string) => {
    try {
      await apiPost(`/revision/admin/moderation/${deckId}/approve`, {});
      setActionMessage("Deck approved!");
      setTimeout(() => setActionMessage(null), 4000);
      loadData();
    } catch (e: any) {
      alert(`Moderation failed: ${e.message || e}`);
    }
  };

  const handleRejectDeck = async (deckId: string) => {
    try {
      await apiPost(`/revision/admin/moderation/${deckId}/reject`, {});
      setActionMessage("Deck rejected.");
      setTimeout(() => setActionMessage(null), 4000);
      loadData();
    } catch (e: any) {
      alert(`Moderation failed: ${e.message || e}`);
    }
  };

  const currentCard = dueCards[currentCardIndex];

  return (
    <div className="min-h-screen bg-obsidian text-text-primary">
      <Navbar />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {actionMessage && (
          <div className="mb-6 p-4 rounded-xl bg-emerald-950/60 border border-emerald-600 text-emerald-200 text-sm flex justify-between items-center">
            <span>{actionMessage}</span>
            <button onClick={() => setActionMessage(null)} className="text-emerald-400 hover:text-white">✕</button>
          </div>
        )}

        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between pb-6 border-b border-obsidian-border gap-4">
          <div>
            <h1 className="text-3xl font-extrabold tracking-tight flex items-center gap-3">
              Smart Revision <Badge variant="cyber">SM-2 Spaced Repetition</Badge>
            </h1>
            <p className="text-text-muted mt-1">
              Scientifically proven recall schedules based on cognitive retention curves and active recall.
            </p>
          </div>

          <div className="flex items-center gap-2 flex-wrap">
            <Button
              variant={activeTab === "study" ? "primary" : "outline"}
              size="sm"
              onClick={() => setActiveTab("study")}
            >
              Active Study
            </Button>
            <Button
              variant={activeTab === "decks" ? "primary" : "outline"}
              size="sm"
              onClick={() => setActiveTab("decks")}
            >
              Decks ({decks.length})
            </Button>
            <Button
              variant={activeTab === "focus" ? "primary" : "outline"}
              size="sm"
              onClick={() => setActiveTab("focus")}
            >
              Focus Pomodoro
            </Button>
            {pendingDecks.length > 0 && (
              <Button
                variant={activeTab === "moderation" ? "primary" : "outline"}
                size="sm"
                onClick={() => setActiveTab("moderation")}
              >
                Moderation ({pendingDecks.length})
              </Button>
            )}
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowImportModal(true)}
              className="border-cyber text-cyber hover:bg-cyber/10"
            >
              + Import Deck
            </Button>
          </div>
        </div>

        {/* Dashboard Metrics Row */}
        {stats && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 my-6">
            <Card className="p-4 bg-obsidian-card border-obsidian-border">
              <span className="text-xs uppercase font-bold text-text-muted">Due Today</span>
              <div className="text-3xl font-black text-cyber mt-1">{stats.due_cards_count}</div>
              <p className="text-xs text-text-muted mt-1">Cards ready for review</p>
            </Card>
            <Card className="p-4 bg-obsidian-card border-obsidian-border">
              <span className="text-xs uppercase font-bold text-text-muted">Reviewed Today</span>
              <div className="text-3xl font-black text-text-primary mt-1">{stats.cards_reviewed_today}</div>
              <p className="text-xs text-text-muted mt-1">Total repetitions completed</p>
            </Card>
            <Card className="p-4 bg-obsidian-card border-obsidian-border">
              <span className="text-xs uppercase font-bold text-text-muted">Retention Rate</span>
              <div className="text-3xl font-black text-emerald-400 mt-1">{stats.retention_rate_pct}%</div>
              <p className="text-xs text-text-muted mt-1">Ebbinghaus retention score</p>
            </Card>
            <Card className="p-4 bg-obsidian-card border-obsidian-border">
              <span className="text-xs uppercase font-bold text-text-muted">Day Streak</span>
              <div className="text-3xl font-black text-amber-400 mt-1">{stats.current_streak_days} 🔥</div>
              <p className="text-xs text-text-muted mt-1">Consecutive revision days</p>
            </Card>
          </div>
        )}

        {/* ACTIVE STUDY TAB */}
        {activeTab === "study" && (
          <div className="mt-8 max-w-2xl mx-auto">
            {loading ? (
              <div className="text-center py-16 text-text-muted">Loading flashcards...</div>
            ) : dueCards.length === 0 ? (
              <Card className="p-12 text-center bg-obsidian-card border-obsidian-border">
                <div className="text-5xl mb-4">🎉</div>
                <h2 className="text-2xl font-bold">All Caught Up!</h2>
                <p className="text-text-muted mt-2">
                  No cards are currently due for review. Come back later or explore other decks!
                </p>
              </Card>
            ) : currentCard ? (
              <div>
                <div className="flex justify-between items-center text-xs text-text-muted mb-3">
                  <span>Card {currentCardIndex + 1} of {dueCards.length}</span>
                  <span>Ease Factor: {currentCard.ease_factor}</span>
                </div>

                {/* 3D Flip Flashcard */}
                <div
                  className="w-full min-h-[300px] p-8 rounded-2xl bg-gradient-to-br from-obsidian-surface to-obsidian-card border-2 border-obsidian-border shadow-2xl flex flex-col justify-between cursor-pointer transition-all hover:border-cyber"
                  onClick={() => setIsFlipped(!isFlipped)}
                >
                  <div className="text-xs uppercase font-bold tracking-widest text-cyber">
                    {isFlipped ? "Answer & Explanation" : "Prompt / Question"}
                  </div>

                  <div className="my-auto py-6 text-xl sm:text-2xl font-semibold leading-relaxed text-center">
                    {isFlipped ? currentCard.answer : currentCard.prompt}
                  </div>

                  {isFlipped && currentCard.explanation && (
                    <div className="text-sm text-text-muted border-t border-obsidian-border pt-4 text-center">
                      {currentCard.explanation}
                    </div>
                  )}

                  <div className="text-center text-xs text-text-muted italic">
                    {isFlipped ? "Rate your recall confidence below" : "Click anywhere to flip"}
                  </div>
                </div>

                {/* SM-2 Recall Rating Bar */}
                {isFlipped && (
                  <div className="grid grid-cols-4 gap-2 mt-6">
                    <button
                      onClick={() => submitGrade(1)}
                      className="py-3 px-2 rounded-xl bg-red-950/40 border border-red-800/60 hover:bg-red-900/60 text-red-300 font-bold text-sm transition-all"
                    >
                      Again (1)
                      <span className="block text-xs font-normal opacity-70">1 day</span>
                    </button>
                    <button
                      onClick={() => submitGrade(3)}
                      className="py-3 px-2 rounded-xl bg-amber-950/40 border border-amber-800/60 hover:bg-amber-900/60 text-amber-300 font-bold text-sm transition-all"
                    >
                      Hard (3)
                      <span className="block text-xs font-normal opacity-70">Interval + EF-</span>
                    </button>
                    <button
                      onClick={() => submitGrade(4)}
                      className="py-3 px-2 rounded-xl bg-blue-950/40 border border-blue-800/60 hover:bg-blue-900/60 text-blue-300 font-bold text-sm transition-all"
                    >
                      Good (4)
                      <span className="block text-xs font-normal opacity-70">Scheduled</span>
                    </button>
                    <button
                      onClick={() => submitGrade(5)}
                      className="py-3 px-2 rounded-xl bg-emerald-950/40 border border-emerald-800/60 hover:bg-emerald-900/60 text-emerald-300 font-bold text-sm transition-all"
                    >
                      Easy (5)
                      <span className="block text-xs font-normal opacity-70">Bonus + EF+</span>
                    </button>
                  </div>
                )}
              </div>
            ) : null}
          </div>
        )}

        {/* DECKS TAB */}
        {activeTab === "decks" && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-6">
            {decks.map((deck) => (
              <Card key={deck.id} className="p-6 bg-obsidian-card border-obsidian-border flex flex-col justify-between">
                <div>
                  <div className="flex justify-between items-start">
                    <Badge variant="cyber">{deck.category}</Badge>
                    <span className="text-xs font-mono text-text-muted">{deck.card_count} cards</span>
                  </div>
                  <h3 className="text-lg font-bold mt-3 text-text-primary">{deck.title}</h3>
                  <p className="text-sm text-text-muted mt-1">{deck.description || "No description provided."}</p>
                  {deck.is_public && (
                    <Badge variant="neutral" className="mt-2 text-xs border border-blue-500 text-blue-400">
                      Public Deck
                    </Badge>
                  )}
                </div>
                <div className="mt-6 flex flex-col gap-2">
                  <Button
                    variant="primary"
                    size="sm"
                    className="w-full"
                    onClick={() => {
                      setSelectedDeckId(deck.id);
                      setActiveTab("study");
                    }}
                  >
                    Study Deck ({deck.due_card_count} due)
                  </Button>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      className="w-1/2 text-xs"
                      onClick={() => handleExportAnki(deck.id, deck.title)}
                    >
                      Export Anki
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      className="w-1/2 text-xs"
                      onClick={() => handleForkDeck(deck.id)}
                    >
                      Fork Deck
                    </Button>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )}

        {/* FOCUS POMODORO TAB */}
        {activeTab === "focus" && (
          <div className="max-w-md mx-auto my-12 text-center">
            <Card className="p-8 bg-obsidian-card border-obsidian-border">
              <h2 className="text-2xl font-bold">Revision Focus Sprint</h2>
              <p className="text-xs text-text-muted mt-1">Pomodoro 25-minute deep retention cycle</p>

              <div className="text-6xl font-black font-mono my-8 text-cyber">
                {Math.floor(timeLeft / 60).toString().padStart(2, "0")}:
                {(timeLeft % 60).toString().padStart(2, "0")}
              </div>

              <div className="flex justify-center gap-4">
                <Button
                  variant={timerRunning ? "outline" : "primary"}
                  onClick={() => setTimerRunning(!timerRunning)}
                >
                  {timerRunning ? "Pause" : "Start Focus"}
                </Button>
                <Button
                  variant="outline"
                  onClick={() => {
                    setTimerRunning(false);
                    setTimeLeft(25 * 60);
                  }}
                >
                  Reset
                </Button>
              </div>
            </Card>
          </div>
        )}

        {/* MODERATION TAB (ADMIN ONLY) */}
        {activeTab === "moderation" && (
          <div className="mt-6">
            <h2 className="text-xl font-bold mb-4">Pending Deck Moderation (FEAT-162)</h2>
            {pendingDecks.length === 0 ? (
              <p className="text-text-muted">No pending decks awaiting moderation.</p>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {pendingDecks.map((deck) => (
                  <Card key={deck.id} className="p-5 bg-obsidian-card border-obsidian-border flex justify-between items-center">
                    <div>
                      <h3 className="font-bold text-text-primary">{deck.title}</h3>
                      <p className="text-xs text-text-muted mt-1">{deck.description || "No description"}</p>
                      <span className="text-xs text-cyber font-mono">{deck.card_count} cards • Category: {deck.category}</span>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        variant="primary"
                        onClick={() => handleApproveDeck(deck.id)}
                      >
                        Approve
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleRejectDeck(deck.id)}
                      >
                        Reject
                      </Button>
                    </div>
                  </Card>
                ))}
              </div>
            )}
          </div>
        )}

        {/* ANKI IMPORT MODAL */}
        {showImportModal && (
          <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-obsidian-card border border-obsidian-border rounded-2xl max-w-lg w-full p-6 shadow-2xl">
              <h2 className="text-xl font-bold mb-2">Import Flashcard Deck (FEAT-157)</h2>
              <p className="text-xs text-text-muted mb-4">
                Import cards from an Anki JSON export or paste JSON cards payload directly.
              </p>

              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-bold text-text-muted mb-1">Deck Title</label>
                  <input
                    type="text"
                    value={importTitle}
                    onChange={(e) => setImportTitle(e.target.value)}
                    placeholder="e.g. Dynamic Programming Master Deck"
                    className="w-full px-3 py-2 rounded-lg bg-obsidian border border-obsidian-border text-sm text-text-primary focus:outline-none focus:border-cyber"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-text-muted mb-1">Category</label>
                  <input
                    type="text"
                    value={importCategory}
                    onChange={(e) => setImportCategory(e.target.value)}
                    placeholder="e.g. Algorithms, System Design, Behavioral"
                    className="w-full px-3 py-2 rounded-lg bg-obsidian border border-obsidian-border text-sm text-text-primary focus:outline-none focus:border-cyber"
                  />
                </div>

                <div>
                  <div className="flex justify-between items-center mb-1">
                    <label className="text-xs font-bold text-text-muted">Cards JSON Array</label>
                    <button
                      onClick={() => fileInputRef.current?.click()}
                      className="text-xs text-cyber hover:underline"
                    >
                      Upload JSON File
                    </button>
                  </div>
                  <input
                    type="file"
                    ref={fileInputRef}
                    onChange={handleFileUpload}
                    accept=".json"
                    className="hidden"
                  />
                  <textarea
                    rows={6}
                    value={importJsonText}
                    onChange={(e) => setImportJsonText(e.target.value)}
                    placeholder='[&#10;  {"prompt": "What is Memoization?", "answer": "Caching top-down subproblem results.", "explanation": "Avoids redundant tree recalculation."}&#10;]'
                    className="w-full px-3 py-2 rounded-lg bg-obsidian border border-obsidian-border text-xs font-mono text-text-primary focus:outline-none focus:border-cyber"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-3 mt-6">
                <Button variant="outline" size="sm" onClick={() => setShowImportModal(false)}>
                  Cancel
                </Button>
                <Button variant="primary" size="sm" onClick={handleImportAnki}>
                  Confirm & Import
                </Button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}