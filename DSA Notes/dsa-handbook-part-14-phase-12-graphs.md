# DSA Placement Handbook (C++) — Part 14
# Phase 12: Graphs

**Module 12 · 22–28 hours · Tier 1 · Requires: Modules 0, 1, 4, 5, 7, 10**

---

## How this module reuses everything

Graphs feel like a new topic and are mostly a reassembly of things you already have:

| Graph technique | Built on |
|---|---|
| BFS | Module 7's queue, with the level-snapshot trick from Module 9.5 |
| DFS | Module 4's recursion, or Module 7's stack |
| Grid problems | Module 2.11's direction arrays and bounds checks |
| Dijkstra | BFS + Module 10's heap, with lazy deletion |
| Kruskal | Module 5's sorting + DSU |
| Prim | Module 10's heap |
| Topological sort | BFS or DFS with one extra piece of bookkeeping |

The genuinely new content is smaller than the module's size suggests: representation choices, the fact that **directed and undirected cycle detection are different algorithms**, the shortest-path decision table, and DSU.

### Budget for the 25 hours

| Part | Hours | Content |
|---|---|---|
| A — Fundamentals | 2 | Terminology, representation |
| B — Traversal | 8 | BFS, DFS, grids, components, cycles, bipartite |
| C — Topological sort | 3 | Kahn, DFS, course schedule |
| D — Shortest paths | 7 | The four algorithms and the decision table |
| E — MST and DSU | 4 | DSU, Kruskal, Prim |
| F — Advanced | 1 | Read-only, priority-marked |

**Grid problems deserve the biggest share of Part B.** Number of Islands and its relatives are among the most-asked graph questions in placements, and they are graph problems that never mention the word "graph".

---

# PART A — Fundamentals

## 12.1 Terminology

| Term | Meaning |
|---|---|
| Vertex / node | A point. Count is `V` or `n` |
| Edge | A connection. Count is `E` or `m` |
| Directed | Edges have a direction (u → v) |
| Undirected | Edges go both ways |
| Weighted | Edges carry a cost |
| Degree | Number of edges at a vertex. Directed graphs have **in-degree** and **out-degree** |
| Path | A sequence of vertices connected by edges |
| Cycle | A path that returns to its start |
| Connected | Every vertex is reachable from every other (undirected) |
| Component | A maximal connected piece |
| Tree | A connected acyclic undirected graph. Exactly `V−1` edges |
| DAG | Directed Acyclic Graph. The only kind that can be topologically sorted |
| Dense / sparse | `E ≈ V²` / `E ≈ V` |

### Facts worth having

- A tree with `V` vertices has exactly `V − 1` edges. Adding any edge creates exactly one cycle.
- An undirected graph with `V` vertices and `≥ V` edges **must** contain a cycle.
- A connected undirected graph needs at least `V − 1` edges.
- Maximum edges: `V(V−1)/2` undirected, `V(V−1)` directed.
- A DAG always has at least one vertex with in-degree 0. That is why Kahn's algorithm can start.

---

## 12.2 Representation

### The three options

```cpp
// 1. ADJACENCY LIST — the default
vector<vector<int>> adj(n);
adj[u].push_back(v);
adj[v].push_back(u);                 // undirected only

// Weighted:
vector<vector<pair<int,int>>> adj(n);     // {neighbour, weight}
adj[u].push_back({v, w});

// 2. ADJACENCY MATRIX
vector<vector<int>> mat(n, vector<int>(n, 0));
mat[u][v] = 1;                       // or the weight

// 3. EDGE LIST
vector<array<int,3>> edges;          // {u, v, w}
edges.push_back({u, v, w});
```

### Comparison

| | Adjacency list | Adjacency matrix | Edge list |
|---|---|---|---|
| Space | O(V + E) | **O(V²)** | O(E) |
| Iterate a vertex's neighbours | O(degree) | **O(V)** | O(E) |
| Check if edge (u,v) exists | O(degree) | **O(1)** | O(E) |
| Add an edge | O(1) | O(1) | O(1) |
| Best for | Almost everything | Dense graphs, Floyd-Warshall | Kruskal, Bellman-Ford |

### Which to use

**Adjacency list, by default.** Real graphs are sparse, traversals iterate neighbours constantly, and O(V + E) beats O(V²) whenever E is much less than V². At V = 10⁵ a matrix needs 10¹⁰ cells and is simply impossible.

**Adjacency matrix** when the graph is dense, when you need O(1) edge lookups, or when the algorithm is matrix-shaped (Floyd-Warshall).

**Edge list** when the algorithm processes edges rather than vertices: Kruskal sorts them, Bellman-Ford relaxes all of them repeatedly.

### Grids are graphs

A 2D grid is an implicit graph: each cell is a vertex, adjacent cells are edges. You never build `adj` — you compute neighbours on the fly with the direction arrays from Module 2.11.

```cpp
int dr[] = {-1, 1, 0, 0};
int dc[] = {0, 0, -1, 1};

for (int d = 0; d < 4; d++) {
    int nr = r + dr[d], nc = c + dc[d];
    if (nr < 0 || nr >= n || nc < 0 || nc >= m) continue;   // bounds FIRST
    // neighbour is (nr, nc)
}
```

**Most interview graph problems are grid problems.** Recognising "this is BFS on a grid" is worth more than any algorithm in Part D.

### Must remember

1. Adjacency list by default: O(V + E) space, O(degree) neighbour iteration.
2. Adjacency matrix is O(V²) space, impossible above V ≈ 10⁴.
3. For undirected graphs, add the edge in **both** directions. Forgetting this is a silent, very common bug.
4. Edge list for Kruskal and Bellman-Ford.
5. A grid is a graph with implicit edges. Do not materialise it.
6. Complexity is O(V + E), never "O(n)". Say which is which.

---

# PART B — Traversal

## 12.3 BFS

### 1. What is it?

Explore the graph level by level: all vertices at distance 1, then all at distance 2, and so on. Uses a queue.

### 2. Why do we need it?

**BFS finds shortest paths in unweighted graphs.** That is its defining property and the reason it is not interchangeable with DFS. The first time BFS reaches a vertex, it has done so by a minimum-edge path.

### 3. Template

```cpp
vector<int> bfs(int src, const vector<vector<int>>& adj) {
    int n = adj.size();
    vector<int> dist(n, -1);                  // -1 doubles as "unvisited"
    queue<int> q;

    dist[src] = 0;
    q.push(src);

    while (!q.empty()) {
        int u = q.front(); q.pop();
        for (int v : adj[u]) {
            if (dist[v] == -1) {              // unvisited
                dist[v] = dist[u] + 1;
                q.push(v);                    // MARK WHEN PUSHING
            }
        }
    }
    return dist;
}
```

**Mark visited when you push, not when you pop.** If you mark at pop time, a vertex with several neighbours gets queued repeatedly before any of them is processed. The result is still correct but the queue can blow up to O(E), and on dense graphs that is a real time-limit failure. This is the single most common BFS bug.

