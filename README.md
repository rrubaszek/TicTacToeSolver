# 5x5 Bot for Tic Tac Toe Board Game

## Project Overview

This project implements an **intelligent bot** for a turn-based game on a 5x5 board. Players take turns placing their symbols (`X` or `O`) on empty cells. The objective is to **create exactly 4 symbols in a row** (horizontally, vertically, or diagonally) — but with a twist:

> **Creating exactly 3 symbols in a row results in an automatic loss!**

The bot uses the **Minimax algorithm with alpha-beta pruning** along with a carefully crafted heuristic function to avoid traps and make optimal decisions based on the current board state.

---

## Game Rules

* Board: 5x5 grid.
* Player symbols: `X` and `O`.
* Players alternate turns.
* The winner is the player who forms **exactly 4 symbols in a line**.
* A player **loses immediately** if they form **exactly 3 symbols in a line**.
* Alignments longer than 4 are ignored.

---

## Algorithm

### 1. **Minimax with Alpha-Beta Pruning**

The bot uses a tree-based decision algorithm to:

* Search all possible moves up to a certain depth.
* Maximize its own score while minimizing the opponent's.
* Apply **alpha-beta pruning** to eliminate suboptimal paths early.

### 2. **Board Evaluation Heuristic**

The heuristic function is based on several key criteria:

* **Board Positioning** – Central squares (especially `(2, 2)`) are highly valued.
* **Symbol Patterns**:

  * 1 in a row: minor reward.
  * 2 in a row: moderate reward (+bonus for gaps).
  * 3 in a row: penalty — threat of immediate loss.
  * 4 in a row: high reward — potential win.
* **Future Move Simulation**:

  * Bot evaluates potential moves for both itself and the opponent.
  * It adjusts the score based on whether a win or loss is imminent next turn.

---

## Code Structure

* `BotPlayer` – The core bot class, which implements:

  * `choose_move()` – Selects the best move.
  * `evaluate()` – Heuristic function for board state.
  * `evaluate_pattern()` – Scores patterns in different directions.
  * `count_consecutive()` – Counts sequences of the same symbol.
  * `get_available_moves()` – Lists available moves, sorted by centrality.

---

## Gameplay Modes

* **Bot vs Human**
* **Bot vs Bot**

Game needs a server with TCP socket!
---

## Parameters

* `depth`: Search tree depth (default: 3-5).
* `player_symbol`: Player's symbol (`X` or `O`).
* `opponent_symbol`: Opponent's symbol.

---

## License

Open-source project for educational and hobby purposes.