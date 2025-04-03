import random as r
from .photo_create import show_board
from pathlib import Path
import os

main_path = os.getcwd() + "/"
main_path = Path(__file__).parent.__str__() + "\\"

circle = [(0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1)]
circle_gallop = [(-1, -2), (1, -2), (2, -1), (2, 1), (1, 2), (-1, 2), (-2, 1), (-2, -1)]
circle_24 = [[(0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1)],
             [(-1, -2), (1, -2), (2, -1), (2, 1), (1, 2), (-1, 2), (-2, 1), (-2, -1)],
             [(0, -2), (2, -2), (2, 0), (2, 2), (0, 2), (-2, 2), (-2, 0), (-2, -2)]]


def clone_list(arr) -> list:
    RT = []
    for i in arr:
        if isinstance(i, list):
            RT.append(clone_list(i))
        else:
            RT.append(i)
    return RT


class board:
    def __init__(self, board: int | list, H: int = None, dye: str = None, R: int = -1):
        if isinstance(board, int):
            if H is None:
                H = board
            self.board = [[None for _ in range(board)] for _ in range(H)]
            self.Size_N = board
            self.Size_H = H
            self.mines_R = R
        else:
            self.board = board
            self.Size_N = len(board[0])
            self.Size_H = len(board)
            self.mines_R = 0
            for row in self.board:
                for col in row:
                    if col is True:
                        self.mines_R += 1
        self.dye = [[False for _ in range(self.Size_N)] for _ in range(self.Size_H)]
        self.dye_model = dye
        if dye == '@c':
            for y in range(self.Size_H):
                for x in range(self.Size_N):
                    if (x + y) & 1:
                        self.dye[y][x] = True
        if dye == '@v':
            for y in range(self.Size_H):
                for x in range(self.Size_N, 2):
                    self.dye[y][x] = True
        if dye == '@h':
            for y in range(self.Size_H, 2):
                for x in range(self.Size_N):
                    self.dye[y][x] = True
        if dye == '@s':
            for y in range(self.Size_H):
                for x in range(self.Size_N):
                    if ((x + y + 2) >> 1) & 1:
                        self.dye[y][x] = True
        if dye == '@r':
            for y in range(self.Size_H):
                for x in range(self.Size_N):
                    self.dye[y][x] = (r.random() > 0.5)
        self.subord_board = [[None for _ in range(self.Size_N)] for _ in range(self.Size_H)]
        self.subord_board_I = []
        self.answer_board = False

    def __eq__(self, other):
        if isinstance(other, board):
            return (self.board == other.board)
        return False

    def __str__(self):
        Q_str = ''
        for row in self.board:
            for col in row:
                if col is True:
                    Q_str += ' F____'
                elif col is False:
                    Q_str += ' ?____'
                elif col is None:
                    Q_str += ' _____'
                else:
                    Q_str += ' ' + str(col) + '_' * (5 - len(str(col)))
            Q_str += '\n'
        #print(Q_str)
        return Q_str

    def __call__(self, model: str = 'all'):
        from . import clue
        for y in range(self.Size_H):
            for x in range(self.Size_N):
                if model == 'all':
                    yield ((x, y), self.board[y][x])
                else:
                    if (self.board[y][x] is None) and ('N' in model):
                        yield ((x, y), None)
                    elif (self.board[y][x] is True) and ('F' in model):
                        yield ((x, y), True)
                    elif (self.board[y][x] is False) and ('X' in model):
                        yield ((x, y), False)
                    elif (isinstance(self.board[y][x], clue.clue)) and ('C' in model):
                        yield (x, y), self.board[y][x]

    def create_photo(self, output_name='output.png', size=60, mini_bool: bool = True):
        from . import clue
        data = [['' for _ in range(self.Size_N)] for _ in range(self.Size_H)]
        mini_data = [['ABCDEFGHIJKLMNOPQRST'[x] + str(y + 1) for x in range(self.Size_N)] for y in range(self.Size_H)]
        for pos, value in self():
            if value == False:
                data[pos[1]][pos[0]] = '?'
                mini_data[pos[1]][pos[0]] = ''
            elif value == True:
                data[pos[1]][pos[0]] = 'F'
                mini_data[pos[1]][pos[0]] = ''
            elif (isinstance(value, clue.clue)):
                value = str(value).split('(')
                data[pos[1]][pos[0]] = value[0]
                if mini_bool:
                    mini_data[pos[1]][pos[0]] = value[1][:-1]
                else:
                    mini_data[pos[1]][pos[0]] = ''
        output_path = main_path + output_name
        show_board.generate_grid_image(data=data, mini_data=mini_data, dye=self.dye, output_path=output_path,
                                       font_size=size)

    def create_txt(self, output_name='output.txt', rules=[]):
        board_txt = str(self.Size_N) + '*' + str(self.Size_H) + '\n'
        if ('R' in rules) or ('1B' in rules) or ('2B' in rules):
            board_txt += 'R=' + str(self.mines_R) + '\n'
        rules_txt = ''
        for rl in rules:
            if rl != 'R':
                rules_txt += '[' + rl + ']'
        if rules_txt:
            board_txt += rules_txt + '\n'
        if self.dye_model in ['@c', '@s', '@h', '@v']:
            board_txt += '[' + self.dye_model + ']\n'
        elif self.dye_model == '@r':
            board_txt += '[@r]\n'
            for y in range(self.Size_H):
                for x in range(self.Size_N):
                    if self.dye[y][x]:
                        board_txt += 'W'
                    else:
                        board_txt += 'B'
                board_txt = board_txt + '\n'

        for y in range(self.Size_H):
            for x in range(self.Size_N):
                if self.board[y][x] is None:
                    board_txt += '_ '
                elif self.board[y][x] is False:
                    board_txt += '? '
                elif self.board[y][x] is True:
                    board_txt += 'F '
                else:
                    board_txt += str(self.board[y][x]) + ' '
            board_txt = board_txt[:-1] + '\n'
        with open(main_path + output_name, "w") as txt_file:
            txt_file.write(board_txt)
            print(main_path + output_name + ' 已生成')

    def has_None(self):
        try:
            for pos, value in self('N'):
                break
            else:
                return True
        except:
            return True
        return False

    def get_pos(self, pos: tuple):
        if -1 < pos[0] < self.Size_N and -1 < pos[1] < self.Size_H:
            return self.board[pos[1]][pos[0]]
        return 'off board'

    def get_subord_pos(self, pos: tuple):
        if -1 < pos[0] < self.Size_N and -1 < pos[1] < self.Size_H:
            return self.subord_board[pos[1]][pos[0]]
        return 'off board'

    def get_dye(self, pos: tuple):
        if -1 < pos[0] < self.Size_N and -1 < pos[1] < self.Size_H:
            return self.dye[pos[1]][pos[0]]
        return 'off board'

    def set_pos(self, pos: tuple, value):
        if -1 < pos[0] < self.Size_N and -1 < pos[1] < self.Size_H:
            self.board[pos[1]][pos[0]] = value
            return True
        return False

    def set_subord_pos(self, pos: tuple, value):
        if -1 < pos[0] < self.Size_N and -1 < pos[1] < self.Size_H:
            self.subord_board[pos[1]][pos[0]] = value
            return True
        return False

    def clone(self):
        board_c = board(clone_list(self.board))
        board_c.dye = self.dye
        board_c.mines_R = self.mines_R
        board_c.subord_board = clone_list(self.subord_board)
        board_c.subord_board_I = self.subord_board_I
        return board_c

    def random(self, clue_list: list = ['V'], R: int = None, rules: list = [], str_board: list[str] = False):
        from . import clue
        from . import rule
        if R == None:
            R = ((self.Size_N * self.Size_H + 1) << 1) // 5
            self.mines_R = R
        elif R < 0 or self.Size_N * self.Size_H < R:
            return False
        else:
            self.mines_R = R
        while True:
            R = self.mines_R
            Space_pos = []
            liar_pos = []
            for clue_name in range(len(clue_list) - 1, -1, -1):
                if '2I' in clue_list[clue_name]:
                    self.subord_board_I = [_ for _ in range(8)]
                    self.subord_board_I.pop(r.randint(0, 7))
                if ('2L' in clue_list[clue_name]):
                    if self.Size_N == self.Size_H:
                        row = [_ for _ in range(self.Size_N)]
                        for i in range(self.Size_N):
                            K = row.pop(r.randint(0, self.Size_N - i - 1))
                            for j in range(self.Size_N):
                                self.set_subord_pos((i, j), False)
                            liar_pos.append((i, K))
                            self.set_subord_pos((i, K), True)
                            self.set_pos((i, K), False)
                    else:
                        clue_list.pop(clue_name)
            for pos, value in self('N'):
                Space_pos.append(pos)
            i = 0
            board_stack = []
            while i < R and not (str_board):
                for rl in rules:
                    self.board = rl.r_check(self)
                new_mines = 0
                new_Space_pos = []
                for pos, value in self('NF'):
                    if value is None:
                        new_Space_pos.append(pos)
                    elif value is True:
                        new_mines += 1
                if new_mines == i and new_Space_pos == Space_pos:
                    try:
                        x, y = Space_pos.pop(r.randint(0, len(Space_pos) - 1))
                    except:
                        i = 0
                        board_recall, x, y = board_stack.pop()
                        self.board = board_recall.board
                        if x >= 0:
                            self.board[y][x] = False
                        continue
                    self.board[y][x] = True
                    i += 1
                    board_stack.append((self.clone(), x, y))
                else:
                    i = new_mines
                    Space_pos = new_Space_pos
                    for rl in rules:
                        if not (rl.easy_check(self)):
                            i = 0
                            board_recall, x, y = board_stack.pop()
                            self.board = board_recall.board
                            if x >= 0:
                                self.board[y][x] = False
                            break
                if i >= R:
                    if i == R:
                        for pos, _ in self('N'):
                            self.board[pos[1]][pos[0]] = False
                        for rl in rules:
                            if not (rl.easy_check(self)):
                                i = 0
                                board_recall, x, y = board_stack.pop()
                                self.board = board_recall.board
                                if x >= 0:
                                    self.board[y][x] = False
                                else:
                                    board_stack = [(self.clone(), -1, -1)]
                                break
                    else:
                        i = 0
                        board_recall, x, y = board_stack.pop()
                        self.board = board_recall.board
                        if x >= 0:
                            self.board[y][x] = False
                        else:
                            board_stack = [(self.clone(), -1, -1)]
                print(self)
                print(len(board_stack))
            if str_board:
                for y in range(self.Size_H):
                    for x in range(self.Size_N):
                        if str_board[y][x] == 'F':
                            self.set_pos((x, y), True)
            for pos, value in self('NX'):
                clue_choice = clue.find_clue(r.choice(clue_list))
                clue_choice.create_self(pos, self)
                self.set_pos(pos, clue_choice)
            self.answer_board = clone_list(self.board)
            for rl in rules:
                if not (rl.easy_check(self)):
                    break
            else:
                self.subord_board = [[None for _ in range(self.Size_N)] for _ in range(self.Size_H)]
                self.subord_board_I = []
                for pos, value in self('F'):
                    self.set_pos(pos, None)
                break
            self.board = [[None for _ in range(self.Size_N)] for _ in range(self.Size_H)]
            self.subord_board = [[None for _ in range(self.Size_N)] for _ in range(self.Size_H)]
            self.subord_board_I = []
            #input()
        if liar_pos:
            return liar_pos
        return True