Using `dist[]` as both the distance array and the visited marker saves a separate array and one more thing to keep in sync.

### 4. Multi-source BFS

Push **all** sources at the start with distance 0. Everything else is identical, and the result is the distance from the *nearest* source.

```cpp
for (each source s) { dist[s] = 0; q.push(s); }
// ... same loop
```

This is a genuinely useful technique and it solves Rotten Oranges, 01 Matrix, and Walls and Gates in a few lines each. Simulating each source separately is O(sources × (V+E)); multi-source is one pass.

### 5. Level-by-level BFS

When you need to know which level you are on (minutes elapsed, steps taken), use the size snapshot from Module 9.5:

```cpp
int level = 0;
while (!q.empty()) {
    int sz = q.size();                        // SNAPSHOT
    for (int i = 0; i < sz; i++) {
        int u = q.front(); q.pop();
        // process u
    }
    level++;
}
```

### 6. Complexity

O(V + E) time. Each vertex is enqueued once and each edge examined once (twice for undirected). O(V) space for the queue and the distance array.

### 7. Must remember

1. BFS gives shortest paths in **unweighted** graphs. Not weighted ones.
2. Mark visited at **push** time.
3. Multi-source BFS: seed the queue with every source at distance 0.
4. `dist[] = -1` serves as both distance and visited marker.
5. Level-by-level needs the `q.size()` snapshot.
6. O(V + E) time, O(V) space.
7. BFS on a weighted graph is wrong unless all weights are equal. Use Dijkstra.

---

## 12.4 DFS

### Template (recursive)

```cpp
void dfs(int u, const vector<vector<int>>& adj, vector<bool>& vis) {
    vis[u] = true;
    for (int v : adj[u])
        if (!vis[v]) dfs(v, adj, vis);
}
```

Three lines. Mark, then recurse into unvisited neighbours.

### Template (iterative)

```cpp
void dfsIter(int src, const vector<vector<int>>& adj, vector<bool>& vis) {
    stack<int> st;
    st.push(src);

    while (!st.empty()) {
        int u = st.top(); st.pop();
        if (vis[u]) continue;                 // check at POP time here
        vis[u] = true;
        for (int v : adj[u])
            if (!vis[v]) st.push(v);
    }
}
```

Note the asymmetry with BFS: iterative DFS checks `vis` when **popping**, because a vertex can legitimately be pushed several times before it is first processed, and you cannot mark it early without changing the traversal order.

### Visited marks are permanent

**This is the difference from Module 8.** In backtracking you set `visited[x] = true`, recurse, then set it back to false, because you are exploring *all paths*. In graph traversal you never reset it, because you are exploring *all vertices*.

| | Graph DFS | Backtracking |
|---|---|---|
| Goal | Visit every reachable vertex | Enumerate every path/configuration |
| `visited` | Set once, never reset | Set, recurse, **unset** |
| Complexity | O(V + E) | Exponential |

Resetting `visited` in a graph traversal turns O(V+E) into an exponential path enumeration. It is a real and fatal bug.

### Recursion depth

DFS depth can reach V. At V = 10⁵ that is borderline (Module 4.2) and at 10⁶ it segfaults. On large graphs, use the iterative version.

### BFS or DFS?

| Use BFS | Use DFS |
|---|---|
| **Shortest path** in an unweighted graph | Connectivity, components |
| "Minimum steps / moves / levels" | Cycle detection |
| Multi-source spreading (infection, fire, rot) | Topological sort (the DFS variant) |
| Level-by-level processing | Path enumeration, backtracking |
| Wide, shallow graphs | Bridges, articulation points, SCC |
| When you want an early exit at the nearest target | When recursion expresses the problem naturally |

For pure reachability and components **either works** and both are O(V + E). The choice matters when the problem mentions distance or levels — then it must be BFS.

### Must remember

1. Graph DFS marks visited **permanently**. Never reset it.
2. Recursive DFS checks `vis` before recursing; iterative DFS checks at pop time.
3. DFS depth can reach V. Use the iterative version on large graphs.
4. BFS for shortest paths and levels; DFS for structure and cycles.
5. Both are O(V + E).
6. For a disconnected graph, loop over all vertices and start a traversal from each unvisited one.

---

## 12.5 Grid problems

**The highest-frequency graph topic in placements**, and the one people fail to recognise as graphs.

### Number of Islands (LC 200)

```cpp
int numIslands(vector<vector<char>>& g) {
    int n = g.size(), m = g[0].size(), count = 0;

    function<void(int,int)> sink = [&](int r, int c) {
        if (r < 0 || r >= n || c < 0 || c >= m || g[r][c] != '1') return;
        g[r][c] = '0';                        // MARK FIRST, then recurse
        sink(r+1, c); sink(r-1, c); sink(r, c+1); sink(r, c-1);
    };

    for (int r = 0; r < n; r++)
        for (int c = 0; c < m; c++)
            if (g[r][c] == '1') { count++; sink(r, c); }

    return count;
}
```

**The structure:** loop over every cell; each time you find an unvisited land cell, that is a new island, so increment and then flood the entire island so it is never counted again.

**Mark before recursing.** Setting `g[r][c] = '0'` *after* the four recursive calls causes infinite recursion, because the neighbours immediately recurse back.

**Marking in place** avoids a separate visited grid. If you are not allowed to modify the input, use `vector<vector<bool>> vis(n, vector<bool>(m, false))` — say so and move on.

### The grid template

Every grid problem is this shape:

```cpp
int n = g.size(), m = g[0].size();
int dr[] = {-1, 1, 0, 0}, dc[] = {0, 0, -1, 1};

for (int d = 0; d < 4; d++) {
    int nr = r + dr[d], nc = c + dc[d];
    if (nr < 0 || nr >= n || nc < 0 || nc >= m) continue;   // bounds FIRST
    if (!isValid(g[nr][nc]) || visited[nr][nc]) continue;
    // process
}
```

For 8 directions (including diagonals): `dr[] = {-1,-1,-1,0,0,1,1,1}`, `dc[] = {-1,0,1,-1,1,-1,0,1}`.

### Rotten Oranges (LC 994): multi-source BFS

*Every minute, rotten oranges rot their fresh neighbours. How many minutes until all are rotten, or −1?*

