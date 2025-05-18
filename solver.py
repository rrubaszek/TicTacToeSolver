import socket
import sys
from typing import Tuple, Optional

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
        self.transposition_table = {}

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
        print("  " + " ".join(str(i) for i in range(1, 6)))  # nagłówek kolumn
        for i, row in enumerate(self.board, start=1):
            print(f"{i} " + " ".join(row))
        print()

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
                move_input = self.choose_move()
                self.update_board(move_input, self.player_number)
                self.send(str(move_input))
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
        tt_key = (board_key, depth, is_maximizing)

        if tt_key in self.transposition_table:
            return self.transposition_table[tt_key]

        result = self.check_game_over()
        if result is not None:
            return result
    
        if depth == 0:
            score = self.evaluate()
            self.transposition_table[tt_key] = score
            return score
        
        moves = self.get_available_moves()
        if not moves:
            return 0

        if is_maximizing:
            max_eval = float('-inf')
            for row, col in moves:
                self.board[row][col] = self.player_symbol

                if self.three_in_row(row, col, self.player_symbol):
                    self.board[row][col] = '-'
                    continue

                eval = self.minmax(depth - 1, False, alpha, beta)

                self.board[row][col] = '-'    

                max_eval = max(max_eval, eval)
            
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break  # odcięcie
            self.transposition_table[tt_key] = max_eval
            return max_eval
        else:
            min_eval = float('inf')
            for row, col in moves:
                self.board[row][col] = self.opponent_symbol
        
                if self.three_in_row(row, col, self.opponent_symbol):
                    self.board[row][col] = '-'
                    continue
            
                eval = self.minmax(depth - 1, True, alpha, beta)
            
                self.board[row][col] = '-'
            
                min_eval = min(min_eval, eval)
            
                beta = min(beta, eval)
                if beta <= alpha:
                    break  # odcięcie
            self.transposition_table[tt_key] = min_eval
            return min_eval

    def three_in_row(self, row: int, col: int, symbol: str) -> bool:  
        directions = [
            (0, 1),   # poziomo
            (1, 0),   # pionowo
            (1, 1),   # ukośnie "\"
            (1, -1),  # ukośnie "/"
        ]

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

            if count >= 3:
                return True

        return False
    
    def get_available_moves(self) -> list[Tuple[int, int]]:
        return [(i, j) for i in range(5) for j in range(5) if self.board[i][j] == '-']
    
    def check_game_over(self) -> Optional[int]:
        for row in range(5):
            for col in range(5):
                symbol = self.board[row][col]
                if symbol != '-' and self.three_in_row(row, col, symbol):
                    return 1 if symbol == self.player_symbol else -1
        return None

    
    def evaluate(self) -> float:
        score = 0
        center_positions = [(2, 2), (1, 2), (2, 1), (2, 3), (3, 2)]

        for row in range(5):
            for col in range(5):
                current = self.board[row][col]
                if current == '-':
                    continue

                is_player = current == self.player_symbol
                is_opponent = current == self.opponent_symbol
                player_multiplier = 1 if is_player else -1

                # Preferencja środka
                if (row, col) in center_positions:
                    score += 5 * player_multiplier

                # 4 kierunki
                for dr, dc in [(0, 1), (1, 0), (1, 1), (1, -1)]:
                    count = 1
                    open_ends = 0

                    # Przód
                    r, c = row + dr, col + dc
                    while 0 <= r < 5 and 0 <= c < 5 and self.board[r][c] == current:
                        count += 1
                        r += dr
                        c += dc
                    if 0 <= r < 5 and 0 <= c < 5 and self.board[r][c] == '-':
                        open_ends += 1

                    # Tył
                    r, c = row - dr, col - dc
                    while 0 <= r < 5 and 0 <= c < 5 and self.board[r][c] == current:
                        count += 1
                        r -= dr
                        c -= dc
                    if 0 <= r < 5 and 0 <= c < 5 and self.board[r][c] == '-':
                        open_ends += 1

                    # Punktacja
                    if count == 2:
                        score += 10 * open_ends * player_multiplier
                    elif count == 3:
                        score += 100 * open_ends * player_multiplier
                    elif count >= 4:
                        score += 1000 * player_multiplier

        for row, col in self.get_available_moves():
            self.board[row][col] = self.opponent_symbol
            if self.three_in_row(row, col, self.opponent_symbol):
                score += 75 
            self.board[row][col] = '-'
            
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
