"""程序入口模块。

启动迷宫生成与寻路可视化程序。
"""

import argparse

from app.game import MazeGame


def parse_args() -> argparse.Namespace:
    """解析命令行参数。"""
    parser = argparse.ArgumentParser(description="迷宫生成与寻路可视化")
    parser.add_argument("--rows", type=int, default=21, help="迷宫行数（默认 21，建议为奇数）")
    parser.add_argument("--cols", type=int, default=21, help="迷宫列数（默认 21，建议为奇数）")
    parser.add_argument("--cell", type=int, default=26, help="每个格子的像素大小（默认 26）")
    return parser.parse_args()


def main() -> None:
    """程序入口函数。"""
    args = parse_args()
    game = MazeGame(rows=args.rows, cols=args.cols, cell_size=args.cell)
    game.run()


if __name__ == "__main__":
    main()