```cpp
int orangesRotting(vector<vector<int>>& g) {
    int n = g.size(), m = g[0].size(), fresh = 0;
    queue<pair<int,int>> q;

    for (int r = 0; r < n; r++)
        for (int c = 0; c < m; c++) {
            if (g[r][c] == 2) q.push({r, c});     // ALL sources at once
            else if (g[r][c] == 1) fresh++;
        }

    if (fresh == 0) return 0;                     // nothing to rot

    int dr[] = {-1,1,0,0}, dc[] = {0,0,-1,1};
    int minutes = 0;

    while (!q.empty() && fresh > 0) {
        int sz = q.size();                        // one minute = one level
        for (int i = 0; i < sz; i++) {
            auto [r, c] = q.front(); q.pop();
            for (int d = 0; d < 4; d++) {
                int nr = r + dr[d], nc = c + dc[d];
                if (nr < 0 || nr >= n || nc < 0 || nc >= m) continue;
                if (g[nr][nc] != 1) continue;
                g[nr][nc] = 2;
                fresh--;
                q.push({nr, nc});
            }
        }
        minutes++;
    }
    return fresh == 0 ? minutes : -1;
}
```

Three details that cause wrong answers: **all sources seeded before the loop**, the **`fresh == 0` early return** (otherwise an all-empty grid returns 1), and the **`fresh > 0` loop guard** (otherwise the last level increments `minutes` one time too many).

### The grid family

| Problem | Technique | Note |
|---|---|---|
| Number of Islands (200) | DFS/BFS flood | Count starts, sink each |
| Flood Fill (733) | DFS flood | Check the new colour equals the old, or infinite loop |
| Max Area of Island (695) | DFS returning a count | `1 + sum of four calls` |
| Rotten Oranges (994) | Multi-source BFS | Levels are minutes |
| 01 Matrix (542) | Multi-source BFS | Seed with all 0s |
| Surrounded Regions (130) | DFS from the **border** | Mark border-connected regions first, then flip the rest |
| Word Search (79) | Backtracking | Module 8: visited **is** reset here |
| Number of Enclaves (1020) | DFS from the border | Same inversion as 130 |
| Walls and Gates | Multi-source BFS | Seed with all gates |

**Surrounded Regions and Number of Enclaves share an inversion trick** worth knowing: instead of finding the regions that *are* surrounded, find the ones that *escape* (touch the border) and mark them; everything left is surrounded. Trying to detect "surrounded" directly is far harder.

### Must remember

1. Grids are graphs. Cells are vertices, adjacency is edges.
2. Mark **before** recursing, or you get infinite recursion.
3. Bounds check **first**, before reading the cell.
4. Marking in place avoids a visited grid; say so if the input must be preserved.
5. Multi-source BFS: seed **all** sources at distance 0.
6. Level-counting BFS needs the `q.size()` snapshot and careful handling of the final increment.
7. Border-inversion solves the "surrounded region" family.
8. Complexity is O(n·m) for both BFS and DFS on a grid.

---

## 12.6 Connected components

```cpp
int countComponents(int n, const vector<vector<int>>& adj) {
    vector<bool> vis(n, false);
    int count = 0;

    for (int i = 0; i < n; i++) {
        if (!vis[i]) {
            count++;
            dfs(i, adj, vis);           // or BFS
        }
    }
    return count;
}
```

**The outer loop over all vertices is the point.** A single traversal only reaches one component. Every graph problem on a possibly-disconnected graph needs this loop, and forgetting it is a common omission — especially in bipartite checking and cycle detection.

DSU (Section 12.13) solves this too, and is the better choice when edges arrive incrementally.

---

## 12.7 Cycle detection

**Directed and undirected need different algorithms.** This is the conceptual content of the section.

### Undirected: DFS with a parent

```cpp
bool hasCycleDFS(int u, int parent, const vector<vector<int>>& adj, vector<bool>& vis) {
    vis[u] = true;
    for (int v : adj[u]) {
        if (!vis[v]) {
            if (hasCycleDFS(v, u, adj, vis)) return true;
        }
        else if (v != parent) return true;     // visited, and not where we came from
    }
    return false;
}
```

The parent check exists because every undirected edge appears twice in the adjacency list. Walking from `u` to `v` and immediately seeing `u` again in `v`'s list is not a cycle, it is the same edge.

**Caveat:** this fails with **parallel edges** (two distinct edges between the same pair), which genuinely form a cycle but look like the parent case. If parallel edges are possible, track the edge index instead of the parent vertex. Worth mentioning; rarely tested.

Kahn's algorithm and DSU also detect undirected cycles — DSU does it in one line (`if (!unite(u,v)) cycle found`), which is often the cleanest answer.

### Directed: DFS with three states

The parent trick does **not** work for directed graphs. You need to know whether a vertex is currently on the recursion stack.

```cpp
// state: 0 = unvisited, 1 = in the current DFS path, 2 = fully processed
bool hasCycleDirected(int u, const vector<vector<int>>& adj, vector<int>& state) {
    state[u] = 1;                                    // entering

    for (int v : adj[u]) {
        if (state[v] == 1) return true;              // BACK EDGE -> cycle
        if (state[v] == 0 && hasCycleDirected(v, adj, state)) return true;
    }

    state[u] = 2;                                    // leaving
    return false;
}
```

**Why "visited" alone is insufficient.** Consider `A → B`, `A → C`, `B → C`. Starting at A, DFS visits B, then C, finishes both. Back at A, it sees C already visited. That is a **cross edge**, not a cycle. Only an edge back to a vertex still on the current path (state 1) is a cycle.

State 2 means "done, and no cycle was found through here", so it is safe to skip.

### Comparison

| | Undirected | Directed |
|---|---|---|
| Method | DFS with parent | DFS with 3 states |
| Cycle signal | Visited neighbour that is not the parent | Neighbour in state 1 |
| Alternative | DSU (one line), or BFS with parent | Kahn's (order size < n) |
| Gotcha | Parallel edges | "Visited" is not enough |

### Must remember

1. Undirected and directed cycle detection are **different algorithms**.
2. Undirected: check `v != parent`, because each edge appears twice.
3. Directed: three states. A back edge to state 1 is a cycle; state 2 is a safe cross edge.
4. DSU detects undirected cycles in one line.
5. Kahn's detects directed cycles for free: if the topological order is shorter than `n`, there is a cycle.
6. Loop over all vertices for disconnected graphs.

---

## 12.8 Bipartite graphs

*Can the vertices be 2-coloured so that no edge joins same-coloured vertices?*

```cpp
bool isBipartite(const vector<vector<int>>& adj) {
    int n = adj.size();
    vector<int> color(n, -1);

    for (int s = 0; s < n; s++) {              // every component
        if (color[s] != -1) continue;

        queue<int> q;
        q.push(s);
        color[s] = 0;

        while (!q.empty()) {
            int u = q.front(); q.pop();
            for (int v : adj[u]) {
                if (color[v] == -1) {
                    color[v] = color[u] ^ 1;    // opposite colour
                    q.push(v);
                }
                else if (color[v] == color[u]) return false;
            }
        }
    }
    return true;
}
```

**The theorem worth knowing:** a graph is bipartite **if and only if it contains no odd-length cycle.** Even cycles are fine; a triangle is not. Stating this shows you understand rather than recall.

`color[u] ^ 1` flips between 0 and 1, a small bit trick from Module 14.

