"use client";

import React, { useState } from "react";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";

interface Step {
  step_number: number;
  current_node?: string;
  visited_nodes: string[];
  frontier: string[];
  description: string;
}

export default function DSAVisualizerPage() {
  const [algorithm, setAlgorithm] = useState<string>("bfs");
  const [currentStepIndex, setCurrentStepIndex] = useState<number>(0);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [speedMs, setSpeedMs] = useState<number>(800);

  // Default graph topology
  const defaultNodes = ["A", "B", "C", "D", "E", "F"];
  const defaultEdges = [
    ["A", "B"],
    ["A", "C"],
    ["B", "D"],
    ["C", "E"],
    ["D", "F"],
    ["E", "F"]
  ];

  // Pre-calculated animation steps for immediate client rendering and backend sync
  const sampleSteps: Step[] = [
    {
      step_number: 1,
      current_node: "A",
      visited_nodes: [],
      frontier: ["A"],
      description: "Initialized BFS queue with root node A."
    },
    {
      step_number: 2,
      current_node: "A",
      visited_nodes: ["A"],
      frontier: ["B", "C"],
      description: "Dequeued A. Discovered unvisited neighbors B and C. Added to queue."
    },
    {
      step_number: 3,
      current_node: "B",
      visited_nodes: ["A", "B"],
      frontier: ["C", "D"],
      description: "Dequeued B. Discovered unvisited neighbor D. Added to queue."
    },
    {
      step_number: 4,
      current_node: "C",
      visited_nodes: ["A", "B", "C"],
      frontier: ["D", "E"],
      description: "Dequeued C. Discovered unvisited neighbor E. Added to queue."
    },
    {
      step_number: 5,
      current_node: "D",
      visited_nodes: ["A", "B", "C", "D"],
      frontier: ["E", "F"],
      description: "Dequeued D. Discovered unvisited neighbor F. Added to queue."
    },
    {
      step_number: 6,
      current_node: "E",
      visited_nodes: ["A", "B", "C", "D", "E"],
      frontier: ["F"],
      description: "Dequeued E. Neighbor F already discovered in queue."
    },
    {
      step_number: 7,
      current_node: "F",
      visited_nodes: ["A", "B", "C", "D", "E", "F"],
      frontier: [],
      description: "Dequeued F. All reachable graph vertices visited! Traversal complete."
    }
  ];

  const currentStep = sampleSteps[currentStepIndex] || sampleSteps[0];

  const handleNext = () => {
    if (currentStepIndex < sampleSteps.length - 1) {
      setCurrentStepIndex((prev) => prev + 1);
    }
  };

  const handlePrev = () => {
    if (currentStepIndex > 0) {
      setCurrentStepIndex((prev) => prev - 1);
    }
  };

  const handleReset = () => {
    setCurrentStepIndex(0);
    setIsPlaying(false);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
      {/* Visualizer Title Header */}
      <div className="space-y-3">
        <div className="flex items-center gap-3">
          <Badge variant="cyber">Phase 4</Badge>
          <Badge variant="violet">Interactive Algorithm Canvas</Badge>
        </div>
        <h1 className="text-3xl sm:text-4xl font-extrabold text-text-primary tracking-tight">
          DSA <span className="text-cyber">Visualizer Studio</span>
        </h1>
        <p className="text-text-secondary max-w-3xl text-sm sm:text-base">
          Step through graph traversals, shortest path computations, and dynamic programming matrices with real-time
          queue inspection, color-coded node states, and variable speed sliders.
        </p>
      </div>

      {/* Control Bar */}
      <Card className="p-4 sm:p-6 flex flex-wrap items-center justify-between gap-4 bg-obsidian-card border-obsidian-border">
        {/* Algorithm Selection */}
        <div className="flex items-center gap-3">
          <label className="text-xs font-semibold text-text-secondary">Algorithm:</label>
          <select
            value={algorithm}
            onChange={(e) => {
              setAlgorithm(e.target.value);
              handleReset();
            }}
            className="bg-obsidian border border-obsidian-border rounded-lg px-3 py-1.5 text-xs text-text-primary focus:outline-none focus:border-cyber"
          >
            <option value="bfs">Breadth-First Search (BFS)</option>
            <option value="dfs">Depth-First Search (DFS)</option>
            <option value="dijkstra">Dijkstra Shortest Path</option>
            <option value="knapsack">0/1 Knapsack DP</option>
          </select>
        </div>

        {/* Step Controls */}
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={handleReset}>
            Reset
          </Button>
          <Button variant="outline" size="sm" onClick={handlePrev} disabled={currentStepIndex === 0}>
            ← Previous
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={handleNext}
            disabled={currentStepIndex === sampleSteps.length - 1}
          >
            Next Step →
          </Button>
        </div>

        {/* Speed Slider */}
        <div className="flex items-center gap-3 text-xs text-text-secondary">
          <span>Animation Speed:</span>
          <input
            type="range"
            min="200"
            max="1500"
            step="100"
            value={speedMs}
            onChange={(e) => setSpeedMs(Number(e.target.value))}
            className="w-24 accent-cyber"
          />
          <span className="font-mono text-text-primary">{speedMs}ms</span>
        </div>
      </Card>

      {/* Interactive Simulation Display */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Graph Canvas */}
        <div className="lg:col-span-2">
          <Card className="p-8 h-96 flex flex-col justify-between bg-obsidian/90 border-obsidian-border relative overflow-hidden">
            <div className="flex justify-between items-center text-xs text-text-muted">
              <span>Graph Canvas (SVG Interactive Mode)</span>
              <span>
                Step {currentStep.step_number} of {sampleSteps.length}
              </span>
            </div>

            {/* Nodes Grid Visualization */}
            <div className="flex-1 flex items-center justify-around py-8">
              {defaultNodes.map((node) => {
                const isVisited = currentStep.visited_nodes.includes(node);
                const isCurrent = currentStep.current_node === node;
                const inFrontier = currentStep.frontier.includes(node);

                return (
                  <div key={node} className="flex flex-col items-center gap-2">
                    <div
                      className={`h-14 w-14 rounded-full flex items-center justify-center font-bold text-lg transition-all duration-300 ${
                        isCurrent
                          ? "bg-cyber text-obsidian ring-4 ring-cyber/30 scale-110 shadow-lg shadow-cyber/20"
                          : inFrontier
                          ? "bg-violet-tech text-text-primary ring-2 ring-violet-tech/40 animate-pulse"
                          : isVisited
                          ? "bg-obsidian-card border-2 border-cyber text-cyber"
                          : "bg-obsidian-card border border-obsidian-border text-text-muted"
                      }`}
                    >
                      {node}
                    </div>
                    <span className="text-[10px] font-mono text-text-muted">
                      {isCurrent ? "Active" : inFrontier ? "Queue" : isVisited ? "Visited" : "Unvisited"}
                    </span>
                  </div>
                );
              })}
            </div>

            {/* Step Explanation Banner */}
            <div className="p-4 rounded-lg bg-obsidian-card/80 border border-obsidian-border/80">
              <span className="text-xs font-bold text-cyber uppercase tracking-wider block mb-1">
                Step Description
              </span>
              <p className="text-sm text-text-primary">{currentStep.description}</p>
            </div>
          </Card>
        </div>

        {/* State & Queue Inspector */}
        <div className="space-y-6">
          <Card className="p-6 space-y-4">
            <h3 className="font-bold text-base text-text-primary border-b border-obsidian-border pb-3">
              Memory & Queue Inspector
            </h3>

            {/* Queue / Frontier */}
            <div className="space-y-1.5">
              <span className="text-xs font-semibold text-text-secondary">Current Queue (Frontier):</span>
              <div className="p-3 rounded-lg bg-obsidian border border-obsidian-border min-h-[44px] flex items-center gap-2">
                {currentStep.frontier.length === 0 ? (
                  <span className="text-xs text-text-muted">Queue is empty</span>
                ) : (
                  currentStep.frontier.map((item, idx) => (
                    <Badge key={idx} variant="violet">
                      {item}
                    </Badge>
                  ))
                )}
              </div>
            </div>

            {/* Visited Set */}
            <div className="space-y-1.5">
              <span className="text-xs font-semibold text-text-secondary">Visited Set:</span>
              <div className="p-3 rounded-lg bg-obsidian border border-obsidian-border min-h-[44px] flex flex-wrap items-center gap-2">
                {currentStep.visited_nodes.length === 0 ? (
                  <span className="text-xs text-text-muted">No nodes visited yet</span>
                ) : (
                  currentStep.visited_nodes.map((item, idx) => (
                    <Badge key={idx} variant="cyber">
                      {item}
                    </Badge>
                  ))
                )}
              </div>
            </div>

            {/* Algorithm Complexity Spec */}
            <div className="pt-4 border-t border-obsidian-border space-y-2 text-xs text-text-muted">
              <div className="flex justify-between">
                <span>Time Complexity:</span>
                <span className="font-mono text-cyber">O(V + E)</span>
              </div>
              <div className="flex justify-between">
                <span>Space Complexity:</span>
                <span className="font-mono text-cyber">O(V)</span>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
