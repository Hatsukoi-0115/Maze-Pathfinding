"""迷宫生成算法的单元测试。"""

import pytest

from maze.generator import generate_dfs


def _reachable_count(maze, start):
    """从起点出发，统计通过 BFS 能到达的格子数量。"""
    from collections import deque

    seen = {start}
    queue = deque([start])
    while queue:
        current = queue.popleft()
        for neighbor in maze.passable_neighbors(*current):
            if neighbor not in seen:
                seen.add(neighbor)
                queue.append(neighbor)
    return len(seen)


class TestGenerateDFS:
    """递归回溯 DFS 生成算法的测试。"""

    def test_dimensions(self):
        """生成的迷宫行列数应与输入一致。"""
        maze = generate_dfs(9, 11)
        assert maze.rows == 9
        assert maze.cols == 11

    def test_fully_connected(self):
        """DFS 生成的迷宫应是完全连通的：所有格子都可达。"""
        maze = generate_dfs(11, 11, seed=42)
        total = maze.rows * maze.cols
        assert _reachable_count(maze, (0, 0)) == total

    def test_seed_reproducible(self):
        """相同随机种子应生成完全相同的迷宫。"""
        maze_a = generate_dfs(13, 13, seed=7)
        maze_b = generate_dfs(13, 13, seed=7)
        # 逐格比较四面墙是否一致
        for r in range(maze_a.rows):
            for c in range(maze_a.cols):
                assert maze_a.cell(r, c).walls == maze_b.cell(r, c).walls

    def test_different_seeds_differ(self):
        """不同随机种子通常应生成不同的迷宫。"""
        maze_a = generate_dfs(25, 25, seed=1)
        maze_b = generate_dfs(25, 25, seed=2)
        differs = any(
            maze_a.cell(r, c).walls != maze_b.cell(r, c).walls
            for r in range(maze_a.rows)
            for c in range(maze_a.cols)
        )
        assert differs

    def test_outer_walls_intact(self):
        """迷宫最外圈边界墙不应被拆除（保证不越界）。"""
        maze = generate_dfs(15, 15, seed=3)
        # 顶部边界
        for c in range(maze.cols):
            assert maze.cell(0, c).has_wall("N")
        # 底部边界
        for c in range(maze.cols):
            assert maze.cell(maze.rows - 1, c).has_wall("S")
        # 左边界
        for r in range(maze.rows):
            assert maze.cell(r, 0).has_wall("W")
        # 右边界
        for r in range(maze.rows):
            assert maze.cell(r, maze.cols - 1).has_wall("E")

    def test_invalid_size_raises(self):
        """非法尺寸应抛出异常。"""
        with pytest.raises(ValueError):
            generate_dfs(0, 5)
        with pytest.raises(ValueError):
            generate_dfs(5, 0)
