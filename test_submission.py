import json
import random
import re
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Set

# --- Copied from Minesweeper GRPO Notebook ---

@dataclass
class MinesweeperGame:
    rows: int
    cols: int
    num_mines: int
    seed: Optional[int] = None
    _rng: random.Random = field(init=False, repr=False)
    _board: List[List[int]] = field(init=False, repr=False)  # -1 = mine, 0-8 = count
    _revealed: Set[Tuple[int, int]] = field(init=False, repr=False, default_factory=set)
    _flagged: Set[Tuple[int, int]] = field(init=False, repr=False, default_factory=set)
    _state: str = field(default="ongoing", init=False, repr=False)

    def __post_init__(self):
        if self.num_mines >= self.rows * self.cols:
            raise ValueError("Too many mines for board size")
        self._rng = random.Random(self.seed)
        self._board = [[0 for _ in range(self.cols)] for _ in range(self.rows)]
        self._place_mines()
        self._calculate_numbers()

    def _place_mines(self):
        """Place mines randomly on the board"""
        positions = [(r, c) for r in range(self.rows) for c in range(self.cols)]
        mine_positions = self._rng.sample(positions, self.num_mines)
        for r, c in mine_positions:
            self._board[r][c] = -1

    def _calculate_numbers(self):
        """Calculate numbers for each cell based on adjacent mines"""
        for r in range(self.rows):
            for c in range(self.cols):
                if self._board[r][c] == -1:
                    continue
                count = 0
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        if dr == 0 and dc == 0:
                            continue
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < self.rows and 0 <= nc < self.cols:
                            if self._board[nr][nc] == -1:
                                count += 1
                self._board[r][c] = count

    def _reveal_cell(self, row: int, col: int) -> bool:
        """Reveal a cell. Returns True if valid move, False if invalid."""
        if not (0 <= row < self.rows and 0 <= col < self.cols):
            return False
        if (row, col) in self._revealed or (row, col) in self._flagged:
            return False

        stack = [(row, col)]
        while stack:
            r, c = stack.pop()
            if (r, c) in self._revealed:
                continue

            self._revealed.add((r, c))

            # Hit a mine!
            if self._board[r][c] == -1:
                self._state = "failed"
                return True

            # Auto-reveal neighbors if cell is 0
            if self._board[r][c] == 0:
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        if dr == 0 and dc == 0:
                            continue
                        nr, nc = r + dr, c + dc
                        if (0 <= nr < self.rows and 0 <= nc < self.cols
                                and (nr, nc) not in self._revealed
                                and (nr, nc) not in self._flagged):
                            stack.append((nr, nc))

        return True

    def _flag_cell(self, row: int, col: int) -> bool:
        """Flag/unflag a cell. Returns True if valid, False if invalid"""
        if not (0 <= row < self.rows and 0 <= col < self.cols):
            return False
        if (row, col) in self._revealed:
            return False
        
        if (row, col) in self._flagged:
            self._flagged.remove((row, col))
        else:
            self._flagged.add((row, col))
        return True

    def do_action(self, action: dict) -> str:
        """Execute an action and return a status string."""
        if self._state != "ongoing":
            return "game_over"

        if not isinstance(action, dict):
            self._state = "failed"
            return "invalid_format"

        action_type = action.get("type")
        row = action.get("row")
        col = action.get("col")

        if action_type not in ["reveal", "flag"] or row is None or col is None:
            self._state = "failed"
            return "invalid_format"

        try:
            row, col = int(row), int(col)
        except (ValueError, TypeError):
            self._state = "failed"
            return "invalid_format"

        if not (0 <= row < self.rows and 0 <= col < self.cols):
            self._state = "failed"
            return "out_of_bounds"

        if action_type == "reveal":
            if (row, col) in self._revealed:
                self._state = "failed"
                return "already_revealed"
            if (row, col) in self._flagged:
                self._state = "failed"
                return "flagged_cell"
            valid = self._reveal_cell(row, col)
        else:
            if (row, col) in self._revealed:
                self._state = "failed"
                return "invalid_flag"
            valid = self._flag_cell(row, col)

        if not valid:
            self._state = "failed"
            return "invalid_format"

        self._check_win()

        if self._state == "failed":
            return "mine"
        if self._state == "success":
            return "win"
        return "ok"

    def _check_win(self):
        """Check if player has won"""
        total_cells = self.rows * self.cols
        safe_cells = total_cells - self.num_mines
        if len(self._revealed) == safe_cells:
            self._state = "success"

    def get_visible_board(self) -> List[List[str]]:
        """Get board state as player sees it"""
        visible = []
        for r in range(self.rows):
            row = []
            for c in range(self.cols):
                if (r, c) in self._flagged:
                    row.append('F')
                elif (r, c) in self._revealed:
                    val = self._board[r][c]
                    row.append('*' if val == -1 else str(val))
                else:
                    row.append('.')
            visible.append(row)
        return visible

    def state(self) -> str:
        return self._state

    def pretty_print(self) -> str:
        """Pretty print the board"""
        visible = self.get_visible_board()
        lines = []
        
        # Header
        header = "   " + " ".join(f"{i:2d}" for i in range(self.cols))
        lines.append(header)
        lines.append("  " + "─" * (self.cols * 3 + 1))
        
        # Board
        for r, row in enumerate(visible):
            line = f"{r:2d}│ " + "  ".join(row)
            lines.append(line)
        
        return "\n".join(lines)

def format_state_for_llm(game: MinesweeperGame) -> str:
    """Convert game state to JSON prompt for LLM"""

    state = {
        "board": game.get_visible_board(),
        "rows": game.rows,
        "cols": game.cols,
        "mines": game.num_mines,
        "flags_placed": len(game._flagged),
        "cells_revealed": len(game._revealed),
    }

    prompt = f"""
You are a Minesweeper agent.

You must output ONLY valid JSON.
No explanation.
No reasoning.
No extra text.

Output format strictly:

{{{"type":"reveal","row":X,"col":Y}}}

or

{{{"type":"flag","row":X,"col":Y}}}

Start immediately with {{ and end with }}.

Game state:
{json.dumps(state, indent=2)}

Legend:
- "." = unrevealed cell
- "F" = flagged cell (suspected mine)
- "0"-"8" = number of adjacent mines
- "*" = revealed mine (game over)

Output your next action as JSON:
{{{"type": "reveal", "row": <row_index>, "col": <col_index>}}}
or
{{{"type": "flag", "row": <row_index>, "col": <col_index>}}}

Your action:
"""
    return prompt

# --- Test Logic ---

def test_game_logic():
    print("Testing Minesweeper Game Logic...")
    game = MinesweeperGame(rows=6, cols=6, num_mines=5, seed=42)
    print(game.pretty_print())
    
    # Test a valid move
    print("\nExecuting Move: Reveal (0,0)")
    res = game.do_action({"type": "reveal", "row": 0, "col": 0})
    print(f"Result: {res}")
    print(game.pretty_print())
    
    assert res == "ok"
    assert game.state() == "ongoing"
    
    # Test prompt generation
    print("\nGenerating Prompt...")
    prompt = format_state_for_llm(game)
    print(prompt[:200] + "...")
    assert "Game state:" in prompt
    assert "\"board\"" in prompt
    print("Promp Check Passed!")

if __name__ == "__main__":
    test_game_logic()
