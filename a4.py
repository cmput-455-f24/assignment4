# CMPUT 455 Assignment 4 starter code
# Implement the specified commands to complete the assignment
# Full assignment specification here: https://webdocs.cs.ualberta.ca/~mmueller/courses/cmput455/assignments/a4.html

import sys
import random
import signal

import numpy as np


# Custom time out exception
class TimeoutException(Exception):
    pass


# Function that is called when we reach the time limit
def handle_alarm(signum, frame):
    raise TimeoutException


class CommandInterface:

    def __init__(self):
        # Define the string to function command mapping
        self.command_dict = {
            "help": self.help,
            "game": self.game,
            "show": self.show,
            "play": self.play,
            "legal": self.legal,
            "genmove": self.genmove,
            "winner": self.winner,
            "timelimit": self.timelimit,
        }
        self.board = [[None]]
        self.player = 1
        self.max_genmove_time = 1
        signal.signal(signal.SIGALRM, handle_alarm)

    # ====================================================================================================================
    # VVVVVVVVVV Start of predefined functions. You may modify, but make sure not to break the functionality. VVVVVVVVVV
    # ====================================================================================================================

    # Convert a raw string to a command and a list of arguments
    def process_command(self, str):
        str = str.lower().strip()
        command = str.split(" ")[0]
        args = [x for x in str.split(" ")[1:] if len(x) > 0]
        if command not in self.command_dict:
            print(
                "? Uknown command.\nType 'help' to list known commands.",
                file=sys.stderr,
            )
            print("= -1\n")
            return False
        try:
            return self.command_dict[command](args)
        except Exception as e:
            print("Command '" + str + "' failed with exception:", file=sys.stderr)
            print(e, file=sys.stderr)
            print("= -1\n")
            return False

    # Will continuously receive and execute commands
    # Commands should return True on success, and False on failure
    # Every command will print '= 1' or '= -1' at the end of execution to indicate success or failure respectively
    def main_loop(self):
        while True:
            str = input()
            if str.split(" ")[0] == "exit":
                print("= 1\n")
                return True
            if self.process_command(str):
                print("= 1\n")

    # Will make sure there are enough arguments, and that they are valid numbers
    # Not necessary for commands without arguments
    def arg_check(self, args, template):
        converted_args = []
        if len(args) < len(template.split(" ")):
            print(
                "Not enough arguments.\nExpected arguments:", template, file=sys.stderr
            )
            print("Recieved arguments: ", end="", file=sys.stderr)
            for a in args:
                print(a, end=" ", file=sys.stderr)
            print(file=sys.stderr)
            return False
        for i, arg in enumerate(args):
            try:
                converted_args.append(int(arg))
            except ValueError:
                print(
                    "Argument '"
                    + arg
                    + "' cannot be interpreted as a number.\nExpected arguments:",
                    template,
                    file=sys.stderr,
                )
                return False
        args = converted_args
        return True

    # List available commands
    def help(self, args):
        for command in self.command_dict:
            if command != "help":
                print(command)
        print("exit")
        return True

    def game(self, args):
        if not self.arg_check(args, "n m"):
            return False
        n, m = [int(x) for x in args]
        if n < 0 or m < 0:
            print("Invalid board size:", n, m, file=sys.stderr)
            return False

        self.board = []
        for i in range(m):
            self.board.append([None] * n)
        self.player = 1
        return True

    def show(self, args):
        for row in self.board:
            for x in row:
                if x is None:
                    print(".", end="")
                else:
                    print(x, end="")
            print()
        return True

    def is_legal(self, x, y, num):
        if self.board[y][x] is not None:
            return False, "occupied"

        consecutive = 0
        count = 0
        self.board[y][x] = num
        for row in range(len(self.board)):
            if self.board[row][x] == num:
                count += 1
                consecutive += 1
                if consecutive >= 3:
                    self.board[y][x] = None
                    return False, "three in a row"
            else:
                consecutive = 0
        too_many = count > len(self.board) // 2 + len(self.board) % 2

        consecutive = 0
        count = 0
        for col in range(len(self.board[0])):
            if self.board[y][col] == num:
                count += 1
                consecutive += 1
                if consecutive >= 3:
                    self.board[y][x] = None
                    return False, "three in a row"
            else:
                consecutive = 0
        if too_many or count > len(self.board[0]) // 2 + len(self.board[0]) % 2:
            self.board[y][x] = None
            return False, "too many " + str(num)

        self.board[y][x] = None
        return True, ""

    def valid_move(self, x, y, num):
        if (
            x >= 0
            and x < len(self.board[0])
            and y >= 0
            and y < len(self.board)
            and (num == 0 or num == 1)
        ):
            legal, _ = self.is_legal(x, y, num)
            return legal

    def play(self, args):
        err = ""
        if len(args) != 3:
            print("= illegal move: " + " ".join(args) + " wrong number of arguments\n")
            return False
        try:
            x = int(args[0])
            y = int(args[1])
        except ValueError:
            print("= illegal move: " + " ".join(args) + " wrong coordinate\n")
            return False
        if x < 0 or x >= len(self.board[0]) or y < 0 or y >= len(self.board):
            print("= illegal move: " + " ".join(args) + " wrong coordinate\n")
            return False
        if args[2] != "0" and args[2] != "1":
            print("= illegal move: " + " ".join(args) + " wrong number\n")
            return False
        num = int(args[2])
        legal, reason = self.is_legal(x, y, num)
        if not legal:
            print("= illegal move: " + " ".join(args) + " " + reason + "\n")
            return False
        self.board[y][x] = num
        if self.player == 1:
            self.player = 2
        else:
            self.player = 1
        return True

    def legal(self, args):
        if not self.arg_check(args, "x y number"):
            return False
        x, y, num = [int(x) for x in args]
        if self.valid_move(x, y, num):
            print("yes")
        else:
            print("no")
        return True

    def get_legal_moves(self):
        moves = []
        for y in range(len(self.board)):
            for x in range(len(self.board[0])):
                for num in range(2):
                    legal, _ = self.is_legal(x, y, num)
                    if legal:
                        moves.append([str(x), str(y), str(num)])
        return moves

    def is_terminal(self):
        return len(self.get_legal_moves()) == 0

    def winner(self, args):
        if len(self.get_legal_moves()) == 0:
            if self.player == 1:
                print(2)
            else:
                print(1)
        else:
            print("unfinished")
        return True

    def timelimit(self, args):
        self.max_genmove_time = int(args[0])
        return True

    # ===============================================================================================
    # ɅɅɅɅɅɅɅɅɅɅ End of predefined functions. ɅɅɅɅɅɅɅɅɅɅ
    # ===============================================================================================

    # ===============================================================================================
    # VVVVVVVVVV Start of Assignment 4 functions. Add/modify as needed. VVVVVVVV
    # ===============================================================================================

    def genmove(self, args):
        try:
            # Set the time limit alarm
            signal.alarm(self.max_genmove_time)

            # Modify the following to give better moves than random play
            moves = self.get_legal_moves()
            if len(moves) == 0:
                print("resign")
            else:
                rand_move = moves[random.randint(0, len(moves) - 1)]
                self.play(rand_move)
                print(" ".join(rand_move))

            # Disable the time limit alarm
            signal.alarm(0)

        except TimeoutException:
            # This block of code runs when the time limit is reached
            print("resign")

        return True

    # ===============================================================================================
    # ɅɅɅɅɅɅɅɅɅɅ End of Assignment 4 functions. ɅɅɅɅɅɅɅɅɅɅ
    # ===============================================================================================


