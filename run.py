"""
Pygame presentation layer for Minesweeper.

This module owns:
- Renderer: all drawing of cells, header, and result overlays
- InputController: translate mouse input to board actions and UI feedback
- Game: orchestration of loop, timing, state transitions, and composition

The logic lives in components.Board; this module should not implement rules.
"""
import json
from pathlib import Path

import sys

import pygame

import config
from components import Board
from pygame.locals import Rect

HIGHSCORE_PATH = Path(__file__).with_name("high_scores.json")


def load_highscores() -> dict:
    if HIGHSCORE_PATH.exists():
        try:
            return json.loads(HIGHSCORE_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_highscores(data: dict) -> None:
    HIGHSCORE_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


class Renderer:
    """Draws the Minesweeper UI.

    Knows how to draw individual cells with flags/numbers, header info,
    and end-of-game overlays with a semi-transparent background.
    """

    def __init__(self, screen: pygame.Surface, board: Board):
        self.screen = screen
        self.board = board
        self.font = pygame.font.Font(config.font_name, config.font_size)
        self.header_font = pygame.font.Font(config.font_name, config.header_font_size)
        self.result_font = pygame.font.Font(config.font_name, config.result_font_size)

    def cell_rect(self, col: int, row: int) -> Rect:
        """Return the rectangle in pixels for the given grid cell."""
        x = config.margin_left + col * config.cell_size
        y = config.margin_top + row * config.cell_size
        return Rect(x, y, config.cell_size, config.cell_size)

    def draw_cell(self, col: int, row: int, highlighted: bool) -> None:
        """Draw a single cell, respecting revealed/flagged state and highlight."""
        cell = self.board.cells[self.board.index(col, row)]
        rect = self.cell_rect(col, row)
        if cell.state.is_revealed:
            pygame.draw.rect(self.screen, config.color_cell_revealed, rect)
            if cell.state.is_mine:
                pygame.draw.circle(self.screen, config.color_cell_mine, rect.center, rect.width // 4)
            elif cell.state.adjacent > 0:
                color = config.number_colors.get(cell.state.adjacent, config.color_text)
                label = self.font.render(str(cell.state.adjacent), True, color)
                label_rect = label.get_rect(center=rect.center)
                self.screen.blit(label, label_rect)
        else:
            base_color = config.color_highlight if highlighted else config.color_cell_hidden
            pygame.draw.rect(self.screen, base_color, rect)
            if cell.state.is_flagged:
                flag_w = max(6, rect.width // 3)
                flag_h = max(8, rect.height // 2)
                pole_x = rect.left + rect.width // 3
                pole_y = rect.top + 4
                pygame.draw.line(self.screen, config.color_flag, (pole_x, pole_y), (pole_x, pole_y + flag_h), 2)
                pygame.draw.polygon(
                    self.screen,
                    config.color_flag,
                    [
                        (pole_x + 2, pole_y),
                        (pole_x + 2 + flag_w, pole_y + flag_h // 3),
                        (pole_x + 2, pole_y + flag_h // 2),
                    ],
                )
        pygame.draw.rect(self.screen, config.color_grid, rect, 1)

    def draw_header(self, remaining_mines: int, time_text: str, urgent: bool = False) -> None:
        """Draw the header bar containing remaining mines and elapsed time."""
        pygame.draw.rect(
            self.screen,
            config.color_header,
            Rect(0, 0, config.width, config.margin_top - 4),
        )

        left_text = f"Mines: {remaining_mines}"
        right_text = f"Time: {time_text}"

        left_label = self.header_font.render(left_text, True, config.color_header_text)

        # Time 색상 결정
        right_color = config.color_header_text
        if urgent:
            if getattr(config, "timer_blink_interval_ms", 0) and config.timer_blink_interval_ms > 0:
                blink_on = (pygame.time.get_ticks() // config.timer_blink_interval_ms) % 2 == 0
                right_color = config.color_timer_urgent if blink_on else config.color_header_text
            else:
                right_color = config.color_timer_urgent

        right_label = self.header_font.render(right_text, True, right_color)

        # 위치 잡아서 그리기
        left_rect = left_label.get_rect(midleft=(10, (config.margin_top - 4) // 2))
        right_rect = right_label.get_rect(midright=(config.width - 10, (config.margin_top - 4) // 2))

        self.screen.blit(left_label, left_rect)
        self.screen.blit(right_label, right_rect)

    def draw_result_overlay(self, text: str | None) -> None:
        """Draw a semi-transparent overlay with centered result text (supports multiline)."""
        if not text:
            return

        overlay = pygame.Surface((config.width, config.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, config.result_overlay_alpha))
        self.screen.blit(overlay, (0, 0))

        lines = text.splitlines()
        gap = 10

        # 첫 줄(큰 글씨): result_font / 나머지(작은 글씨): header_font
        surfaces = []
        for i, line in enumerate(lines):
            font = self.result_font if i == 0 else self.header_font
            surfaces.append(font.render(line, True, config.color_result))

        total_h = sum(s.get_height() for s in surfaces) + gap * (len(surfaces) - 1)
        y = (config.height // 2) - (total_h // 2)

        for s in surfaces:
            rect = s.get_rect(center=(config.width // 2, y + s.get_height() // 2))
            self.screen.blit(s, rect)
            y += s.get_height() + gap


class InputController:
    """Translates input events into game and board actions."""

    def __init__(self, game: "Game"):
        self.game = game

    def pos_to_grid(self, x: int, y: int):
        """Convert pixel coordinates to (col,row) grid indices or (-1,-1) if out of bounds."""
        if not (config.margin_left <= x < config.width - config.margin_right):
            return -1, -1
        if not (config.margin_top <= y < config.height - config.margin_bottom):
            return -1, -1
        col = (x - config.margin_left) // config.cell_size
        row = (y - config.margin_top) // config.cell_size
        if 0 <= col < self.game.board.cols and 0 <= row < self.game.board.rows:
            return int(col), int(row)
        return -1, -1

    def handle_mouse(self, pos, button) -> None:
        # TODO: Handle mouse button events: left=reveal, right=flag, middle=neighbor highlight  in here
        col, row = self.pos_to_grid(pos[0], pos[1])
        if col == -1:  # 마우스가 그리드 밖에 있는 경우
            return

        game = self.game  # 게임 객체 가져오기
        board = game.board  # 보드 객체 가져오기

        # 게임이 끝나면 입력 무시
        if board.game_over or board.win:
            return

        # -------------------------------------
        # 왼쪽 버튼: reveal (칸 열기)
        # -------------------------------------
        if button == config.mouse_left:  # 왼쪽 버튼 클릭
            game.highlight_targets.clear()  # 하이라이트 초기화

            # 첫 클릭이면 타이머 시작
            if not game.started:
                game.started = True
                game.start_ticks_ms = pygame.time.get_ticks()

            # 칸 열기
            board.reveal(col, row)

        # -------------------------------------
        # 오른쪽 버튼: flag toggle (깃발 꽂기/빼기)
        # -------------------------------------
        elif button == config.mouse_right:  # 오른쪽 버튼 클릭
            game.highlight_targets.clear()  # 하이라이트 초기화
            board.toggle_flag(col, row)

        # -------------------------------------
        # 가운데 버튼: 주변 칸 하이라이트
        # -------------------------------------
        elif button == config.mouse_middle:
            neighbors = board.neighbors(col, row)

            game.highlight_targets = {
                (nc, nr)  # 하이라이트 대상 좌표
                for (nc, nr) in neighbors  # 주변 칸들중에
                if not board.cells[board.index(nc, nr)].state.is_revealed  # 열리지 않은 칸만 하이라이트
            }
            game.highlight_until_ms = pygame.time.get_ticks() + config.highlight_duration_ms
            # 전체 게임 진행 시간 + 하이라이트 지속 시간 의 시간까지 highlight 유지 #draw에서 처리


class Game:
    """Main application object orchestrating loop and high-level state."""

    def __init__(self):
        pygame.init()
        pygame.display.set_caption(config.title)
        self.screen = pygame.display.set_mode(config.display_dimension)
        self.clock = pygame.time.Clock()
        self.board = Board(config.cols, config.rows, config.num_mines)
        self.renderer = Renderer(self.screen, self.board)
        self.input = InputController(self)
        self.highlight_targets = set()
        self.highlight_until_ms = 0
        self.started = False
        self.start_ticks_ms = 0
        self.end_ticks_ms = 0
        self.highscores = load_highscores()
        self.new_record = False

    def reset(self):
        """Reset the game state and start a new board."""
        self.board = Board(config.cols, config.rows, config.num_mines)
        self.renderer.board = self.board
        self.highlight_targets.clear()
        self.highlight_until_ms = 0
        self.started = False
        self.start_ticks_ms = 0
        self.end_ticks_ms = 0
        self.new_record = False

    def _elapsed_ms(self) -> int:
        """Return elapsed time in milliseconds (stops when game ends)."""
        if not self.started:
            return 0
        if self.end_ticks_ms:
            return self.end_ticks_ms - self.start_ticks_ms
        return pygame.time.get_ticks() - self.start_ticks_ms

    def _format_time(self, ms: int) -> str:
        """Format milliseconds as mm:ss string."""
        total_seconds = ms // 1000
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes:02d}:{seconds:02d}"

    def _result_text(self) -> str | None:
        """Return result label to display, or None if game continues."""
        key = self._score_key()
        best = self.highscores.get(key)

        def fmt_best() -> str:
            return self._format_time(best) if isinstance(best, int) else "--:--"

        if self.board.game_over:
            return "GAME OVER\nBEST " + fmt_best()

        if self.board.win:
            elapsed = self._elapsed_ms()
            lines = [
                "GAME CLEAR",
                "TIME " + self._format_time(elapsed),
                "BEST " + fmt_best(),
            ]
            if self.new_record:
                lines.append("BEST RECORD!")
            return "\n".join(lines)

        return None

    def draw(self):
        """Render one frame: header, grid, result overlay."""
        if pygame.time.get_ticks() > self.highlight_until_ms and self.highlight_targets:
            self.highlight_targets.clear()
        self.screen.fill(config.color_bg)
        remaining = max(0, config.num_mines - self.board.flagged_count())
        elapsed_ms = self._elapsed_ms()
        time_text = self._format_time(elapsed_ms)
        urgent = elapsed_ms >= config.timer_urgent_after_ms
        self.renderer.draw_header(remaining, time_text, urgent)
        now = pygame.time.get_ticks()
        for r in range(self.board.rows):
            for c in range(self.board.cols):
                highlighted = (now <= self.highlight_until_ms) and ((c, r) in self.highlight_targets)
                self.renderer.draw_cell(c, r, highlighted)
        self.renderer.draw_result_overlay(self._result_text())
        pygame.display.flip()

    def run_step(self) -> bool:
        """Process inputs, update time, draw, and tick the clock once."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    self.reset()

                elif event.key == pygame.K_i:
                    if not self.started:
                        self.started = True
                        self.start_ticks_ms = pygame.time.get_ticks()
                    self.board.reveal_random_safe_cell()

                elif event.key == pygame.K_1:
                    self.change_difficulty("easy")
                elif event.key == pygame.K_2:
                    self.change_difficulty("medium")
                elif event.key == pygame.K_3:
                    self.change_difficulty("hard")
                elif event.key == pygame.K_4:
                    self.change_difficulty("very_hard")

            if event.type == pygame.MOUSEBUTTONDOWN:
                self.input.handle_mouse(event.pos, event.button)

        if (self.board.game_over or self.board.win) and self.started and not self.end_ticks_ms:
            self.end_ticks_ms = pygame.time.get_ticks()
            self._update_highscore_if_win()

        self.draw()
        self.clock.tick(config.fps)
        return True

    def _score_key(self) -> str:
        # 난이도 시스템이 있든 없든 동작하도록, 현재 보드 설정으로 키 생성
        return f"{config.cols}x{config.rows}-{config.num_mines}"

    def _update_highscore_if_win(self) -> None:
        """승리 시에만 BEST 기록 갱신/저장."""
        self.new_record = False
        if not (self.board.win and self.started and self.end_ticks_ms):
            return

        key = self._score_key()
        elapsed = self._elapsed_ms()
        best = self.highscores.get(key)

        if (best is None) or (elapsed < best):
            self.highscores[key] = elapsed
            save_highscores(self.highscores)
            self.new_record = True

    def change_difficulty(self, level_key: str):
        """난이도를 변경하고 게임을 재시작합니다."""
        config.apply_difficulty(level_key)

        # 창 크기 갱신
        self.screen = pygame.display.set_mode(config.display_dimension)

        # (선택) 타이틀에 난이도 표시
        pygame.display.set_caption(f"{config.title} ({level_key})")

        # 새 보드/렌더러로 교체 후 리셋
        self.board = Board(config.cols, config.rows, config.num_mines)
        self.renderer = Renderer(self.screen, self.board)

        self.reset()


def main() -> int:
    """Application entrypoint: run the main loop until quit."""
    game = Game()
    running = True
    while running:
        running = game.run_step()
    pygame.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
