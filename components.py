"""
Core game logic for Minesweeper.

This module contains pure domain logic without any pygame or pixel-level
concerns. It defines:
- CellState: the state of a single cell
- Cell: a cell positioned by (col,row) with an attached CellState
- Board: grid management, mine placement, adjacency computation, reveal/flag

The Board exposes imperative methods that the presentation layer (run.py)
can call in response to user inputs, and does not know anything about
rendering, timing, or input devices.
"""

import random
from typing import List, Tuple


class CellState:
    """Mutable state of a single cell.

    Attributes:
        is_mine: Whether this cell contains a mine.
        is_revealed: Whether the cell has been revealed to the player.
        is_flagged: Whether the player flagged this cell as a mine.
        adjacent: Number of adjacent mines in the 8 neighboring cells.
    """

    def __init__(self, is_mine: bool = False, is_revealed: bool = False, is_flagged: bool = False, adjacent: int = 0):
        self.is_mine = is_mine
        self.is_revealed = is_revealed
        self.is_flagged = is_flagged
        self.adjacent = adjacent


class Cell:
    """Logical cell positioned on the board by column and row."""

    def __init__(self, col: int, row: int):
        self.col = col
        self.row = row
        self.state = CellState()


class Board:
    """Minesweeper board state and rules.

    Responsibilities:
    - Generate and place mines with first-click safety
    - Compute adjacency counts for every cell
    - Reveal cells (iterative flood fill when adjacent == 0)
    - Toggle flags, check win/lose conditions
    """

    def __init__(self, cols: int, rows: int, mines: int):
        self.cols = cols
        self.rows = rows
        self.num_mines = mines
        self.cells: List[Cell] = [Cell(c, r) for r in range(rows) for c in range(cols)]
        self._mines_placed = False
        self.revealed_count = 0
        self.game_over = False
        self.win = False

    def index(self, col: int, row: int) -> int:
        """Return the flat list index for (col,row)."""
        return row * self.cols + col

    def is_inbounds(self, col: int, row: int) -> bool:
        # TODO: Return True if (col,row) is inside the board bounds.
        return 0 <= col < self.cols and 0 <= row < self.rows 
        # 범위 체크

    def neighbors(self, col: int, row: int) -> List[Tuple[int, int]]:
        # TODO: Return list of valid neighboring coordinates around (col,row).
        deltas = [
            (-1, -1), (0, -1), (1, -1),
            (-1,  0),           (1,  0),
            (-1,  1), (0,  1), (1,  1)
        ]

        result = [] 
        for dc, dr in deltas:
            nc, nr = col + dc, row + dr           # 새로운 좌표 계산
            if self.is_inbounds(nc, nr):          # 보드 안쪽이면만 추가
                result.append((nc, nr))
        return result
        # 현재 위치 기준에서 주위의 범위 안의 위치를 return  

    def place_mines(self, safe_col: int, safe_row: int) -> None:
        # TODO: Place mines randomly, guaranteeing the first click and its neighbors are safe. And Compute adjacency counts
            # 모든 지뢰 지정 가능 위치 저장
        all_positions = [(c, r) for r in range(self.rows) for c in range(self.cols)]
        # 첫 클릭한 셀과 그 주변 8방향 은 지뢰 금지 <- 합집합으로 중복없이 9좌표
        forbidden = {(safe_col, safe_row)} | set(self.neighbors(safe_col, safe_row))
        
        
        pool = [p for p in all_positions if p not in forbidden]
        random.shuffle(pool)
        
        
        #random 셔플된 pool의 앞에서 mine 개수만큼 선택
        mine_positions = pool[:self.num_mines]
        # 해당 위치에 is_mine = true 설정
        for (c, r) in mine_positions:
            # cell 객체의 state.is_mine을 true 즉 지뢰 생성.
            self.cells[self.index(c, r)].state.is_mine = True
        
        # 생성된 board에 대해서 인접한 지뢰 숫자를 파악해서 수를 표시
        for r in range(self.rows):
            for c in range(self.cols):
                cell = self.cells[self.index(c, r)]
                if cell.state.is_mine:
                    continue  # 지뢰 셀은 계산할 필요 없음
                count = 0
                # 주변 8칸 검사
                for (nc, nr) in self.neighbors(c, r):
                    if self.cells[self.index(nc, nr)].state.is_mine:
                        count += 1
                cell.state.adjacent = count  # 인접 지뢰 개수 저장
        self._mines_placed = True

    def reveal(self, col: int, row: int) -> None:
        # TODO: Reveal a cell; if zero-adjacent, iteratively flood to neighbors.
        # 범위 체크
        if not self.is_inbounds(col, row):
            return
        # 아직 지뢰 배치 안되었다면 (첫클릭이면) place_mines실행
        if not self._mines_placed:
            self.place_mines(col, row)

        # 클릭한 cell 가져오기
        cell = self.cells[self.index(col, row)]
        # 누른 cell이 만약 깃발이거나, 이미 눌러진 칸이면 클릭 무시
        if cell.state.is_flagged or cell.state.is_revealed:
            return
        
        # 지뢰칸이면 game over
        if cell.state.is_mine:
            cell.state.is_revealed = True
            self.game_over = True
            self._reveal_all_mines() # 모든 지뢰 위치 보이기
            return
        
        to_reveal = [(col,row)] # DFS방식 을 위한 stack
        while to_reveal:
            c,r = to_reveal.pop()
            cur = self.cells[self.index(c,r)] #객체 참조
            # 깃발이나 이미 열린 cell은 무시
            if cur.state.is_revealed or cur.state.is_flagged:
                continue
            
            cur.state.is_revealed = True
            self.revealed_count += 1

            if cur.state.adjacent == 0:
                # 주변에 지뢰가 없으면 flood fill 시작
                for(nc,nr) in self.neighbors(c,r):
                    ncell = self.cells[self.index(nc,nr)]
                    if not ncell.state.is_revealed and not ncell.state.is_mine:
                        #append된 값들은 while문에서 다시 pop되어 조건을 따지고 열리거나 무시되거나 할것
                        to_reveal.append((nc,nr))

        self._check_win()

    def toggle_flag(self, col: int, row: int) -> None:
        # TODO: Toggle a flag on a non-revealed cell.
        if not self.is_inbounds(col, row):
            return 
        
        cell = self.cells[self.index(col,row)]

        if cell.state.is_revealed == True: # 이미 open되어있으면 무시
            return
        
        cell.state.is_flagged = not cell.state.is_flagged # toggle

    def flagged_count(self) -> int:
        # TODO: Return current number of flagged cells.
       

    def _reveal_all_mines(self) -> None:
        """Reveal all mines; called on game over."""
        for cell in self.cells:
            if cell.state.is_mine:
                cell.state.is_revealed = True

    def _check_win(self) -> None:
        """Set win=True when all non-mine cells have been revealed."""
        total_cells = self.cols * self.rows
        if self.revealed_count == total_cells - self.num_mines and not self.game_over:
            self.win = True
            for cell in self.cells:
                if not cell.state.is_revealed and not cell.state.is_mine:
                    cell.state.is_revealed = True