class MCTS:
    def __init__(self, iteration_limit=1000000) -> None:
        self.iteration_limit = iteration_limit

    # Search for the best move from the initial state
    # 1) Select the child node of the root using uct
    # 2) Expand the tree with node child
    # 3) Simulate the game from the node state
    # 4) Back propagate the reward
    def search(self, initial_state):
        root = Node(initial_state)

        for _ in range(self.iteration_limit):
            node = self.select(root)

            if node.state.is_terminal():
                # Expand tree with node children
                node = self.expand(node)

            reward = self.simulate(node)

            # Back propagate the reward
            self.back_propagation(node, reward)

    # Run UCT to select the best child of the node (balance exploration and exploitation)
    def select(self, node):

        while not node.state.is_terminal():
            if node.state.is_terminal():
                # Run UCT to select the best child of the node (balance exploration and exploitation)
                node = node.best_child(self.exploration_constant)
            else:
                return node
        # return best child node to explore
        return node

    # Add a new child node representing a possible move
    def expand(self, node):
        # Get node children's attempted moves
        attempted_moves = node.get_children_moves()
        # Get the legal moves from the current state
        legal_moves = node.state.get_legal_moves()

        for move in legal_moves:
            if move not in attempted_moves:
                # Play move
                new_state = node.state.play(move)
                # Create a new child node based on new state, parent node and move
                child_node = Node(new_state, parent=node, move=move)
                # Update node's children
                node.children.append(child_node)

                return child_node

        # Case for fully expanded path
        return node

    # Perform a simulation from the node state'
    # TODO Need a heuristic based simulation policy
    def simulation(self, state):
        current_state = state.copy()

        while not current_state.is_terminal():
            # Get legal moves
            legal_moves = current_state.get_legal_moves()
            # Don't do anything if there are no legal moves remaining
            if len(legal_moves) == 0:
                break

            # TODO: For now, use a uniform random policy (all moves are equally likely to be chosen)
            random_move = random.choice(legal_moves)
            # Play the random move selected by policy
            current_state = current_state.play_move(random_move)

        # Get the winner of the game from the final state produced by the simulation
        isWinner = current_state.get_winner()

        # return 1 if player 1 wins
        #        0 if player 2 wins
        if isWinner == current_state.player_turn():
            return 1
        else:
            return 0

    # Update visit counts and rewards along the path back to the root node
    # This data will be used to select the next node to explore
    def back_propagation(self, node, reward):
        while node is not None:
            node.visits += 1
            node.reward += reward
            node = node.parent


# What should a node class include
# - state - the state of the game
# - parent - the parent node
# - children - the children nodes
# - visits - the number of times the node has been visited
# - reward - the reward of the node
class Node:
    def __init__(self):
        self.state = None
        self.parent = None
        self.children = []
        self.visits = 0
        self.reward = 0

    def is_fully_expanded(self):
        return len(self.children) == len(self.state.get_legal_moves())

    def best_child(self, exploration_constant):
        children_evals = [
            self.uct(child, exploration_constant) for child in self.children
        ]
        return self.children[np.argmax(children_evals)]

    # win ratio of child * exploration constant * sqrt(log(parent visits) / child visits)
    def uct(self, node, exploration_constant=1.4):
        return (node.reward / node.visits) + exploration_constant * np.sqrt(
            np.log(self.visits) / node.visits
        )
    

if __name__ == "__main__":
    interface = CommandInterface()
    interface.main_loop()
