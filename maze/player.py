"""玩家模块。

封装玩家在迷宫中的位置与手动移动逻辑，
并对撞墙、越界等非法移动进行判断与提示。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from maze.maze import DIRECTIONS, Maze, Position


@dataclass
class MoveResult:
    """单次移动的结果。

    属性:
        success: 是否移动成功。
        reason: 移动失败时的原因说明（成功时为空字符串）。
        position: 移动后的位置。
    """

    success: bool
    reason: str
    position: Position


class Player:
    """迷宫中的玩家角色。

    负责记录当前位置，并在移动时进行合法性判断：
    角色不得穿墙、不得越界。
    """

    def __init__(self, start: Position) -> None:
        """以指定起点初始化玩家位置。"""
        self.row, self.col = start

    @property
    def position(self) -> Position:
        """返回玩家当前位置坐标。"""
        return (self.row, self.col)

    def move(self, maze: Maze, direction: str) -> MoveResult:
        """尝试沿指定方向移动一步。

        参数:
            maze: 当前所在的迷宫。
            direction: 移动方向（N/S/E/W）。

        返回:
            MoveResult，包含是否成功、失败原因与移动后的位置。
        """
        if direction not in DIRECTIONS:
            return MoveResult(False, "无效的方向", self.position)

        dr, dc = DIRECTIONS[direction]
        nr, nc = self.row + dr, self.col + dc

        # 越界判断：目标位置必须在迷宫范围内
        if not maze.in_bounds(nr, nc):
            return MoveResult(False, "越界：无法走出迷宫边界", self.position)

        # 撞墙判断：目标方向存在墙时禁止通行
        if maze.cell(self.row, self.col).has_wall(direction):
            return MoveResult(False, "撞墙：此方向有墙体阻挡", self.position)

        # 合法移动：更新位置
        self.row, self.col = nr, nc
        return MoveResult(True, "", self.position)

    def teleport(self, position: Position) -> None:
        """将玩家直接传送到指定坐标（用于寻路动画等场景）。"""
        self.row, self.col = position
