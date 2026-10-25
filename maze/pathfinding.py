"""寻路模块。

实现广度优先搜索（BFS）与 A* 两种寻路算法：
- BFS：保证在无权图中找到最短路径。
- A*：使用曼哈顿距离作为启发函数，通常比 BFS 访问更少节点。

两种算法均返回统一的结果对象 PathResult，包含路径、访问节点数与耗时，
便于在界面中对比展示。
"""

from __future__ import annotations

import heapq
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Callable, List, Optional, Set, Tuple

from maze.maze import DIRECTIONS, Maze, Position


@dataclass
class PathResult:
    """寻路结果。

    属性:
        found: 是否找到可达路径。
        path: 从起点到终点的坐标序列（含起终点），未找到时为空列表。
        visited: 搜索过程中访问过的所有坐标集合（用于可视化）。
        visited_count: 访问节点数。
        elapsed_ms: 寻路耗时（毫秒）。
    """

    found: bool
    path: List[Position] = field(default_factory=list)
    visited: Set[Position] = field(default_factory=set)
    visited_count: int = 0
    elapsed_ms: float = 0.0

    @property
    def length(self) -> int:
        """路径长度（步数），未找到时为 0。"""
        return len(self.path) - 1 if self.found and self.path else 0


def _reconstruct_path(parent: dict, start: Position, goal: Position) -> List[Position]:
    """根据父节点映射回溯出从起点到终点的完整路径。"""
    path: List[Position] = [goal]
    current = goal
    while current != start:
        current = parent[current]
        path.append(current)
    path.reverse()
    return path


def _heuristic(a: Position, b: Position) -> int:
    """曼哈顿距离启发函数，用于 A* 算法估计剩余代价。"""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def bfs(maze: Maze, start: Position, goal: Position) -> PathResult:
    """广度优先搜索（BFS）寻路。

    使用队列逐层扩展，在无权图中保证找到从起点到终点的最短路径。
    """
    if not maze.in_bounds(*start) or not maze.in_bounds(*goal):
        return PathResult(found=False)

    begin = time.perf_counter()
    queue = deque([start])
    visited: Set[Position] = {start}
    parent: dict = {start: None}

    while queue:
        current = queue.popleft()
        if current == goal:
            path = _reconstruct_path(parent, start, goal)
            return PathResult(
                found=True,
                path=path,
                visited=visited,
                visited_count=len(visited),
                elapsed_ms=(time.perf_counter() - begin) * 1000,
            )

        # 仅扩展无墙阻隔且未访问过的邻居
        for neighbor in maze.passable_neighbors(*current):
            if neighbor not in visited:
                visited.add(neighbor)
                parent[neighbor] = current
                queue.append(neighbor)

    # 队列耗尽仍未找到终点，说明无法寻路
    return PathResult(
        found=False,
        visited=visited,
        visited_count=len(visited),
        elapsed_ms=(time.perf_counter() - begin) * 1000,
    )


def astar(maze: Maze, start: Position, goal: Position) -> PathResult:
    """A* 寻路算法。

    使用“已走代价 + 曼哈顿距离启发值”作为优先级，
    优先扩展更可能通往终点的节点，通常比 BFS 访问更少节点。
    """
    if not maze.in_bounds(*start) or not maze.in_bounds(*goal):
        return PathResult(found=False)

    begin = time.perf_counter()
    # 优先队列元素为 (优先级, 已走代价, 坐标)
    open_heap: List[Tuple[int, int, Position]] = [(0, 0, start)]
    came_from: dict = {start: None}
    g_score: dict = {start: 0}
    visited: Set[Position] = set()

    while open_heap:
        _, g, current = heapq.heappop(open_heap)
        visited.add(current)

        if current == goal:
            path = _reconstruct_path(came_from, start, goal)
            return PathResult(
                found=True,
                path=path,
                visited=visited,
                visited_count=len(visited),
                elapsed_ms=(time.perf_counter() - begin) * 1000,
            )

        for neighbor in maze.passable_neighbors(*current):
            tentative_g = g + 1
            if neighbor not in g_score or tentative_g < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                priority = tentative_g + _heuristic(neighbor, goal)
                heapq.heappush(open_heap, (priority, tentative_g, neighbor))

    return PathResult(
        found=False,
        visited=visited,
        visited_count=len(visited),
        elapsed_ms=(time.perf_counter() - begin) * 1000,
    )


# 算法名称到实现函数的映射，供统一入口选择
_ALGORITHMS: dict[str, Callable[[Maze, Position, Position], PathResult]] = {
    "bfs": bfs,
    "astar": astar,
}


def find_path(
    maze: Maze, start: Position, goal: Position, algorithm: str = "bfs"
) -> PathResult:
    """统一寻路入口，根据算法名称调度 BFS 或 A*。"""
    if algorithm not in _ALGORITHMS:
        raise ValueError(f"未知的寻路算法: {algorithm}")
    return _ALGORITHMS[algorithm](maze, start, goal)
