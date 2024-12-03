# CMPUT 455 Assignment 2 starter code
# Implement the specified commands to complete the assignment
# Full assignment specification here: https://webdocs.cs.ualberta.ca/~mmueller/courses/cmput455/assignments/a2.html

import sys
import random
import signal
import math
import numpy as np
import cProfile
import copy

class CommandInterface:

    def __init__(self):
        # Define the string to function command mapping
        self.command_dict = {
            "help" : self.help,
            "game" : self.game,
            "show" : self.show,
            "play" : self.play,
            "legal" : self.legal,
            "genmove" : self.genmove,
            "winner" : self.winner,
            "timelimit" : self.timelimit,
            "solve" : self.solve
        }
        self.board = [[None]]
        self.player = 1
        self.timelimit = 1
        self.numberOfDigitsInRow = [[None]]
        self.numberOfDigitsInCol = [[None]]
        self.zobristHashTable = [[None]]
        self.zobristStateValue = 0 
    #===============================================================================================
    # VVVVVVVVVV START of PREDEFINED FUNCTIONS. DO NOT MODIFY. VVVVVVVVVV
    #===============================================================================================

    # Convert a raw string to a command and a list of arguments
    def process_command(self, str):
        str = str.lower().strip()
        command = str.split(" ")[0]
        args = [x for x in str.split(" ")[1:] if len(x) > 0]
        if command not in self.command_dict:
            print("? Uknown command.\nType 'help' to list known commands.", file=sys.stderr)
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
            print("Not enough arguments.\nExpected arguments:", template, file=sys.stderr)
            print("Recieved arguments: ", end="", file=sys.stderr)
            for a in args:
                print(a, end=" ", file=sys.stderr)
            print(file=sys.stderr)
            return False
        for i, arg in enumerate(args):
            try:
                converted_args.append(int(arg))
            except ValueError:
                print("Argument '" + arg + "' cannot be interpreted as a number.\nExpected arguments:", template, file=sys.stderr)
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

    #===============================================================================================
    # ɅɅɅɅɅɅɅɅɅɅ END OF PREDEFINED FUNCTIONS. ɅɅɅɅɅɅɅɅɅɅ
    #===============================================================================================

    #===============================================================================================
    # VVVVVVVVVV START OF ASSIGNMENT 2 FUNCTIONS. ADD/REMOVE/MODIFY AS NEEDED. VVVVVVVV
    #===============================================================================================

    def game(self, args):
        if not self.arg_check(args, "n m"):
            return False
        n, m = [int(x) for x in args]
        if n < 0 or m < 0:
            print("Invalid board size:", n, m, file=sys.stderr)
            return False
        
        self.board = []
        for i in range(m):
            self.board.append([None]*n)

        self.player = 1
        
        # Added
        self.numberOfDigitsInRow = [[0,0] for i in range(m)]
        self.numberOfDigitsInCol = [[0,0] for i in range(n)]
        self.zobristHashTable = [[ random.randint(-sys.maxsize-1, sys.maxsize) for i in range(3)] for i in range(n*m)]
        
        # 0 and 1 in the same position have negated hashcodes
        for i in range(n*m):
            self.zobristStateValue ^= self.zobristHashTable[i][2] 
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

    def is_legal_reason(self, x, y, num):
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
    
    def is_legal(self, x, y, num):
        if self.board[y][x] is not None:
            return False
        if self.violatesTriplesConstraint(x, y, num, self.board, len(self.board[0]), len(self.board)):
            return False
        if self.violatesBalanceConstraint(x, y, num):
            return False

        return True

    def violatesBalanceConstraint(self, col, row, digit):
        # Get number of value element (0 or 1) in the target row and column
        # Add 1 to the count to account for the new value being added
        digitsInRow = self.numberOfDigitsInRow[row][digit] + 1
        digitsInCol = self.numberOfDigitsInCol[col][digit] + 1
        # If the number of value elements in the row or column exceeds half the size of the row or column return True
        boardWidth = len(self.board[0])
        boardHeight = len(self.board)
        if math.ceil(boardWidth / 2) < digitsInRow:
            return True
        if math.ceil(boardHeight / 2) < digitsInCol:
            return True

        return False


    def violatesTriplesConstraint(self, col, row, digit, board, boardWidth, boardHeight):
        if (
            row < 0
            or col < 0
            or (digit != 1 and digit != 0)
            or row >= boardHeight
            or col >= boardWidth
            or len(board)*len(board[0]) != boardWidth * boardHeight
        ):
            raise Exception("Invalid argument for violatesTriplesConstraint() function")

        pointerRight = col
        while (pointerRight+1 < boardWidth and board[row][pointerRight+1] == digit):
            pointerRight += 1
            if pointerRight - col + 1 >= 3:
                return True

        pointerLeft = col
        while(pointerLeft - 1>=0 and board[row][pointerLeft-1] == digit):
            pointerLeft -= 1
            if col - pointerLeft + 1 >= 3:
                return True

        if pointerRight - pointerLeft + 1 >= 3:
            return True

        pointerUp = row
        while (pointerUp - 1 >= 0 and board[pointerUp-1][col] == digit):
            pointerUp -= 1
            if row - pointerUp + 1 >= 3:
                return True

        pointerDown = row
        while (pointerDown+1 < boardHeight and board[pointerDown+1][col] == digit):
            pointerDown += 1
            if pointerDown - row + 1 >= 3:
                return True

        if pointerDown - pointerUp + 1 >= 3:
            return True

        return False

    def valid_move(self, x, y, num):
        return  x >= 0 and x < len(self.board[0]) and\
                y >= 0 and y < len(self.board) and\
                (num == 0 or num == 1) and\
                self.is_legal(x, y, num)

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
        if  x < 0 or x >= len(self.board[0]) or y < 0 or y >= len(self.board):
            print("= illegal move: " + " ".join(args) + " wrong coordinate\n")
            return False
        if args[2] != '0' and args[2] != '1':
            print("= illegal move: " + " ".join(args) + " wrong number\n")
            return False
        num = int(args[2])
        legal, reason = self.is_legal_reason(x, y, num)
        if not legal:
            print("= illegal move: " + " ".join(args) + " " + reason + "\n")
            return False
        self.board[y][x] = num

        # Increment row and column number of digits tracker
        col = x
        row = y
        self.numberOfDigitsInRow[row][num] += 1
        self.numberOfDigitsInCol[col][num] += 1
        self.zobristStateValue ^= self.zobristHashTable[len(self.board[0])*row+col][2 if num == None else num]
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
                    if self.is_legal(x, y, num):
                        moves.append([str(x), str(y), str(num)])
        return moves

    def genmove(self, args):
        moves = self.get_legal_moves()
        if len(moves) == 0:
            print("resign")
        else:
            is_win, move = self.solve(None)
            print(" ".join(move))
            print("Root Board State: \n")
            self.show(None)
            print("Is win: " + str(is_win))
            self.play(move)
        return True
    
    def winner(self, args):
        if len(self.get_legal_moves()) == 0:
            if self.player == 1:
                print(2)
            else:
                print(1)
        else:
            print("unfinished")
        return True
    
    # new function to be implemented for assignment 2
    def timelimit(self, args):
        self.timelimit = int(args[0])
        return True

    # new function to be implemented for assignment 3
    def solve(self, args):
        try:
            # Start timelimit
            signal.signal(signal.SIGALRM,self.onLimitReached)
            signal.alarm(self.timelimit)

            hashtable = {}
            
            legalMoves = self.get_legal_moves()

            rootBoard = copy.deepcopy(self.board)
            rootColDigits = copy.deepcopy(self.numberOfDigitsInCol)
            rootRowDigits = copy.deepcopy(self.numberOfDigitsInRow)
            rootStateHash = copy.deepcopy(self.zobristStateValue)
            
            if len(legalMoves) <= 0:
                signal.alarm(0)
                return None, random.choice(legalMoves)
            
            # Move Ordering
            legalMovesH = []

            for move in legalMoves:
                col = int(move[0])
                row = int(move[1])
                digit = int(move[2])
                legalMovesH.append(self.heuristic(row, col, digit))

            paired = list(zip(legalMovesH, legalMoves))
            paired.sort(key=lambda x: x[0], reverse=True)
            _, sorted_reflected = zip(*paired)
            legalMoves = list(sorted_reflected)
            
            for move in legalMoves:

                # Make move
                col = int(move[0])
                row = int(move[1])
                digit = int(move[2])
                self.board[row][col] = digit
                self.numberOfDigitsInRow[row][digit] += 1
                self.numberOfDigitsInCol[col][digit] += 1
                self.zobristStateValue ^= self.zobristHashTable[len(self.board[0])*row+col][2] ^ self.zobristHashTable[len(self.board[0])*row+col][2 if digit == None else digit]
                
                isWin = not self.negamax(hashtable)

                # undo move
                self.board[row][col] = None
                self.numberOfDigitsInRow[row][digit] -= 1
                self.numberOfDigitsInCol[col][digit] -= 1
                self.zobristStateValue ^= self.zobristHashTable[len(self.board[0])*row+col][2] ^ self.zobristHashTable[len(self.board[0])*row+col][2 if digit == None else digit]

                if isWin == True:
                    
                    # stop time limit
                    signal.alarm(0)
                    return True, move

            # stop time limit
            signal.alarm(0)
            return False, random.choice(legalMoves)

        except Exception as err:
            self.resetToRootState(rootBoard, rootRowDigits, rootColDigits, rootStateHash)
            return None, random.choice(legalMoves)

    def resetToRootState(self, rootBoard, rootRowDigits, rootColDigits, rootStateHash):
        self.board = rootBoard
        self.numberOfDigitsInRow = rootRowDigits
        self.numberOfDigitsInCol = rootColDigits
        self.zobristStateValue = rootStateHash

    def onLimitReached(self,number, stackframe):
        raise Exception("unknown")

    def getHashCode(self):
        return self.getZobristHashCode()

    def getZobristHashCode(self):
        return self.zobristStateValue

    def heuristic(self, row, col, digit):
        return self.numberOfDigitsInRow[row][digit] + self.numberOfDigitsInCol[col][digit] - (self.numberOfDigitsInRow[row][1 if digit == 0 else 0] + self.numberOfDigitsInRow[col][1 if digit == 0 else 0])
        
    # Returns true if the current player has a winning strategy
    def negamax(self, hashtable, alpha=-math.inf,):
        hashcode = self.getHashCode()
        

        if hashcode in hashtable:
            return hashtable[hashcode]

        legalMoves = self.get_legal_moves()
        
        # if len(legalMoves) <= 0:
        if not legalMoves:
            hashtable[hashcode] = False
            return False
        
        # Move Ordering
        legalMovesH = []

        for move in legalMoves:
            col = int(move[0])
            row = int(move[1])
            digit = int(move[2])
            legalMovesH.append(self.heuristic(row, col, digit))

        paired = list(zip(legalMovesH, legalMoves))
        paired.sort(key=lambda x: x[0], reverse=True)
        _, sorted_reflected = zip(*paired)
        legalMoves = list(sorted_reflected)

        for move in legalMoves:
            # Make Move
            col = int(move[0])
            row = int(move[1])
            digit = int(move[2])
            self.board[row][col] = digit
           
            self.numberOfDigitsInRow[row][digit] += 1
            self.numberOfDigitsInCol[col][digit] += 1
            self.zobristStateValue ^= self.zobristHashTable[len(self.board[0])*row+col][2] ^ self.zobristHashTable[len(self.board[0])*row+col][2 if digit == None else digit]

            isWin = not self.negamax(hashtable)

            # Undo Move
            self.board[row][col] = None
            self.numberOfDigitsInRow[row][digit] -= 1
            self.numberOfDigitsInCol[col][digit] -= 1
            self.zobristStateValue ^= self.zobristHashTable[len(self.board[0])*row+col][2] ^ self.zobristHashTable[len(self.board[0])*row+col][2 if digit == None else digit]

            if (isWin):
                hashtable[hashcode] = True
                return True
        
        hashtable[hashcode] = False
        return False
    
    #===============================================================================================
    # ɅɅɅɅɅɅɅɅɅɅ END OF ASSIGNMENT 2 FUNCTIONS. ɅɅɅɅɅɅɅɅɅɅ
    #===============================================================================================
    
if __name__ == "__main__":
    interface = CommandInterface()
    interface.main_loop()


cProfile.run('solve')