Applications: scheduling into two groups, "can these be split into two teams", conflict graphs. The DFS version works equally well.

### Must remember

1. Bipartite ⟺ no odd-length cycle.
2. Loop over all components.
3. `^ 1` flips the colour.
4. A conflict means an edge between same-coloured vertices, checked when the neighbour is already coloured.
5. O(V + E). BFS and DFS both work.

---

# PART C — Topological Sort

## 12.9 Topological sorting

### 1. What is it?

A linear ordering of a **DAG**'s vertices such that every edge `u → v` places `u` before `v`.

### 2. Why do we need it?

Any "do A before B" problem is this: course prerequisites, build dependencies, task scheduling, alien dictionary ordering, DP over a DAG. It is one of the highest-frequency graph topics in interviews, mostly under the name "Course Schedule".

### 3. It only exists for DAGs

A cycle makes the ordering impossible — each vertex in the cycle would have to come before itself. **Both algorithms detect this for free**, which is why "is there a cycle in this directed graph?" and "can these courses be finished?" are the same question.

### 4. Kahn's algorithm (BFS-based)

```cpp
vector<int> topoSort(int n, const vector<vector<int>>& adj) {
    vector<int> indeg(n, 0);
    for (int u = 0; u < n; u++)
        for (int v : adj[u]) indeg[v]++;

    queue<int> q;
    for (int i = 0; i < n; i++)
        if (indeg[i] == 0) q.push(i);          // no prerequisites

    vector<int> order;
    while (!q.empty()) {
        int u = q.front(); q.pop();
        order.push_back(u);

        for (int v : adj[u])
            if (--indeg[v] == 0) q.push(v);    // last prerequisite satisfied
    }

    return (int)order.size() == n ? order : vector<int>{};   // empty means a cycle
}
```

**The intuition:** repeatedly take a vertex with no remaining prerequisites, output it, and remove its outgoing edges. A DAG always has such a vertex.

**`order.size() < n` means a cycle.** Vertices inside a cycle never reach in-degree 0, so they are never enqueued. Free cycle detection.

### 5. DFS-based topological sort

```cpp
void dfs(int u, const vector<vector<int>>& adj, vector<bool>& vis, vector<int>& order) {
    vis[u] = true;
    for (int v : adj[u])
        if (!vis[v]) dfs(v, adj, vis, order);
    order.push_back(u);                        // AFTER all descendants
}

vector<int> topoSortDFS(int n, const vector<vector<int>>& adj) {
    vector<bool> vis(n, false);
    vector<int> order;
    for (int i = 0; i < n; i++)
        if (!vis[i]) dfs(i, adj, vis, order);
    reverse(order.begin(), order.end());       // reverse postorder
    return order;
}
```

**Reverse postorder is a topological order.** A vertex is appended only after everything reachable from it, so reversing puts it before all of them.

This version does **not** detect cycles on its own. Add the three-state check from 12.7 if you need that, or use Kahn's.

### 6. Course Schedule (LC 207 / 210)

LC 207 asks "can all courses be finished?", which is "is this a DAG?". LC 210 asks for the order itself. Both are Kahn's verbatim.

**Edge direction is the trap.** `[a, b]` meaning "to take `a` you must first take `b`" is an edge `b → a`, not `a → b`. Getting it backwards produces a reversed answer that is correct-looking and wrong. **Read the statement and write the direction down before coding.**

### 7. Complexity

O(V + E) for both. Kahn's uses O(V) extra for the in-degree array and queue; the DFS version uses O(V) for the stack and output.

### 8. Kahn's or DFS?

| | Kahn's (BFS) | DFS |
|---|---|---|
| Cycle detection | **Built in** | Needs the 3-state check |
| Lexicographically smallest order | Easy (use a `priority_queue`) | Hard |
| Iterative | Yes | No (unless you convert it) |
| Code length | Slightly longer | Shorter |
| Recommendation | **Default to this** | When you already have a DFS |

**Default to Kahn's.** The free cycle detection is what most problems actually want, and swapping the `queue` for a `priority_queue` gives the lexicographically smallest valid order when a problem asks for it.

### 9. Must remember

1. Topological sort exists only for DAGs.
2. Kahn's: in-degree 0 into a queue, decrement neighbours, `order.size() < n` means a cycle.
3. DFS version: reverse postorder, and it does not detect cycles by itself.
4. **Check the edge direction** in prerequisite problems.
5. Both are O(V + E).
6. `priority_queue` instead of `queue` gives the lexicographically smallest order.
7. The order is not unique unless the DAG is a chain.

### 10. Practice

- Course Schedule (LC 207, Medium)
- Course Schedule II (LC 210, Medium)
- Alien Dictionary (LC 269, Hard) — build the graph from the word list, then topo sort

---

# PART D — Shortest Paths

## 12.10 Choosing the algorithm

**The decision table is the most valuable thing in Part D.**

| Situation | Algorithm | Complexity |
|---|---|---|
| Unweighted graph, single source | **BFS** | O(V + E) |
| Weights all 0 or 1 | **0-1 BFS** (deque) | O(V + E) |
| Non-negative weights, single source | **Dijkstra** | O((V + E) log V) |
| **Negative** weights allowed, single source | **Bellman-Ford** | O(V·E) |
| Need to **detect** a negative cycle | **Bellman-Ford** | O(V·E) |
| All pairs, small V (≤ 400ish) | **Floyd-Warshall** | O(V³) |
| All pairs, sparse, non-negative | Dijkstra from each vertex | O(V·(V+E) log V) |
| DAG, any weights | Topological order + relax | O(V + E) |

### The questions to ask, in order

1. **Are the edges weighted?** No → BFS. Stop.
2. **Are any weights negative?** Yes → Bellman-Ford (or Floyd-Warshall for all pairs).
3. **Do I need all pairs?** Yes and V is small → Floyd-Warshall.
4. Otherwise → **Dijkstra.**

**Using Dijkstra on an unweighted graph is not wrong, just wasteful** — it adds a log factor for nothing. Using BFS on a weighted graph **is** wrong.

---

## 12.11 Dijkstra

### 1. What is it?

Single-source shortest paths with **non-negative** edge weights. BFS with a priority queue instead of a queue.

### 2. Core idea

Always expand the unvisited vertex with the smallest known distance. Because all weights are non-negative, **once a vertex is popped its distance is final**: no route through a vertex that is further away could possibly be shorter.

That greedy claim is the algorithm's correctness argument, and it is exactly what negative edges break.

### 3. Template

```cpp
vector<long long> dijkstra(int src, const vector<vector<pair<int,int>>>& adj) {
    int n = adj.size();
    const long long INF = LLONG_MAX / 4;
    vector<long long> dist(n, INF);

    priority_queue<pair<long long,int>,
                   vector<pair<long long,int>>,
                   greater<pair<long long,int>>> pq;        // MIN-heap on distance

    dist[src] = 0;
    pq.push({0, src});

    while (!pq.empty()) {
        auto [d, u] = pq.top(); pq.pop();

        if (d > dist[u]) continue;                  // STALE entry: lazy deletion

        for (auto [v, w] : adj[u]) {
            if (dist[u] + w < dist[v]) {
                dist[v] = dist[u] + w;
                pq.push({dist[v], v});
            }
        }
    }
    return dist;
}
```

