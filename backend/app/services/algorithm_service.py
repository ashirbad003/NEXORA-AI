from typing import List, Dict, Any, Optional
from collections import deque
import heapq

class AlgorithmTraceEngine:
    """
    Deterministic step-by-step algorithm trace generator for DSA Visualizer (FEAT-163..FEAT-180).
    Produces structured animation steps containing queues, stacks, distance tables, and backtrack paths.
    """

    @staticmethod
    def trace_bfs(nodes: List[str], edges: List[List[str]], start_node: str) -> Dict[str, Any]:
        """Breadth-First Search step-by-step queue trace (FEAT-163)."""
        adj: Dict[str, List[str]] = {n: [] for n in nodes}
        for u, v in edges:
            if u in adj and v in adj:
                adj[u].append(v)
                adj[v].append(u)
        for n in adj:
            adj[n].sort()

        steps = []
        visited = []
        queue = deque([start_node])
        seen = {start_node}
        step_num = 1

        steps.append({
            "step_number": step_num,
            "current_node": start_node,
            "visited_nodes": list(visited),
            "frontier": list(queue),
            "description": f"Enqueued start node {start_node}.",
            "state_snapshot": {"queue": list(queue)}
        })

        while queue:
            curr = queue.popleft()
            visited.append(curr)
            step_num += 1
            
            newly_enqueued = []
            for neighbor in adj.get(curr, []):
                if neighbor not in seen:
                    seen.add(neighbor)
                    queue.append(neighbor)
                    newly_enqueued.append(neighbor)

            steps.append({
                "step_number": step_num,
                "current_node": curr,
                "visited_nodes": list(visited),
                "frontier": list(queue),
                "description": f"Visited node {curr}." + (f" Discovered neighbors: {', '.join(newly_enqueued)}" if newly_enqueued else " No new unvisited neighbors."),
                "state_snapshot": {"queue": list(queue), "adj": adj.get(curr, [])}
            })

        return {
            "algorithm": "BFS",
            "total_steps": len(steps),
            "steps": steps,
            "result": {"traversal_order": visited}
        }

    @staticmethod
    def trace_dfs(nodes: List[str], edges: List[List[str]], start_node: str) -> Dict[str, Any]:
        """Depth-First Search step-by-step stack/backtracking trace (FEAT-164)."""
        adj: Dict[str, List[str]] = {n: [] for n in nodes}
        for u, v in edges:
            if u in adj and v in adj:
                adj[u].append(v)
                adj[v].append(u)
        for n in adj:
            adj[n].sort()

        steps = []
        visited = []
        stack = [start_node]
        seen = {start_node}
        step_num = 1

        steps.append({
            "step_number": step_num,
            "current_node": start_node,
            "visited_nodes": list(visited),
            "frontier": list(stack),
            "description": f"Pushed start node {start_node} onto stack.",
            "state_snapshot": {"stack": list(stack)}
        })

        while stack:
            curr = stack.pop()
            if curr not in visited:
                visited.append(curr)
            step_num += 1

            # Discover neighbors in reverse order so lowest is popped first
            unvisited_neighbors = [nb for nb in adj.get(curr, []) if nb not in seen]
            for nb in reversed(unvisited_neighbors):
                seen.add(nb)
                stack.append(nb)

            steps.append({
                "step_number": step_num,
                "current_node": curr,
                "visited_nodes": list(visited),
                "frontier": list(stack),
                "description": f"Exploring node {curr}." + (f" Pushed unvisited neighbors: {unvisited_neighbors}" if unvisited_neighbors else " Backtracking."),
                "state_snapshot": {"stack": list(stack)}
            })

        return {
            "algorithm": "DFS",
            "total_steps": len(steps),
            "steps": steps,
            "result": {"traversal_order": visited}
        }

    @staticmethod
    def trace_dijkstra(nodes: List[str], edges: List[Dict[str, Any]], start_node: str) -> Dict[str, Any]:
        """Dijkstra's shortest path priority queue trace (FEAT-165)."""
        adj: Dict[str, List[Dict[str, Any]]] = {n: [] for n in nodes}
        for e in edges:
            u, v, w = e["from"], e["to"], float(e.get("weight", 1))
            if u in adj and v in adj:
                adj[u].append({"to": v, "weight": w})
                adj[v].append({"to": u, "weight": w})

        distances = {n: float("inf") for n in nodes}
        distances[start_node] = 0.0
        pq = [(0.0, start_node)]
        visited = set()
        steps = []
        step_num = 1

        steps.append({
            "step_number": step_num,
            "current_node": start_node,
            "visited_nodes": [],
            "frontier": [start_node],
            "description": f"Initialized distances. Start node {start_node} dist=0.",
            "state_snapshot": {"distances": dict(distances)}
        })

        while pq:
            d, u = heapq.heappop(pq)
            if u in visited:
                continue
            visited.add(u)
            step_num += 1

            relaxed = []
            for edge in adj.get(u, []):
                v, w = edge["to"], edge["weight"]
                if distances[u] + w < distances[v]:
                    distances[v] = distances[u] + w
                    heapq.heappush(pq, (distances[v], v))
                    relaxed.append(f"{v} (new dist: {distances[v]})")

            steps.append({
                "step_number": step_num,
                "current_node": u,
                "visited_nodes": list(visited),
                "frontier": [item[1] for item in pq],
                "description": f"Extracted min node {u} (dist={d})." + (f" Relaxed edges to: {', '.join(relaxed)}" if relaxed else " No shorter path updates."),
                "state_snapshot": {"distances": dict(distances)}
            })

        return {
            "algorithm": "Dijkstra",
            "total_steps": len(steps),
            "steps": steps,
            "result": {"shortest_distances": distances}
        }

    @staticmethod
    def trace_knapsack(weights: List[int], values: List[int], capacity: int) -> Dict[str, Any]:
        """0/1 Knapsack 2D Dynamic Programming matrix trace (FEAT-172)."""
        n = len(weights)
        dp = [[0] * (capacity + 1) for _ in range(n + 1)]
        steps = []
        step_num = 1

        steps.append({
            "step_number": step_num,
            "current_node": "init",
            "visited_nodes": [],
            "frontier": [],
            "description": f"Initialized {n+1}x{capacity+1} DP table with zeros.",
            "state_snapshot": {"dp_row": 0, "dp_col": 0, "value": 0}
        })

        for i in range(1, n + 1):
            w = weights[i - 1]
            v = values[i - 1]
            for c in range(1, capacity + 1):
                step_num += 1
                if w <= c:
                    dp[i][c] = max(dp[i - 1][c], dp[i - 1][c - w] + v)
                    chosen = "included" if dp[i][c] == dp[i - 1][c - w] + v else "excluded"
                else:
                    dp[i][c] = dp[i - 1][c]
                    chosen = "too heavy"

                steps.append({
                    "step_number": step_num,
                    "current_node": f"item_{i}_cap_{c}",
                    "visited_nodes": [f"item_{k}" for k in range(1, i)],
                    "frontier": [f"cap_{c}"],
                    "description": f"Item {i} (w={w}, v={v}) at cap {c}: {chosen} -> optimal value={dp[i][c]}.",
                    "state_snapshot": {"row": i, "col": c, "val": dp[i][c]}
                })

        return {
            "algorithm": "0/1 Knapsack DP",
            "total_steps": len(steps),
            "steps": steps,
            "result": {"max_value": dp[n][capacity]}
        }
