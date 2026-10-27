"""pygame 图形界面模块。

负责迷宫渲染、键盘/按钮交互、寻路可视化与统计信息展示。
图形界面与核心逻辑（maze 包）解耦，核心逻辑可独立测试。
"""

from __future__ import annotations

import sys
from typing import Callable, List, Optional, Tuple

import pygame

from maze import DIRECTIONS, EAST, NORTH, SOUTH, WEST, Maze, Player, find_path, generate_dfs
from maze.pathfinding import PathResult

# ---------------------------------------------------------------------------
# 颜色常量
# ---------------------------------------------------------------------------
BG_COLOR = (24, 26, 30)            # 窗口背景色
MAZE_BG = (40, 44, 52)             # 迷宫格子底色
WALL_COLOR = (220, 224, 232)       # 墙体颜色
VISITED_COLOR = (58, 96, 138)      # 已访问节点颜色
PATH_COLOR = (240, 196, 66)        # 寻路路径颜色
START_COLOR = (72, 190, 100)       # 起点颜色
GOAL_COLOR = (230, 80, 90)         # 终点颜色
PLAYER_COLOR = (80, 170, 255)      # 玩家颜色
PANEL_COLOR = (33, 36, 44)         # 侧边栏底色
TEXT_COLOR = (235, 238, 244)       # 正文文字颜色
MUTED_COLOR = (150, 158, 170)      # 次要文字颜色
MESSAGE_COLOR = (255, 210, 90)     # 提示信息颜色
BUTTON_BG = (56, 62, 76)           # 按钮背景色
BUTTON_HOVER = (74, 82, 100)       # 按钮悬停色
BUTTON_BORDER = (110, 120, 140)    # 按钮边框色
SCROLLBAR_TRACK_COLOR = (45, 49, 58)      # 滚动条轨道颜色
SCROLLBAR_THUMB_COLOR = (110, 120, 140)   # 滚动条滑块颜色
SCROLLBAR_WIDTH = 8                        # 滚动条宽度（像素）

# 键盘按键到移动方向的映射（方向键 + WASD）
KEY_TO_DIRECTION = {
    pygame.K_UP: NORTH,
    pygame.K_w: NORTH,
    pygame.K_DOWN: SOUTH,
    pygame.K_s: SOUTH,
    pygame.K_RIGHT: EAST,
    pygame.K_d: EAST,
    pygame.K_LEFT: WEST,
    pygame.K_a: WEST,
}


def _load_font(size: int) -> pygame.font.Font:
    """加载支持中文的字体，找不到时回退到默认字体。"""
    # 依次尝试常见的中文字体
    candidates = ["microsoftyahei", "simhei", "simsun", "notosanscjksc", "arial"]
    for name in candidates:
        path = pygame.font.match_font(name)
        if path:
            return pygame.font.Font(path, size)
    return pygame.font.Font(None, size)


class Button:
    """可点击的界面按钮。"""

    def __init__(
        self,
        rect: pygame.Rect,
        text: str,
        font: pygame.font.Font,
        action: Callable[[], None],
    ) -> None:
        self.rect = rect
        self.text = text
        self.font = font
        self.action = action

    def draw(self, surface: pygame.Surface, screen_rect: pygame.Rect, mouse_pos: Tuple[int, int]) -> None:
        """在指定屏幕矩形上绘制按钮，并根据鼠标位置显示悬停效果。"""
        hovered = screen_rect.collidepoint(mouse_pos)
        bg = BUTTON_HOVER if hovered else BUTTON_BG
        pygame.draw.rect(surface, bg, screen_rect, border_radius=6)
        pygame.draw.rect(surface, BUTTON_BORDER, screen_rect, width=1, border_radius=6)
        label = self.font.render(self.text, True, TEXT_COLOR)
        surface.blit(label, label.get_rect(center=screen_rect.center))

    def is_clicked(self, pos: Tuple[int, int]) -> bool:
        """判断鼠标点击位置是否落在按钮上。"""
        return self.rect.collidepoint(pos)