**`if (d > dist[u]) continue;` is mandatory.** C++ has no decrease-key, so when a shorter path to `v` is found you push a *new* entry rather than updating the old one. The heap ends up with stale entries, and this line discards them. This is the lazy deletion from Module 10.5.

**Push `{distance, vertex}` in that order.** `pair` compares by `first`, so putting the distance first is what makes the heap order by distance.

**`INF = LLONG_MAX / 4`, not `LLONG_MAX`.** Otherwise `dist[u] + w` overflows.

### 4. Why negative edges break it

```
A --2--> B
A --3--> C
C --(-2)--> B

True shortest A→B: A→C→B = 3 + (-2) = 1
Dijkstra: pops B at distance 2 (before C at 3), finalises it. Answer 2. WRONG.
```

Dijkstra commits to B the moment it is the closest unvisited vertex. A negative edge discovered later can improve a path that was already finalised, and Dijkstra never revisits. **This is the most common "gotcha" question about Dijkstra.**

### 5. Complexity

O((V + E) log V) with a binary heap. The `log V` comes from heap operations; each edge can cause at most one push.

### 6. Variants worth recognising

| Problem | Change |
|---|---|
| Network Delay Time (LC 743) | Plain Dijkstra, answer is `max(dist)` |
| Path with Minimum Effort (LC 1631) | Relax with `max(effort, edge)` instead of a sum |
| Swim in Rising Water (LC 778) | Same: minimise the maximum along the path |
| Cheapest Flights Within K Stops (LC 787) | Add a stop count to the state — **Bellman-Ford is cleaner here** |
| Path with Maximum Probability (LC 1514) | Max-heap, multiply instead of add |

The "minimise the maximum edge on a path" variants are worth noticing: Dijkstra works with any relaxation function that is monotonic, not only addition.

### 7. Must remember

1. **Non-negative weights only.** Have the counterexample ready.
2. Min-heap of `{distance, vertex}`, distance first.
3. `if (d > dist[u]) continue;` for lazy deletion. Mandatory.
4. `INF = LLONG_MAX / 4` to avoid overflow on relaxation.
5. Once popped, a vertex's distance is final. That is the correctness argument.
6. O((V + E) log V).
7. Dijkstra with all weights equal to 1 is just BFS with extra overhead.

### 8. Common mistakes

- Using it with negative weights.
- Omitting the stale-entry check, giving a correct but much slower solution.
- Pushing `{vertex, distance}` and ordering by vertex id.
- `INT_MAX` as infinity, overflowing on addition.
- Using a `visited` array instead of the distance check — workable but easier to get wrong.

---

## 12.12 Bellman-Ford

### 1. What is it?

Single-source shortest paths that **tolerates negative weights** and **detects negative cycles**.

### 2. Core idea

Relax **every edge**, `V − 1` times. A shortest path has at most `V − 1` edges, and after `k` rounds every shortest path using at most `k` edges is correct. So `V − 1` rounds suffice.

### 3. Template

```cpp
vector<long long> bellmanFord(int n, int src, const vector<array<int,3>>& edges) {
    const long long INF = LLONG_MAX / 4;
    vector<long long> dist(n, INF);
    dist[src] = 0;

    for (int i = 0; i < n - 1; i++) {
        bool changed = false;
        for (auto& e : edges) {
            int u = e[0], v = e[1], w = e[2];
            if (dist[u] < INF && dist[u] + w < dist[v]) {
                dist[v] = dist[u] + w;
                changed = true;
            }
        }
        if (!changed) break;                         // early exit: converged
    }

    for (auto& e : edges) {                          // one EXTRA round
        int u = e[0], v = e[1], w = e[2];
        if (dist[u] < INF && dist[u] + w < dist[v])
            return {};                               // still improving -> negative cycle
    }
    return dist;
}
```

**The `V`-th round is the negative-cycle test.** If anything still improves after `V − 1` rounds, some path can be shortened indefinitely, which means a negative cycle is reachable.

**`dist[u] < INF` guards against relaxing from an unreachable vertex**, which would otherwise produce nonsense like `INF + (-5)`.

### 4. Complexity

O(V · E). Much slower than Dijkstra, which is why you use it only when you need the negative-weight handling.

### 5. Cheapest Flights Within K Stops (LC 787)

Bellman-Ford fits this better than Dijkstra: run exactly `k + 1` rounds and you get the shortest path using at most `k + 1` edges, which is exactly the constraint.

**One subtlety:** relax from a **snapshot** of the previous round's distances, not the live array, or a single round can use more than one edge.

```cpp
for (int i = 0; i <= k; i++) {
    vector<long long> prev = dist;                   // SNAPSHOT
    for (auto& [u, v, w] : edges)
        if (prev[u] < INF && prev[u] + w < dist[v])
            dist[v] = prev[u] + w;
}
```

### 6. Must remember

1. Handles negative weights; Dijkstra does not.
2. `V − 1` rounds, because a shortest path has at most `V − 1` edges.
3. A `V`-th round that still improves means a negative cycle.
4. Guard with `dist[u] < INF` before relaxing.
5. O(V · E), noticeably slower than Dijkstra.
6. For "at most k edges", run `k + 1` rounds with a snapshot.
7. A negative cycle makes "shortest path" undefined, not merely hard.

---

## 12.13 Floyd-Warshall

### 1. What is it?

All-pairs shortest paths in O(V³), on a distance matrix. Handles negative weights (but not negative cycles).

### 2. Template

```cpp
// d[i][j] initialised to the edge weight, 0 on the diagonal, INF otherwise
for (int k = 0; k < n; k++)              // k MUST be the OUTERMOST loop
    for (int i = 0; i < n; i++)
        for (int j = 0; j < n; j++)
            if (d[i][k] < INF && d[k][j] < INF && d[i][k] + d[k][j] < d[i][j])
                d[i][j] = d[i][k] + d[k][j];
```

**`k` must be the outer loop.** This is the classic bug and it produces wrong answers that look almost right.

**Why.** The invariant is: after iteration `k`, `d[i][j]` is the shortest path from `i` to `j` using only vertices `{0..k}` as intermediates. Building that up requires `k` to advance slowest. Putting `k` innermost means you consider intermediate vertices before the paths through them are finalised.

This is a DP over "allowed intermediate vertices" — it is the clearest example of DP on a graph, and Module 13 will make the framing familiar.

### 3. Negative cycle detection

If `d[i][i] < 0` for any `i` after the algorithm, vertex `i` lies on a negative cycle.

### 4. When to use it

