"""迷宫核心逻辑包。

包含迷宫数据模型、迷宫生成、寻路算法与玩家移动逻辑，
全部为纯 Python 实现，不依赖图形界面，便于单元测试与复用。
"""

from maze.maze import (
    Maze,
    Cell,
    DIRECTIONS,
    OPPOSITE,
    NORTH,
    SOUTH,
    EAST,
    WEST,
)
from maze.generator import generate_dfs
from maze.pathfinding import bfs, astar, find_path, PathResult
from maze.player import Player

__all__ = [
    "Maze",
    "Cell",
    "DIRECTIONS",
    "OPPOSITE",
    "NORTH",
    "SOUTH",
    "EAST",
    "WEST",
    "generate_dfs",
    "bfs",
    "astar",
    "find_path",
    "PathResult",
    "Player",
]
