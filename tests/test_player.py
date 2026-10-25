"""玩家移动与合法性判断的单元测试。"""

import pytest

from maze import Maze, Player


def _open_path(maze, cells):
    """按顺序打通一串相邻格子之间的墙，构造可控的迷宫通道。"""
    for a, b in zip(cells, cells[1:]):
        ar, ac = a
        br, bc = b
        if br == ar - 1:
            maze.remove_wall_between(ar, ac, "N")
        elif br == ar + 1:
            maze.remove_wall_between(ar, ac, "S")
        elif bc == ac + 1:
            maze.remove_wall_between(ar, ac, "E")
        elif bc == ac - 1:
            maze.remove_wall_between(ar, ac, "W")


class TestPlayerMovement:
    """玩家移动合法性测试。"""

    def test_valid_move(self):
        """沿已打通的方向移动应成功，并更新位置。"""
        maze = Maze(2, 2)
        maze.remove_wall_between(0, 0, "E")  # (0,0) -> (0,1)
        player = Player((0, 0))
        result = player.move(maze, "E")
        assert result.success
        assert player.position == (0, 1)

    def test_wall_move_blocked(self):
        """撞墙时移动应失败，位置保持不变。"""
        maze = Maze(2, 2)  # 完全封闭，无任何通道
        player = Player((0, 0))
        result = player.move(maze, "E")
        assert not result.success
        assert "撞墙" in result.reason
        assert player.position == (0, 0)

    def test_out_of_bounds_blocked(self):
        """越界移动应失败，位置保持不变。"""
        maze = Maze(2, 2)
        player = Player((0, 0))
        result = player.move(maze, "N")  # 向上会越界
        assert not result.success
        assert "越界" in result.reason
        assert player.position == (0, 0)

    def test_invalid_direction(self):
        """无效方向应返回失败。"""
        maze = Maze(3, 3)
        player = Player((0, 0))
        result = player.move(maze, "X")
        assert not result.success

    def test_reach_goal_through_corridor(self):
        """玩家可沿通道从起点走到终点。"""
        maze = Maze(3, 3)
        path = [(0, 0), (0, 1), (0, 2), (1, 2), (2, 2)]
        _open_path(maze, path)
        player = Player((0, 0))
        for a, b in zip(path, path[1:]):
            direction = None
            if b[0] == a[0] - 1:
                direction = "N"
            elif b[0] == a[0] + 1:
                direction = "S"
            elif b[1] == a[1] + 1:
                direction = "E"
            elif b[1] == a[1] - 1:
                direction = "W"
            assert direction is not None
            result = player.move(maze, direction)
            assert result.success
        assert player.position == (2, 2)

    def test_teleport(self):
        """传送应直接改变玩家位置。"""
        player = Player((0, 0))
        player.teleport((4, 4))
        assert player.position == (4, 4)