V ≤ 400 or so, since 400³ is 6.4 × 10⁷ which fits comfortably. Beyond that it is too slow. Module 1's constraint table flagged `n ≤ 100` as an O(n³) signal, and in graph problems that almost always means Floyd-Warshall.

### 5. Must remember

1. **`k` outermost.** The single most common bug in this algorithm.
2. O(V³) time, O(V²) space.
3. Needs an adjacency **matrix**.
4. Handles negative edges; detects negative cycles via `d[i][i] < 0`.
5. `n ≤ 100` in a graph problem is a strong Floyd-Warshall signal.
6. Guard against `INF + w` overflow.

---

## 12.14 0-1 BFS (brief)

When every weight is 0 or 1, a deque replaces the heap and you get O(V + E) instead of O((V+E) log V):

```cpp
deque<int> dq;
dq.push_front(src);
while (!dq.empty()) {
    int u = dq.front(); dq.pop_front();
    for (auto [v, w] : adj[u]) {
        if (dist[u] + w < dist[v]) {
            dist[v] = dist[u] + w;
            if (w == 0) dq.push_front(v);      // free move: front
            else        dq.push_back(v);        // costly move: back
        }
    }
}
```

Zero-weight edges go to the front (same "level"), weight-one edges to the back. **Medium priority** — it appears in grid problems where some moves are free, and knowing it exists is usually enough.

---

# PART E — MST and Union-Find

## 12.15 Disjoint Set Union (DSU)

### 1. What is it?

A structure maintaining a partition into disjoint sets, supporting "which set is `x` in?" and "merge these two sets", both in effectively O(1).

### 2. Why do we need it?

Because "are these two things already connected?" is a question BFS and DFS answer in O(V + E) **each time**, and DSU answers in near O(1) while edges are being added incrementally. It powers Kruskal, connectivity queries, cycle detection in undirected graphs, and a family of grouping problems.

### 3. Template (memorise this)

```cpp
struct DSU {
    vector<int> parent, rank_;

    DSU(int n) : parent(n), rank_(n, 0) {
        iota(parent.begin(), parent.end(), 0);       // each node is its own parent
    }

    int find(int x) {
        return parent[x] == x ? x : parent[x] = find(parent[x]);   // PATH COMPRESSION
    }

    bool unite(int a, int b) {
        a = find(a); b = find(b);
        if (a == b) return false;                    // already together
        if (rank_[a] < rank_[b]) swap(a, b);         // UNION BY RANK
        parent[b] = a;
        if (rank_[a] == rank_[b]) rank_[a]++;
        return true;
    }
};
```

Fifteen lines, worth having from memory.

### 4. The two optimisations

**Path compression** (`parent[x] = find(parent[x])`): on the way back up from a `find`, point every node directly at the root. Future lookups are then O(1).

**Union by rank** (attach the shallower tree under the deeper one): keeps trees flat so `find` never has far to walk.

Together they give **O(α(n))** amortised, where α is the inverse Ackermann function. α(n) < 5 for any n that fits in the universe, so treat it as O(1) — but know the precise answer when asked.

Without both optimisations, DSU degrades to O(n) per operation.

### 5. What DSU is good at, and not

| Good at | Not good at |
|---|---|
| "Are these connected?" | Finding an actual path |
| Incremental edge addition | **Deleting** edges |
| Counting components | Directed graphs |
| Cycle detection (undirected) | Anything needing distances |
| Grouping / merging equivalences | |

**DSU cannot un-merge.** If edges are removed over time, DSU is the wrong tool (the usual workaround is processing queries offline in reverse).

### 6. The one-liner tricks

```cpp
// Cycle detection in an undirected graph
for (auto& [u, v] : edges)
    if (!dsu.unite(u, v)) { /* cycle found: u and v were already connected */ }

// Counting components
int components = n;
for (auto& [u, v] : edges)
    if (dsu.unite(u, v)) components--;
```

### 7. Must remember

1. Path compression **and** union by rank. Both.
2. `iota` initialises each node as its own parent.
3. `unite` returns false when already connected — that is your cycle detector.
4. O(α(n)) amortised, effectively O(1).
5. Cannot delete edges.
6. Undirected only.
7. Components can be counted by decrementing on each successful union.

### 8. Practice

- Number of Connected Components (LC 323, Medium)
- Redundant Connection (LC 684, Medium) — the first edge whose `unite` fails
- Accounts Merge (LC 721, Medium) — DSU over string identities

---

## 12.16 Minimum Spanning Tree

An MST is a subset of edges connecting all vertices with minimum total weight. It has exactly `V − 1` edges and no cycles.

### Kruskal's algorithm (sort + DSU)

```cpp
long long kruskal(int n, vector<array<int,3>> edges) {    // {weight, u, v}
    sort(edges.begin(), edges.end());                      // weight ascending
    DSU dsu(n);
    long long total = 0;
    int used = 0;

    for (auto& [w, u, v] : edges) {
        if (dsu.unite(u, v)) {                             // adding it makes no cycle
            total += w;
            used++;
            if (used == n - 1) break;                      // MST complete
        }
    }
    return used == n - 1 ? total : -1;                     // -1 if disconnected
}
```

**Greedy:** take the cheapest edge that does not create a cycle. DSU is exactly the cycle test.

O(E log E) for the sort, which dominates.

### Prim's algorithm (heap)

```cpp
long long prim(int n, const vector<vector<pair<int,int>>>& adj) {
    vector<bool> inMST(n, false);
    priority_queue<pair<int,int>, vector<pair<int,int>>, greater<>> pq;  // {weight, vertex}

    pq.push({0, 0});
    long long total = 0;
    int count = 0;

    while (!pq.empty()) {
        auto [w, u] = pq.top(); pq.pop();
        if (inMST[u]) continue;                            // already in the tree

        inMST[u] = true;
        total += w;
        count++;

        for (auto [v, wt] : adj[u])
            if (!inMST[v]) pq.push({wt, v});
    }
    return count == n ? total : -1;
}
```

**Greedy:** grow one tree from a start vertex, always adding the cheapest edge that reaches a new vertex.

O((V + E) log V) with a heap. Structurally nearly identical to Dijkstra — the difference is that Prim's heap holds **edge weights** while Dijkstra's holds **accumulated distances**. Worth noticing; it is a common point of confusion.

### Kruskal or Prim?

| | Kruskal | Prim |
|---|---|---|
| Works on | Edge list | Adjacency list |
| Complexity | O(E log E) | O((V+E) log V) |
| Better for | **Sparse** graphs | **Dense** graphs |
| Needs | Sorting + DSU | Heap |
| Handles disconnected input | Gives a forest | Only reaches one component |
| Code length | Shorter (if DSU is written) | Shorter (if DSU is not) |

**Kruskal is the more common interview answer**, mostly because DSU is independently useful and interviewers like seeing it.

### Must remember

