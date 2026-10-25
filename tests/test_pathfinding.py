"""寻路算法（BFS 与 A*）的单元测试。"""

import pytest

from maze import Maze, bfs, astar, find_path
from maze.generator import generate_dfs


def _assert_valid_path(maze, start, goal, path):
    """断言路径合法：起终点正确，且每一步都通过无墙的通道相邻。"""
    assert path[0] == start
    assert path[-1] == goal
    for a, b in zip(path, path[1:]):
        assert b in maze.passable_neighbors(*a)


class TestBFS:
    """BFS 寻路测试。"""

    def test_finds_path(self):
        maze = generate_dfs(11, 11, seed=5)
        start, goal = (0, 0), (10, 10)
        result = bfs(maze, start, goal)
        assert result.found
        _assert_valid_path(maze, start, goal, result.path)

    def test_path_length_is_shortest(self):
        """BFS 应返回最短路径：路径长度等于最优步数。"""
        maze = generate_dfs(13, 13, seed=8)
        start, goal = (0, 0), (12, 12)
        result = bfs(maze, start, goal)
        assert result.found
        # 步数 = 路径节点数 - 1
        assert result.length == len(result.path) - 1

    def test_no_path_when_goal_isolated(self):
        """终点被墙完全隔离时，BFS 应返回无法寻路。"""
        maze = Maze(2, 2)
        # 打通 (0,0) 与 (0,1)、(1,0) 的通道，但 (1,1) 保持完全封闭
        maze.remove_wall_between(0, 0, "E")
        maze.remove_wall_between(0, 0, "S")
        result = bfs(maze, (0, 0), (1, 1))
        assert not result.found
        assert result.path == []


class TestAStar:
    """A* 寻路测试。"""

    def test_finds_path(self):
        maze = generate_dfs(11, 11, seed=5)
        start, goal = (0, 0), (10, 10)
        result = astar(maze, start, goal)
        assert result.found
        _assert_valid_path(maze, start, goal, result.path)

    def test_same_shortest_length_as_bfs(self):
        """A* 找到的路径长度应与 BFS（最短路径）一致。"""
        for seed in range(20):
            maze = generate_dfs(17, 17, seed=seed)
            start, goal = (0, 0), (16, 16)
            bfs_result = bfs(maze, start, goal)
            astar_result = astar(maze, start, goal)
            assert bfs_result.found
            assert astar_result.found
            assert astar_result.length == bfs_result.length


class TestFindPath:
    """统一寻路入口测试。"""

    def test_unknown_algorithm_raises(self):
        """未知算法名称应抛出异常。"""
        maze = generate_dfs(5, 5, seed=1)
        with pytest.raises(ValueError):
            find_path(maze, (0, 0), (4, 4), "dijkstra")

    def test_returns_path_result(self):
        """统一入口应能正常返回结果对象。"""
        maze = generate_dfs(9, 9, seed=2)
        result = find_path(maze, (0, 0), (8, 8), "bfs")
        assert result.found
        assert result.path[0] == (0, 0)
        assert result.path[-1] == (8, 8)