def encode_txt_to_board(input='input.txt') -> tuple[board, list[str]]:
    from . import clue
    with open(main_path + input, 'r') as txt_file:
        str_B = []
        for line in txt_file:
            str_B.append(line[:-1])
    #print(str_B)
    szN, szH = str_B.pop(0).split('*')
    szN, szH = int(szN), int(szH)
    mines_R = -1
    if str_B[0][0] == 'R':
        mines_R = int(str_B.pop(0)[2:])
    rules = []
    for rl in str_B.pop(0)[1:-1].split(']['):
        rules.append(rl)
    dye_model = '@'
    if str_B[0][0] == '[':
        dye_model = str_B.pop(0)[1:-1]
    RT_board = board(board=szN, H=szH, dye=dye_model, R=mines_R)
    if dye_model == '@r':
        for y in range(szH):
            dye_line = str_B.pop(0)
            for x in range(szN):
                RT_board.dye[y][x] = (dye_line[x] == 'W')
    for y in range(szH):
        line = str_B.pop(0).split()
        for x in range(szN):
            if line[x] == 'F':
                RT_board.set_pos((x, y), True)
            elif line[x] == '?':
                RT_board.set_pos((x, y), False)
            elif line[x][-1] == ')':
                clue_value, clue_type = line[x][:-1].split('(')
                if '_' in clue_value or clue_type == '1W':
                    clue_value_list = clue_value.split('_')
                    clue_value = []
                    for i in clue_value_list:
                        clue_value.append(int(i))
                else:
                    clue_value = int(clue_value)
                clue_type = clue.find_clue(clue_type)
                clue_type.value = clue_value
                RT_board.set_pos((x, y), clue_type)
    return RT_board, rules