1. An MST has exactly `V − 1` edges.
2. Kruskal: sort edges, add if `unite` succeeds.
3. Prim: heap of edges crossing the frontier, skip vertices already in the tree.
4. Prim's heap holds **edge weights**; Dijkstra's holds **distances**. Not the same algorithm.
5. If fewer than `V − 1` edges are used, the graph is disconnected.
6. MSTs are not unique when weights repeat.
7. Both are greedy and both are provably correct via the **cut property**: the lightest edge crossing any cut is in some MST.

---

# PART F — Advanced topics

## 12.17 Priority classification

You asked for these to be marked clearly. Here is the honest assessment for placement preparation.

| Topic | Priority | Verdict |
|---|---|---|
| **DSU** | **Tier 1** | Essential. Covered fully above |
| **Topological sort** | **Tier 1** | Essential. Course Schedule is everywhere |
| **Dijkstra** | **Tier 2** | Common at product companies |
| **Kruskal / Prim** | **Tier 3** | Occasionally asked; know one |
| **Bellman-Ford** | **Tier 3** | Usually conceptual: "what if weights are negative?" |
| **Floyd-Warshall** | **Tier 3** | Short enough to learn; appears when n ≤ 100 |
| **0-1 BFS** | **Tier 3** | Know it exists |
| **Bridges (Tarjan)** | **Tier 4** | Rare in placements, standard in CP |
| **Articulation points** | **Tier 4** | Rare in placements |
| **SCC (Kosaraju / Tarjan)** | **Tier 4** | Rare in placements |
| **Network flow** | **Tier 4** | Skip for placements |

### What to know about the Tier 4 topics without implementing them

**Bridges.** An edge whose removal disconnects the graph. Found with DFS tracking discovery times and low-link values: edge `(u,v)` is a bridge if `low[v] > disc[u]`. O(V + E).

**Articulation points.** A vertex whose removal disconnects the graph. Same DFS, slightly different condition (`low[v] >= disc[u]` for non-root vertices; the root is an articulation point if it has more than one DFS child).

**Strongly connected components.** Maximal sets of vertices where every vertex reaches every other, in a directed graph. Kosaraju: DFS to get a finish order, reverse the graph, DFS again in that order. Tarjan does it in one pass. O(V + E).

**If asked in an interview**, naming the algorithm and its complexity is a complete answer for these. Implementing Tarjan's low-link algorithm under time pressure is not a realistic expectation at placement level, and the hours are better spent on DP.

---

# PART G — Consolidation

## 12.18 Recognition guide

| The statement says | Technique |
|---|---|
| "number of islands / regions / provinces" | DFS or BFS flood fill |
| "shortest path", unweighted | **BFS** |
| "minimum number of steps / moves / transformations" | BFS |
| "spreading", "infection", "rot", "fire" | **Multi-source BFS** |
| "distance to the nearest X for every cell" | Multi-source BFS |
| "shortest path", weighted, non-negative | **Dijkstra** |
| "cheapest / fastest route with costs" | Dijkstra |
| "at most k stops / edges" | Bellman-Ford with k+1 rounds |
| "negative weights" or "detect a negative cycle" | Bellman-Ford |
| "all pairs", n ≤ 100–400 | Floyd-Warshall |
| "prerequisites", "dependencies", "build order" | **Topological sort** |
| "can all tasks be completed" | Topological sort (cycle detection) |
| "are these two connected", edges added over time | **DSU** |
| "minimum cost to connect all X" | **MST** (Kruskal or Prim) |
| "split into two groups", "no two adjacent" | **Bipartite check** |
| "find the redundant edge" | DSU: the first failing `unite` |
| "clone / copy a graph" | DFS or BFS with a node map |
| "minimise the maximum cost along a path" | Dijkstra with `max` relaxation |

### Deciding fast

```
Is it a GRID?           -> DFS/BFS with direction arrays. Most interview graph problems.
Weighted edges?
  No  -> BFS
  Yes -> negative? -> Bellman-Ford
         all pairs & small n? -> Floyd-Warshall
         otherwise -> Dijkstra
Dependencies / ordering? -> Topological sort
Connectivity, incremental? -> DSU
Connect everything cheaply? -> MST
```

---

## 12.19 Comparison tables

### BFS vs DFS

| | BFS | DFS |
|---|---|---|
| Structure | Queue | Stack / recursion |
| Finds shortest path (unweighted) | **Yes** | No |
| Space | O(width) | O(depth) |
| Natural for | Levels, distances, spreading | Components, cycles, structure |
| Early exit | At the nearest target | Not meaningful |

### The four shortest-path algorithms

| | BFS | Dijkstra | Bellman-Ford | Floyd-Warshall |
|---|---|---|---|---|
| Weights | Unweighted | **Non-negative** | Any | Any |
| Sources | One | One | One | **All pairs** |
| Time | O(V+E) | O((V+E) log V) | O(V·E) | O(V³) |
| Space | O(V) | O(V) | O(V) | **O(V²)** |
| Negative cycles | — | — | **Detects** | Detects |
| Representation | List | List | Edge list | Matrix |

### Kruskal vs Prim vs Dijkstra

| | Kruskal | Prim | Dijkstra |
|---|---|---|---|
| Produces | MST | MST | Shortest paths |
| Heap holds | — (sorted edges) | **Edge weights** | **Distances from source** |
| Needs | DSU | Heap | Heap |
| Best for | Sparse | Dense | Any non-negative |

Prim and Dijkstra look almost identical and answer different questions. The heap contents are the tell.

### Cycle detection

| Graph | Method | Signal |
|---|---|---|
| Undirected | DFS with parent | Visited neighbour ≠ parent |
| Undirected | DSU | `unite` returns false |
| Directed | DFS, 3 states | Neighbour in state 1 |
| Directed | Kahn's | `order.size() < n` |

---

## 12.20 Must remember (consolidated)

1. Adjacency list by default. Add both directions for undirected graphs.
2. BFS marks visited at **push** time.
3. BFS gives shortest paths only in **unweighted** graphs.
4. Multi-source BFS: seed all sources at distance 0.
5. Graph DFS marks visited **permanently**; backtracking un-marks.
6. Grid problems: bounds check first, mark before recursing.
7. Undirected cycle detection uses the parent; directed uses three states.
8. Bipartite ⟺ no odd cycle.
9. Kahn's detects cycles for free: `order.size() < n`.
10. DFS topological sort is reverse postorder.
11. Check the **edge direction** in prerequisite problems.
12. Dijkstra needs non-negative weights. Have the counterexample.
13. Dijkstra needs the stale-entry check `if (d > dist[u]) continue;`.
14. Bellman-Ford: `V−1` rounds, plus one more to detect negative cycles.
15. Floyd-Warshall: **`k` outermost**.
16. DSU needs path compression **and** union by rank. Cannot delete.
17. MST has exactly `V−1` edges.
18. Prim's heap holds edge weights; Dijkstra's holds distances.
19. `INF = LLONG_MAX / 4`, never `LLONG_MAX`.
20. Loop over all vertices for disconnected graphs.