class MazeGame:
    """迷宫游戏主类，负责窗口、事件循环、渲染与交互。"""

    def __init__(self, rows: int = 21, cols: int = 21, cell_size: int = 26) -> None:
        """初始化游戏窗口与状态。

        参数:
            rows: 迷宫行数（建议为奇数，起点在左上角）。
            cols: 迷宫列数。
            cell_size: 每个格子的像素大小。
        """
        if rows < 3 or cols < 3:
            raise ValueError("迷宫行列数至少为 3")

        self.rows = rows
        self.cols = cols
        self.cell_size = cell_size

        # 界面布局常量
        self.margin = 20
        self.panel_width = 260
        self.maze_size = (cols * cell_size, rows * cell_size)
        self.window_width = self.margin * 2 + self.maze_size[0] + self.panel_width
        self.window_height = self.margin * 2 + self.maze_size[1]
        self.maze_offset = (self.margin, self.margin)

        pygame.init()
        self.surface = pygame.display.set_mode((self.window_width, self.window_height))
        pygame.display.set_caption("迷宫生成与寻路可视化")

        # 字体
        self.font_small = _load_font(16)
        self.font_normal = _load_font(20)
        self.font_title = _load_font(24)

        # 侧边栏滚动状态
        self.panel_scroll = 0.0          # 当前滚动偏移（像素）
        self.panel_content_height = 0    # 侧边栏内容总高度
        self._panel_message_y = 0        # 提示信息起始 y 坐标（内容坐标）
        self._dragging_scrollbar = False # 是否正在拖动滚动条
        self._scrollbar_drag_last_y = 0  # 拖动滚动条时的上一个鼠标 y 坐标

        # 初始化一局新游戏
        self.reset()

    # ------------------------------------------------------------------
    # 状态管理
    # ------------------------------------------------------------------
    def reset(self) -> None:
        """生成新迷宫并重置玩家、路径与统计信息。"""
        self.maze: Maze = generate_dfs(self.rows, self.cols)
        self.start = (0, 0)
        self.goal = (self.rows - 1, self.cols - 1)
        self.player = Player(self.start)

        self.path: List[Tuple[int, int]] = []
        self.visited = set()
        self.stats: Optional[PathResult] = None
        self.message = "使用方向键/WASD 移动，点击按钮自动寻路"
        self.stop_animation()

    def stop_animation(self) -> None:
        """停止寻路路径动画。"""
        self.animating = False
        self.anim_path: List[Tuple[int, int]] = []
        self.anim_index = 0
        self.anim_timer = 0.0

    def clear_path(self) -> None:
        """清除已显示的路径与统计信息。"""
        self.path = []
        self.visited = set()
        self.stats = None

    # ------------------------------------------------------------------
    # 交互动作
    # ------------------------------------------------------------------
    def handle_move(self, direction: str) -> None:
        """处理玩家手动移动，并进行撞墙/越界判断。"""
        if self.animating:
            self.stop_animation()

        result = self.player.move(self.maze, direction)
        if result.success:
            # 手动移动成功后清除旧路径显示
            self.clear_path()
            if self.player.position == self.goal:
                self.message = "恭喜！你成功到达了终点！"
            else:
                self.message = ""
        else:
            self.message = result.reason

    def run_pathfinding(self, algorithm: str) -> None:
        """执行指定算法寻路并启动路径动画。"""
        self.stop_animation()
        result = find_path(self.maze, self.start, self.goal, algorithm)

        name = "BFS" if algorithm == "bfs" else "A*"
        if result.found:
            self.path = result.path
            self.visited = result.visited
            self.stats = result
            self.message = (
                f"{name} 找到路径：长度 {result.length} 步，"
                f"访问 {result.visited_count} 节点，耗时 {result.elapsed_ms:.2f} ms"
            )
            self._start_animation(result.path)
        else:
            # 无法寻路的异常场景处理
            self.path = []
            self.visited = result.visited
            self.stats = result
            self.message = f"{name} 无法寻路：终点不可达"

    def _start_animation(self, path: List[Tuple[int, int]]) -> None:
        """启动玩家沿路径自动行走的动画。"""
        self.anim_path = path
        self.anim_index = 0
        self.anim_timer = 0.0
        self.animating = True
        self.player.teleport(path[0])

    def update_animation(self, dt_ms: float) -> None:
        """根据帧间隔推进路径动画，让玩家逐格走向终点。"""
        if not self.animating:
            return

        # 每步动画间隔（毫秒）
        step_interval = 40.0
        self.anim_timer += dt_ms

        while self.animating and self.anim_timer >= step_interval:
            self.anim_timer -= step_interval
            self.anim_index += 1
            if self.anim_index >= len(self.anim_path):
                # 动画结束，玩家停在终点
                self.animating = False
                self.player.teleport(self.anim_path[-1])
            else:
                self.player.teleport(self.anim_path[self.anim_index])

    # ------------------------------------------------------------------
    # 事件处理
    # ------------------------------------------------------------------
    def handle_key(self, key: int) -> None:
        """处理键盘按键事件。"""
        if key in KEY_TO_DIRECTION:
            self.handle_move(KEY_TO_DIRECTION[key])
        elif key == pygame.K_r:
            self.reset()
        elif key == pygame.K_1:
            self.run_pathfinding("bfs")
        elif key == pygame.K_2:
            self.run_pathfinding("astar")
        elif key == pygame.K_c:
            self.stop_animation()
            self.clear_path()
            self.message = "已清除路径"

    def handle_click(self, pos: Tuple[int, int]) -> None:
        """处理鼠标左键点击：优先处理滚动条，其次触发按钮动作。"""
        panel = self._panel_rect()
        self._layout_panel()
        self._clamp_scroll()

        # 若内容溢出，先判断是否点击了滚动条（滑块或轨道）
        if self._max_scroll() > 0:
            track, thumb = self._scrollbar_metrics(panel)
            if thumb.collidepoint(pos) or track.collidepoint(pos):
                self._dragging_scrollbar = True
                self._scrollbar_drag_last_y = pos[1]
                if track.collidepoint(pos) and not thumb.collidepoint(pos):
                    # 点击轨道空白处：让滑块跳转到点击位置
                    self._scroll_to_thumb_center(pos[1])
                return

        # 将屏幕坐标转换为内容坐标（补偿滚动偏移）后再命中按钮
        content_pos = (pos[0], pos[1] + int(self.panel_scroll))
        for button in self._build_buttons():
            if button.is_clicked(content_pos):
                button.action()
                break

    def handle_wheel(self, event) -> None:
        """处理鼠标滚轮事件：仅当鼠标悬停在侧边栏内时滚动内容。"""
        if self._panel_rect().collidepoint(pygame.mouse.get_pos()):
            # 向上滚动（event.y > 0）时内容上移，即滚动偏移减小
            self.panel_scroll -= event.y * 40
            self._clamp_scroll()

    def handle_drag_scroll(self, pos: Tuple[int, int]) -> None:
        """处理滚动条拖动：根据鼠标纵向位移同步更新滚动位置。"""
        if not self._dragging_scrollbar:
            return
        track, thumb = self._scrollbar_metrics(self._panel_rect())
        max_scroll = self._max_scroll()
        if max_scroll <= 0:
            return

        dy = pos[1] - self._scrollbar_drag_last_y
        self._scrollbar_drag_last_y = pos[1]
        # 像素位移与滚动位移成正比（滑块可移动范围对应滚动范围）
        scroll_per_px = max_scroll / (track.height - thumb.height)
        self.panel_scroll += dy * scroll_per_px
        self._clamp_scroll()

    def _scroll_to_thumb_center(self, y: int) -> None:
        """将滑块中心移动到指定纵向坐标，并同步更新滚动位置。"""
        track, thumb = self._scrollbar_metrics(self._panel_rect())
        max_scroll = self._max_scroll()
        if max_scroll <= 0:
            self.panel_scroll = 0.0
            return
        target_top = y - thumb.height / 2
        ratio = (target_top - track.top) / (track.height - thumb.height)
        ratio = max(0.0, min(1.0, ratio))
        self.panel_scroll = ratio * max_scroll

    # ------------------------------------------------------------------
    # 渲染
    # ------------------------------------------------------------------
    def cell_rect(self, row: int, col: int) -> pygame.Rect:
        """返回某个格子的像素矩形区域。"""
        x = self.maze_offset[0] + col * self.cell_size
        y = self.maze_offset[1] + row * self.cell_size
        return pygame.Rect(x, y, self.cell_size, self.cell_size)

    def draw(self) -> None:
        """绘制完整画面（迷宫 + 侧边栏）。"""
        self.surface.fill(BG_COLOR)
        self._draw_maze()
        self._draw_panel()
        pygame.display.flip()

    def _draw_maze(self) -> None:
        """绘制迷宫：底色、访问节点、路径、起终点、玩家与墙体。"""
        # 先绘制格子底色
        for r in range(self.rows):
            for c in range(self.cols):
                pygame.draw.rect(self.surface, MAZE_BG, self.cell_rect(r, c))

        # 绘制已访问节点（寻路搜索过程可视化）
        for pos in self.visited:
            if pos not in self.path:  # 路径节点单独高亮，避免被覆盖
                pygame.draw.rect(self.surface, VISITED_COLOR, self.cell_rect(*pos))

        # 绘制路径
        for pos in self.path:
            pygame.draw.rect(self.surface, PATH_COLOR, self.cell_rect(*pos))

        # 起点与终点标记
        pygame.draw.rect(self.surface, START_COLOR, self.cell_rect(*self.start), width=3)
        goal_rect = self.cell_rect(*self.goal)
        pygame.draw.rect(self.surface, GOAL_COLOR, goal_rect, width=3)
        pygame.draw.circle(self.surface, GOAL_COLOR, goal_rect.center, self.cell_size // 4)

        # 玩家
        player_rect = self.cell_rect(*self.player.position)
        pygame.draw.circle(
            self.surface,
            PLAYER_COLOR,
            player_rect.center,
            self.cell_size // 2 - 4,
        )

        # 绘制墙体（最后绘制以覆盖格子边缘，保证墙体清晰）
        for r in range(self.rows):
            for c in range(self.cols):
                x = self.maze_offset[0] + c * self.cell_size
                y = self.maze_offset[1] + r * self.cell_size
                cell = self.maze.cell(r, c)
                if cell.has_wall(NORTH):
                    pygame.draw.line(self.surface, WALL_COLOR, (x, y), (x + self.cell_size, y), 2)
                if cell.has_wall(WEST):
                    pygame.draw.line(self.surface, WALL_COLOR, (x, y), (x, y + self.cell_size), 2)
                if cell.has_wall(SOUTH):
                    pygame.draw.line(self.surface, WALL_COLOR, (x, y + self.cell_size), (x + self.cell_size, y + self.cell_size), 2)
                if cell.has_wall(EAST):
                    pygame.draw.line(self.surface, WALL_COLOR, (x + self.cell_size, y), (x + self.cell_size, y + self.cell_size), 2)

    def _panel_rect(self) -> pygame.Rect:
        """返回侧边栏面板在屏幕上的矩形区域。"""
        return pygame.Rect(
            self.margin + self.maze_size[0],
            self.margin,
            self.panel_width - self.margin,
            self.maze_size[1],
        )

    def _layout_panel(self) -> None:
        """布局侧边栏内容：设置各按钮的内容坐标并计算内容总高度。"""
        panel = self._panel_rect()
        x = panel.x + 16
        y = panel.y + 16
        inner_w = panel.width - 32
        line_gap = 28

        # 标题占位高度
        y += 40
        # 基础信息（2 行）
        y += line_gap * 2
        y += 8
        # 寻路统计信息（最多 5 行）
        if self.stats is not None:
            y += line_gap * 5
            y += 8

        # 操作按钮（按钮 rect 保存内容坐标，绘制时再减去滚动偏移）
        button_h = 34
        button_gap = 10
        for button in self._build_buttons():
            button.rect.update(x, y, inner_w, button_h)
            y += button_h + button_gap

        # 底部提示信息
        y += 6
        self._panel_message_y = y
        y += 22 * len(self._wrap_text(self.message, inner_w))

        self.panel_content_height = y - panel.y

    def _max_scroll(self) -> float:
        """返回可滚动的最大偏移量（内容超出面板的部分）。"""
        return max(0.0, self.panel_content_height - self._panel_rect().height)

    def _clamp_scroll(self) -> None:
        """将滚动偏移限制在合法范围内。"""
        self.panel_scroll = max(0.0, min(self.panel_scroll, self._max_scroll()))

    def _scrollbar_metrics(self, panel: pygame.Rect) -> Tuple[pygame.Rect, pygame.Rect]:
        """根据当前滚动状态计算滚动条的轨道与滑块矩形。"""
        track = pygame.Rect(
            panel.right - SCROLLBAR_WIDTH - 4,
            panel.top + 4,
            SCROLLBAR_WIDTH,
            panel.height - 8,
        )
        view = panel.height
        # 滑块高度与可视比例成正比，但保留最小可抓取高度
        thumb_h = max(20, int(view * view / self.panel_content_height))
        max_scroll = self._max_scroll()
        thumb_y = track.top
        if max_scroll > 0:
            thumb_y = track.top + int(
                (self.panel_scroll / max_scroll) * (track.height - thumb_h)
            )
        thumb = pygame.Rect(track.x, thumb_y, SCROLLBAR_WIDTH, thumb_h)
        return track, thumb

    def _draw_panel(self) -> None:
        """绘制右侧侧边栏：标题、统计信息、提示、操作按钮与滚动条。"""
        panel = self._panel_rect()
        pygame.draw.rect(self.surface, PANEL_COLOR, panel, border_radius=8)

        self._layout_panel()
        self._clamp_scroll()
        offset = int(self.panel_scroll)

        # 在面板区域内裁剪，防止内容溢出到面板之外
        self.surface.set_clip(panel)
        try:
            self._draw_panel_content(offset)
        finally:
            self.surface.set_clip(None)

        # 内容超出可视区域时绘制滚动条
        if self._max_scroll() > 0:
            self._draw_scrollbar(panel)

    def _draw_panel_content(self, offset: int) -> None:
        """在侧边栏内绘制可滚动的内容（标题、信息、按钮与提示）。"""
        panel = self._panel_rect()
        px = panel.x + 16
        py = panel.y + 16 - offset
        line_gap = 28
        mouse_pos = pygame.mouse.get_pos()

        # 标题
        title = self.font_title.render("迷宫寻路", True, TEXT_COLOR)
        self.surface.blit(title, (px, py))
        py += 40

        # 基础信息
        info_lines = [
            f"规模：{self.rows} x {self.cols}",
            f"起点：(0, 0)  终点：({self.goal[0]}, {self.goal[1]})",
        ]
        for line in info_lines:
            self.surface.blit(self.font_small.render(line, True, MUTED_COLOR), (px, py))
            py += line_gap

        py += 8

        # 寻路统计信息
        if self.stats is not None:
            stat_lines = [
                "—— 寻路统计 ——",
                f"路径长度：{self.stats.length} 步",
                f"访问节点：{self.stats.visited_count}",
                f"耗时：{self.stats.elapsed_ms:.2f} ms",
                f"是否可达：{'是' if self.stats.found else '否'}",
            ]
            for line in stat_lines:
                self.surface.blit(self.font_small.render(line, True, TEXT_COLOR), (px, py))
                py += line_gap
            py += 8

        # 操作按钮（按钮 rect 存内容坐标，绘制时减去滚动偏移）
        for button in self._build_buttons():
            screen_rect = button.rect.move(0, -offset)
            button.draw(self.surface, screen_rect, mouse_pos)

        # 底部提示信息（自动换行）
        py = self._panel_message_y - offset
        for line in self._wrap_text(self.message, panel.width - 32):
            self.surface.blit(self.font_small.render(line, True, MESSAGE_COLOR), (px, py))
            py += 22

    def _draw_scrollbar(self, panel: pygame.Rect) -> None:
        """绘制滚动条轨道与滑块。"""
        track, thumb = self._scrollbar_metrics(panel)
        pygame.draw.rect(self.surface, SCROLLBAR_TRACK_COLOR, track, border_radius=SCROLLBAR_WIDTH // 2)
        pygame.draw.rect(self.surface, SCROLLBAR_THUMB_COLOR, thumb, border_radius=SCROLLBAR_WIDTH // 2)

    def _build_buttons(self) -> List[Button]:
        """构建操作按钮列表（每次调用会复用同一批按钮对象）。"""
        if not hasattr(self, "_buttons"):
            self._buttons = [
                Button(pygame.Rect(0, 0, 0, 0), "↑ 上", self.font_normal, lambda: self.handle_move(NORTH)),
                Button(pygame.Rect(0, 0, 0, 0), "← 左", self.font_normal, lambda: self.handle_move(WEST)),
                Button(pygame.Rect(0, 0, 0, 0), "↓ 下", self.font_normal, lambda: self.handle_move(SOUTH)),
                Button(pygame.Rect(0, 0, 0, 0), "→ 右", self.font_normal, lambda: self.handle_move(EAST)),
                Button(pygame.Rect(0, 0, 0, 0), "BFS 自动寻路", self.font_normal, lambda: self.run_pathfinding("bfs")),
                Button(pygame.Rect(0, 0, 0, 0), "A* 自动寻路", self.font_normal, lambda: self.run_pathfinding("astar")),
                Button(pygame.Rect(0, 0, 0, 0), "重新生成", self.font_normal, self.reset),
                Button(pygame.Rect(0, 0, 0, 0), "清除路径", self.font_normal, self._clear_path_action),
            ]
        return self._buttons

    def _clear_path_action(self) -> None:
        """清除路径按钮的动作。"""
        self.stop_animation()
        self.clear_path()
        self.message = "已清除路径"

    def _wrap_text(self, text: str, max_width: int) -> List[str]:
        """将长文本按像素宽度自动换行。"""
        words = text.split(" ")
        lines: List[str] = []
        current = ""
        for word in words:
            candidate = word if not current else current + " " + word
            if self.font_small.size(candidate)[0] <= max_width:
                current = candidate
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines

    # ------------------------------------------------------------------
    # 主循环
    # ------------------------------------------------------------------
    def run(self) -> None:
        """启动游戏主循环。"""
        clock = pygame.time.Clock()
        running = True

        while running:
            dt = clock.tick(60)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    self.handle_key(event.key)
                elif event.type == pygame.MOUSEWHEEL:
                    self.handle_wheel(event)
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.handle_click(event.pos)
                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    self._dragging_scrollbar = False
                elif event.type == pygame.MOUSEMOTION:
                    self.handle_drag_scroll(event.pos)

            # 推进寻路路径动画
            self.update_animation(dt)
            self.draw()

        pygame.quit()
