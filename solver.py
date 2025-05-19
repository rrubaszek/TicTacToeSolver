import socket
import sys
from typing import Tuple, Optional
from collections import OrderedDict

class GameClient:
    def __init__(self, ip: str, port: int, player_number: int, nickname: str, depth: int):
        self.server_address = (ip, port)
        self.player_number = player_number
        self.nickname = nickname[:9]  # Max 9 characters
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.depth = depth
        self.is_maximizing = player_number == 1
        self.player_symbol = 'X' if player_number == 1 else 'O'
        self.opponent_symbol = 'O' if player_number == 1 else 'X'
        self.board = [['-' for _ in range(5)] for _ in range(5)]
        self.transposition_table = OrderedDict()
        self.MAX_TT_SIZE = 10000

    def connect(self) -> None:
        print(f"Connecting to {self.server_address}...")
        self.socket.connect(self.server_address)
        print("Connected to server.")

    def send(self, message: str) -> None:
        encoded = message.encode('utf-8')
        self.socket.sendall(encoded)
        print(f"[Sent] {message}")

    def receive(self, buffer_size: int = 16) -> str:
        data = self.socket.recv(buffer_size)
        message = data.decode('utf-8')
        print(f"[Received] {message}")
        return message
    
    def update_board(self, move: int, player: int) -> None:
        x = (move // 10) - 1  # indeks od 0
        y = (move % 10) - 1
        if 0 <= x < 5 and 0 <= y < 5:
            self.board[x][y] = 'X' if player == 1 else 'O'
        else:
            print(f"Warning: move {move} outside board range")

    def _board_to_string(self) -> str:
        return ''.join(''.join(row) for row in self.board)

    def print_board(self) -> None:
        print("  " + " ".join(str(i) for i in range(1, 6)))
        for i, row in enumerate(self.board, start=1):
            print(f"{i} " + " ".join(row))
        print()
    
    def _get_from_tt(self, key) -> Optional[float]:
        if key in self.transposition_table:
            value = self.transposition_table[key]
            self.transposition_table.move_to_end(key)
            return value
        return None

    def _store_in_tt(self, key, value: float) -> None:
        if key in self.transposition_table:
            self.transposition_table[key] = value
            self.transposition_table.move_to_end(key)
        else:
            # Add new entry
            if len(self.transposition_table) >= self.MAX_TT_SIZE:
                self.transposition_table.popitem(last=False)
            self.transposition_table[key] = value

    def start_game_loop(self) -> None:
        greeting = self.receive()
        print(greeting)

        self.send(f"{self.player_number} {self.nickname}")

        while True:
            raw_msg = self.receive()
            if not raw_msg:
                print("Connection closed by server.")
                break

            msg = int(raw_msg)
            move = msg % 100
            code = msg // 100

            if move != 0:
                opponent = 3 - self.player_number
                self.update_board(move, opponent)
                self.print_board()
                print(f"Opponent played move: {move}")

            if code in {0, 6}:  
                move = self.choose_move()
                self.update_board(move, self.player_number)
                self.print_board()
                self.send(str(move))
            elif code in {1, 2, 3, 4, 5}:  
                self.handle_game_end(code)
                break

        self.socket.close()
        print("Disconnected.")

    def choose_move(self) -> int:
        best_score = float('-inf')
        best_move = None

        moves = self.get_available_moves()
        for row, col in moves:
            self.board[row][col] = self.player_symbol
            score = self.minmax(self.depth - 1, False, float('-inf'), float('inf'))
            self.board[row][col] = '-'

            if score > best_score:
                best_score = score
                best_move = (row, col)

        if best_move is None:
            raise RuntimeError("No valid moves available")

        return (best_move[0] + 1) * 10 + (best_move[1] + 1)

    def minmax(self, depth: int, is_maximizing: bool, alpha: float = float('-inf'), beta: float = float('inf')) -> float:
        board_key = self._board_to_string()
        tt_key = (board_key, depth, is_maximizing, self.player_symbol)

        cached_value = self._get_from_tt(tt_key)
        if cached_value is not None:
            return cached_value

        result = self.check_game_over()
        if result is not None:
            self._store_in_tt(tt_key, result)
            return result
    
        if depth == 0:
            score = self.evaluate()
            self._store_in_tt(tt_key, score)
            return score
        
        moves = self.get_available_moves()
        if not moves:
            self._store_in_tt(tt_key, 0)
            return 0

        if is_maximizing:
            max_eval = float('-inf')
            for row, col in moves:
                self.board[row][col] = self.player_symbol
                eval = self.minmax(depth - 1, False, alpha, beta)
                self.board[row][col] = '-'    
            
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            
            self._store_in_tt(tt_key, max_eval)
            return max_eval
        else:
            min_eval = float('inf')
            for row, col in moves:   
                self.board[row][col] = self.opponent_symbol
                eval = self.minmax(depth - 1, True, alpha, beta)
                self.board[row][col] = '-'
            
                min_eval = min(min_eval, eval)
            
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            
            self._store_in_tt(tt_key, min_eval)
            return min_eval

    def count_consecutive(self, row: int, col: int, symbol: str) -> int:  
        directions = [
            (0, 1),   # poziomo
            (1, 0),   # pionowo
            (1, 1),   # ukośnie "\"
            (1, -1),  # ukośnie "/"
        ]

        max_count = 1
        for dr, dc in directions:
            count = 1

            # W przód
            r, c = row + dr, col + dc
            while 0 <= r < 5 and 0 <= c < 5 and self.board[r][c] == symbol:
                count += 1
                r += dr
                c += dc

            # W tył
            r, c = row - dr, col - dc
            while 0 <= r < 5 and 0 <= c < 5 and self.board[r][c] == symbol:
                count += 1
                r -= dr
                c -= dc

            max_count = max(max_count, count)

        return max_count
    
    def get_available_moves(self) -> list[Tuple[int, int]]:
        moves = [(r, c) for r in range(5) for c in range(5) if self.board[r][c] == '-']
        moves.sort(key=lambda move: abs(move[0] - 2) + abs(move[1] - 2))
        return moves
    
    def check_game_over(self) -> Optional[int]:
        for row in range(5):
            for col in range(5):
                symbol = self.board[row][col]
                if symbol != '-':
                    count = self.count_consecutive(row, col, symbol)
                    if count >= 4:
                        return 10000 if symbol == self.player_symbol else -10000
                    elif count == 3:
                        return -10000 if symbol == self.player_symbol else 10000
        return None
    
    def evaluate(self) -> float:
        score = 0
        center_positions = [(2, 3), (3, 2), (3, 3), (4, 3), (3, 4)]

        for row in range(5):
            for col in range(5):
                current = self.board[row][col]
                if current == '-':
                    continue

                is_player = current == self.player_symbol
                player_multiplier = 1 if is_player else -1

                if (row, col) in center_positions:
                    score += 1000 * player_multiplier

                for dr, dc in [(0, 1), (1, 0), (1, 1), (1, -1)]:
                    pattern_score = self.evaluate_pattern(row, col, dr, dc, current)
                    score += pattern_score * player_multiplier

                consecutive = self.count_consecutive(row, col, current)
                if consecutive == 3:
                    if is_player:
                        score -= 10000
                    else:
                        score += 10000
                elif consecutive >= 4:
                    if is_player:
                        score += 10000
                    else:
                        score -= 10000

        for row, col in self.get_available_moves():
            self.board[row][col] = self.player_symbol
            consecutive = self.count_consecutive(row, col, self.player_symbol)
            if consecutive >= 4:
                score += 10000
            elif consecutive == 3:
                score -= 10000
            self.board[row][col] = '-'

        
            self.board[row][col] = self.opponent_symbol
            consecutive = self.count_consecutive(row, col, self.opponent_symbol)
            if consecutive >= 4:
                score -= 10000
            elif consecutive == 3:
                score += 10000
            self.board[row][col] = '-'

        return score


    def evaluate_pattern(self, row: int, col: int, dr: int, dc: int, symbol: str) -> float:
        pattern = []

        # Collect pattern in negative direction
        r, c = row - dr, col - dc
        while 0 <= r < 5 and 0 <= c < 5:
            pattern.insert(0, self.board[r][c])
            r -= dr
            c -= dc

        # Add current position
        pattern.append(symbol)

        # Collect pattern in positive direction
        r, c = row + dr, col + dc
        while 0 <= r < 5 and 0 <= c < 5:
            pattern.append(self.board[r][c])
            r += dr
            c += dc

        score = 0
        consecutive = 0
        has_gap = False

        for cell in pattern:
            if cell == symbol:
                consecutive += 1
            elif cell == '-':
                if consecutive > 0:
                    has_gap = True
            else:
                break  # przeciwnik - przerywa wzorzec

        if consecutive == 1:
            score += 2
        elif consecutive == 2:
            score += 10
            if has_gap:
                score += 20
        elif consecutive == 3:
            score -= 10000
        elif consecutive >= 4:
            score += 10000

        return score

    def handle_game_end(self, code: int) -> None:
        outcome = {
            1: "You won!",
            2: "You lost.",
            3: "Draw.",
            4: "You won. Opponent made an error.",
            5: "You lost. You made an error."
        }.get(code, "Unknown game result.")
        print(f"Game over: {outcome}")


def parse_args() -> Tuple[str, int, int, str, int]:
    if len(sys.argv) != 6:
        print("Usage: python bot.py <ip> <port> <player_number> <nickname> <depth>")
        sys.exit(1)
    ip = sys.argv[1]
    try:
        port = int(sys.argv[2])
        player_number = int(sys.argv[3])
        depth = int(sys.argv[5])
        if depth > 10 or depth < 1:
            raise ValueError
    except ValueError:
        print("Port and player_number must be integers. Depth must be between 1 and 10")
        sys.exit(1)
    nickname = sys.argv[4]
    return ip, port, player_number, nickname, depth


def main() -> None:
    ip, port, player_number, nickname, depth = parse_args()
    client = GameClient(ip, port, player_number, nickname, depth)
    client.connect()
    client.start_game_loop()


if __name__ == "__main__":
    main()