---

## 12.21 Common mistakes (consolidated)

**Wrong answer**
- Adding only one direction for an undirected edge.
- Reversed edge direction in prerequisite problems.
- Using "visited" alone for directed cycle detection.
- Omitting the parent check in undirected cycle detection.
- BFS on a weighted graph.
- Dijkstra with negative weights.
- `k` not outermost in Floyd-Warshall.
- Not looping over all components (bipartite, cycles, components).
- Off-by-one on the final minute in Rotten Oranges.
- Marking a grid cell after recursing instead of before.

**Time limit exceeded**
- Marking visited at pop time in BFS.
- Omitting the stale check in Dijkstra.
- DSU without path compression or union by rank.
- Adjacency matrix on a large sparse graph.
- Re-running BFS/DFS per query instead of using DSU.

**Runtime error / overflow**
- `INT_MAX` as infinity, overflowing on relaxation.
- Grid access before the bounds check.
- Stack overflow from recursive DFS on a large graph.
- Relaxing from an unreachable vertex in Bellman-Ford.

**Infinite loop**
- Marking a grid cell after the recursive calls.
- Flood fill where the new colour equals the old.
- Resetting `visited` in a graph traversal.

---

## 12.22 Problem set

Twenty-four problems. Grid problems are weighted heavily because interviews weight them heavily.

### Level 1 — Concept (5)

| Problem | Difficulty | Pattern | What it teaches |
|---|---|---|---|
| Number of Islands (LC 200) | Medium | Flood fill | The canonical grid graph problem |
| Flood Fill (LC 733) | Easy | DFS grid | The same-colour infinite-loop guard |
| Max Area of Island (LC 695) | Medium | DFS returning a count | `1 + sum of four calls` |
| Number of Provinces (LC 547) | Medium | Components on a matrix | Adjacency matrix input |
| Clone Graph (LC 133) | Medium | DFS with a node map | Traversal that builds as it goes |

### Level 2 — Pattern (7)

| Problem | Difficulty | Pattern | What it teaches |
|---|---|---|---|
| Rotten Oranges (LC 994) | Medium | **Multi-source BFS** | Levels as time; the three off-by-ones |
| 01 Matrix (LC 542) | Medium | Multi-source BFS | Seeding from all zeros |
| Surrounded Regions (LC 130) | Medium | Border inversion | Find what escapes, not what is trapped |
| Is Graph Bipartite (LC 785) | Medium | 2-colouring | Odd cycles; all components |
| Course Schedule (LC 207) | Medium | **Kahn's** | Cycle detection for free |
| Course Schedule II (LC 210) | Medium | Kahn's | The order itself; edge direction |
| Number of Connected Components (LC 323) | Medium | DSU or DFS | Compare both approaches |

### Level 3 — Interview (8)

| Problem | Difficulty | Pattern | What it teaches |
|---|---|---|---|
| Word Ladder (LC 127) | Hard | BFS on an implicit graph | The graph is never built |
| **Network Delay Time (LC 743)** | Medium | **Dijkstra** | The template, and `max(dist)` |
| Cheapest Flights Within K Stops (LC 787) | Medium | Bellman-Ford, k+1 rounds | Why the snapshot matters |
| Path With Minimum Effort (LC 1631) | Medium | Dijkstra with `max` relaxation | Dijkstra beyond addition |
| Redundant Connection (LC 684) | Medium | **DSU** | The first failing `unite` |
| Accounts Merge (LC 721) | Medium | DSU over strings | DSU on non-integer identities |
| Rotting/Walls variants, or Shortest Path in Binary Matrix (LC 1091) | Medium | 8-direction BFS | Direction arrays at full size |
| Detect Cycle in a Directed Graph (GFG) | Medium | 3-state DFS | Why "visited" is insufficient |

### Level 4 — Advanced (4, optional)

| Problem | Difficulty | Pattern | What it teaches |
|---|---|---|---|
| Alien Dictionary (LC 269) | Hard | Graph construction + topo sort | Building the graph is the hard part |
| Minimum Spanning Tree (GFG) | Medium | Kruskal and Prim | Write both once |
| Swim in Rising Water (LC 778) | Hard | Dijkstra / binary search + BFS | Two valid approaches |
| Floyd-Warshall (GFG) | Medium | All pairs | The `k`-outermost discipline |

**Three to over-prepare:** LC 200 (islands), LC 207/210 (course schedule), and LC 743 (Dijkstra). Those three cover the techniques that appear most often, and the rest of the module is variations on them.

**Word Ladder deserves a note.** The graph is never constructed — vertices are words, edges are one-character differences, and neighbours are generated on the fly. Recognising an implicit graph is a distinct skill from traversing an explicit one, and it is a common interview twist.

---

## Exit checklist

```
[ ] I default to adjacency lists and know when a matrix is better
[ ] I add BOTH directions for undirected edges
[ ] I mark visited at PUSH time in BFS
[ ] I know BFS gives shortest paths only when unweighted
[ ] I can write multi-source BFS from memory
[ ] I know graph DFS never un-marks visited
[ ] I can write the grid template with direction arrays from memory
[ ] I mark grid cells BEFORE recursing
[ ] I know undirected and directed cycle detection are different algorithms
[ ] I can explain why "visited" alone fails for directed cycles
[ ] I know bipartite means no odd cycle
[ ] I can write Kahn's algorithm from memory
[ ] I know order.size() < n means a cycle
[ ] I check edge direction in prerequisite problems
[ ] I can write Dijkstra with the stale-entry check from memory
[ ] I can give the negative-edge counterexample for Dijkstra
[ ] I know Bellman-Ford runs V-1 rounds plus one for detection
[ ] I know k goes OUTERMOST in Floyd-Warshall
[ ] I can write DSU with path compression and union by rank from memory
[ ] I know DSU cannot delete edges
[ ] I can write Kruskal and know Prim's heap holds edge weights
[ ] I use LLONG_MAX/4 as infinity
[ ] I can pick the right shortest-path algorithm in under 15 seconds
[ ] Level 1-3 problems solved
```

---

## Next

Say **"Start Phase 13"** for Dynamic Programming (30–35 hours, Tier 1). It is the largest module in the roadmap and the one that most separates offers from rejections at product companies.

It will not be a list of problems. The module teaches the five-step framework — define the state, define the transition, define the base cases, determine the computation order, optimise the space — and then applies it to each DP family in turn: 1D sequences, the knapsack family, strings, grids, intervals, stocks, and bitmask. The goal is that you can derive a recurrence for a problem you have never seen, rather than recognising one you have.

The groundwork is already laid: Module 4.9 showed memoisation as three lines added to a naive recursion, and Module 1.5 gave the complexity rule — states times transition cost — that lets you evaluate a DP formulation before writing any code.
