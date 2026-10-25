"""迷宫生成模块。

实现基于递归回溯（Recursive Backtracking / DFS）的随机迷宫生成算法。
算法生成的迷宫具有“完全连通”的特性：任意两个格子之间都存在唯一可达路径。
"""

from __future__ import annotations

import random
from typing import Optional

from maze.maze import DIRECTIONS, Maze


def generate_dfs(rows: int, cols: int, seed: Optional[int] = None) -> Maze:
    """使用递归回溯算法生成一个随机迷宫。

    参数:
        rows: 迷宫行数。
        cols: 迷宫列数。
        seed: 随机种子，传入相同种子可复现相同的迷宫（便于测试）。

    返回:
        一个完全连通的迷宫实例。
    """
    if rows < 1 or cols < 1:
        raise ValueError("迷宫行列数必须为正整数")

    maze = Maze(rows, cols)
    rng = random.Random(seed)

    # 记录每个格子是否已被访问过
    visited = [[False] * cols for _ in range(rows)]
    # 使用显式栈替代递归，避免大规模迷宫导致递归深度超限
    stack = [(0, 0)]
    visited[0][0] = True

    while stack:
        r, c = stack[-1]

        # 收集当前格子周围尚未访问的邻居
        unvisited = []
        for direction, (dr, dc) in DIRECTIONS.items():
            nr, nc = r + dr, c + dc
            if maze.in_bounds(nr, nc) and not visited[nr][nc]:
                unvisited.append((direction, nr, nc))

        if not unvisited:
            # 当前格子无未访问邻居，回溯到上一个格子
            stack.pop()
            continue

        # 随机选择一个未访问邻居，打通两者之间的墙
        direction, nr, nc = rng.choice(unvisited)
        maze.remove_wall_between(r, c, direction)
        visited[nr][nc] = True
        stack.append((nr, nc))

    return maze
