"""迷宫数据模型模块。

定义迷宫的基本数据结构：格子（Cell）、迷宫（Maze），
以及方向常量与墙体/边界判断逻辑，供生成、寻路、移动等模块复用。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

# 四个方向的标识常量
NORTH = "N"
SOUTH = "S"
EAST = "E"
WEST = "W"

# 方向对应的（行偏移，列偏移）
DIRECTIONS: Dict[str, Tuple[int, int]] = {
    NORTH: (-1, 0),
    SOUTH: (1, 0),
    EAST: (0, 1),
    WEST: (0, -1),
}

# 相反方向映射，用于打通相邻格子之间的墙
OPPOSITE: Dict[str, str] = {
    NORTH: SOUTH,
    SOUTH: NORTH,
    EAST: WEST,
    WEST: EAST,
}

# 表示坐标位置的类型别名
Position = Tuple[int, int]


@dataclass
class Cell:
    """迷宫中的单个格子。

    属性:
        row: 格子所在行。
        col: 格子所在列。
        walls: 四面墙是否存在，键为方向（N/S/E/W），值为 True 表示有墙。
    """

    row: int
    col: int
    walls: Dict[str, bool]

    def has_wall(self, direction: str) -> bool:
        """判断指定方向是否存在墙。"""
        return self.walls[direction]

    def remove_wall(self, direction: str) -> None:
        """拆除指定方向的墙。"""
        self.walls[direction] = False


class Maze:
    """迷宫数据结构。

    采用“格子 + 墙”的表示法：每个格子记录自身四面墙是否存在。
    初始状态所有墙都存在（完全封闭），由生成算法逐步拆墙形成通道。
    """

    def __init__(self, rows: int, cols: int) -> None:
        """初始化一个 rows 行、cols 列的封闭迷宫。"""
        if rows < 1 or cols < 1:
            raise ValueError("迷宫行列数必须为正整数")

        self.rows = rows
        self.cols = cols
        # 二维网格，每个格子初始四面都有墙
        self.grid: List[List[Cell]] = [
            [Cell(r, c, {d: True for d in DIRECTIONS}) for c in range(cols)]
            for r in range(rows)
        ]

    def cell(self, row: int, col: int) -> Cell:
        """返回指定坐标的格子。"""
        return self.grid[row][col]

    def in_bounds(self, row: int, col: int) -> bool:
        """判断坐标是否在迷宫范围内（边界判断）。"""
        return 0 <= row < self.rows and 0 <= col < self.cols

    def neighbors(self, row: int, col: int) -> List[Tuple[str, int, int]]:
        """返回上下左右四个方向中未越界的邻居，形如 (方向, 行, 列)。"""
        result: List[Tuple[str, int, int]] = []
        for direction, (dr, dc) in DIRECTIONS.items():
            nr, nc = row + dr, col + dc
            if self.in_bounds(nr, nc):
                result.append((direction, nr, nc))
        return result

    def remove_wall_between(self, row: int, col: int, direction: str) -> None:
        """拆掉当前格子指定方向的墙，并同步拆掉相邻格子反向的墙。

        保证两个相邻格子之间的“通道”双向贯通，避免出现单面墙的不一致状态。
        """
        dr, dc = DIRECTIONS[direction]
        nr, nc = row + dr, col + dc
        if not self.in_bounds(nr, nc):
            raise ValueError(f"方向 {direction} 处越界，无法拆墙")

        self.cell(row, col).remove_wall(direction)
        self.cell(nr, nc).remove_wall(OPPOSITE[direction])

    def can_pass(self, row: int, col: int, direction: str) -> bool:
        """判断从当前格子能否沿指定方向通行（无墙且未越界）。"""
        dr, dc = DIRECTIONS[direction]
        nr, nc = row + dr, col + dc
        if not self.in_bounds(nr, nc):
            return False
        return not self.cell(row, col).has_wall(direction)

    def passable_neighbors(self, row: int, col: int) -> List[Position]:
        """返回当前格子所有可通过（无墙阻隔）的相邻坐标。"""
        result: List[Position] = []
        for direction, (dr, dc) in DIRECTIONS.items():
            nr, nc = row + dr, col + dc
            if self.in_bounds(nr, nc) and not self.cell(row, col).has_wall(direction):
                result.append((nr, nc))
        return result
