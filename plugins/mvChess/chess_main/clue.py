from .class_board import board
from random import randint, choice

rainbow_1 = ['V', '1M', '1W', '1N', '1X', '1P', '1L', '1E']
rainbow_sp_1 = ['V', '1M', '1W', '1N', '1X', '1P', '1K', '1L', '1E', '1M1L', '1M1X', '1M1N', '1N1X', '1X\'', '1W\'',
                '1E\'']
rainbow_2 = ['V', '2X', '2D', '2M', '2P']
created = ['MNX', '1L1N', '2V^', '2M1M', '2X1X']
JS = ['2I1K', 'J_3S', 'J_3N', 'J_3P']
all_list = ['V', '1M', '1W', '1N', '1X', '1P', '1K', '1L', '1E', '1L1M', '1M1X', '1M1N', '1N1X', '1X\'', '1W\'', '1E\'',
            '2X', '2D', '2M', '2P', '2I', 'MNX', '1L1N', '2V^']


def full_permu(N, R, record_bool=True, record=[]):
    if record_bool:
        record = [[False for _ in range(R + 1)] for _ in range(N + 1)]
    elif record[N][R]:
        return record[N][R]
    if R == 0:
        record[N][R] = [0]
        return [0]
    if R == N:
        record[N][R] = [(1 << N) - 1]
        return [(1 << N) - 1]
    strs = []
    if N & 1:
        strs = full_permu(N - 1, R, False, record)
        for i in full_permu(N - 1, R - 1, False, record):
            strs.append((1 << (N - 1)) + i)
        record[N][R] = strs[:]
        return strs
    for i in range(max(R - (N >> 1), 0), min((N >> 1), R) + 1):
        K = full_permu((N >> 1), R - i, False, record)
        for j in full_permu((N >> 1), i, False, record):
            for k in K:
                strs.append((j << (N >> 1)) + k)
    record[N][R] = strs[:]
    return strs


def find_clue(clue_str: str):
    match clue_str:
        case 'V':
            return clue_V(-1)
        case '1M':
            return clue_1M(-1)
        case '1W':
            return clue_1W([])
        case '1N':
            return clue_1N(-1)
        case '1X':
            return clue_1X(-1)
        case '1P':
            return clue_1P(-1)
        case '1K':
            return clue_1K(-1)
        case '1L':
            return clue_1L(-1)
        case '1E':
            return clue_1E(-1)
        case '1L1M':
            return clue_1L1M(-1)
        case '1M1X':
            return clue_1M1X(-1)
        case '1M1N':
            return clue_1M1N(-1)
        case '1N1X':
            return clue_1N1X(-1)
        case '1W\'':
            return clue_1W_sp([])
        case '1X\'':
            return clue_1X_sp(-1)
        case 'MNX':
            return clue_MNX(-1)
        case '1L1N':
            return clue_1L1N(-1)
        case '1E\'':
            return clue_1E_sp(-1)
        case '2X':
            return clue_2X([-1, -1])
        case '2D':
            return clue_2D(-1)
        case '2M':
            return clue_2M(-1)
        case '2P':
            return clue_2P(-1)
        case '2L':
            return clue_2L(-1)
        case '2I':
            return clue_2I(-1)
        case '2X\'':
            return clue_2X_sp(-1)
        case '2Q':
            return clue_2Q(-1)
        case '2Q1K':
            return clue_2Q1K(-1)
        case '2I1K':
            return clue_2I1K(-1)
        case '2M1M':
            return clue_2M1M(-1)
        case '2X1X':
            return clue_2X1X(-1)
        case '2V^':
            return clue_2V_up([-1, -1])
        case 'J_3S':
            return clue_J_3S([-1, -1])
        case 'J_3N':
            return clue_J_3N(-1)
        case 'J_3P':
            return clue_J_3P(-1)
        case '1#':
            return find_clue(choice(rainbow_1))
        case '1#\'':
            return find_clue(choice(rainbow_sp_1))
        case '2#':
            return find_clue(choice(rainbow_2))
        case '自创':
            return find_clue(choice(created))
        case 'JS':
            return find_clue(choice(JS))
        case 'all':
            return find_clue(choice(all_list))
        case 'tem':
            return clue_tem(-2)


class clue:
    def weak(self):
        if isinstance(self, (clue_2X_sp, clue_1P, clue_1L1N, clue_2M, clue_2V_up, clue_2M1M, clue_2Q)):
            return True
        return False

    def __and__(self, other: bool):
        if other:
            return self
        return False


class clue_V(clue):
    def __init__(self, value: int):
        self.value = value
        self.circle = [(0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1)]

    def __str__(self):
        return str(self.value) + '(V)'

    def permu(self, Space_num, Flag_num):
        if Space_num + Flag_num < self.value or Flag_num > self.value:
            return []
        return full_permu(Space_num, self.value - Flag_num)

    def near(self, pos: tuple, board: board, model: str = 'nearby'):
        if model == 'nearby':
            nearby = []
            for xi, yi in self.circle:
                neighbor = board.get_pos((pos[0] + xi, pos[1] + yi))
                nearby.append(neighbor)
            return nearby
        if model == 'sf':
            Space = []
            Flag_num = 0
            for xi, yi in self.circle:
                neighbor = board.get_pos((pos[0] + xi, pos[1] + yi))
                if neighbor is None:
                    Space.append((pos[0] + xi, pos[1] + yi))
                if neighbor is True:
                    Flag_num += 1
            return (Space, Flag_num)

    def create_self(self, pos: tuple, board: board):
        nearby = self.near(pos, board, 'sf')
        self.value = nearby[1]

    def permution(self, pos: tuple, board: board):
        nearby = self.near(pos, board, 'sf')
        Space_num = len(nearby[0])
        Flag_num = nearby[1]
        poss = []
        if Space_num + Flag_num < self.value or Flag_num > self.value:
            return False
        pem = self.permu(Space_num, Flag_num)
        for i in pem:
            poss.append(board.clone())
            for space_pos in nearby[0]:
                if i & 1:
                    poss[-1].set_pos(space_pos, True)
                else:
                    poss[-1].set_pos(space_pos, False)
                i >>= 1
        return poss


class clue_2V_up(clue):
    def __init__(self, value: list[int]):
        self.value = value
        self.circle = [(0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1)]

    def __str__(self):
        return str(self.value[0]) + '_' + str(self.value[1]) + '(2V^)'

    def permu(self, Space_num, Flag_num):
        RT = []
        if Space_num + Flag_num >= self.value[0] >= Flag_num:
            RT += full_permu(Space_num, self.value[0] - Flag_num)
        if Space_num + Flag_num >= self.value[1] >= Flag_num:
            RT += full_permu(Space_num, self.value[1] - Flag_num)
        return RT

    def near(self, pos: tuple, board: board, model: str = 'nearby'):
        if model == 'nearby':
            nearby = []
            for xi, yi in self.circle:
                neighbor = board.get_pos((pos[0] + xi, pos[1] + yi))
                nearby.append(neighbor)
            return nearby
        if model == 'sf':
            Space = []
            Flag_num = 0
            for xi, yi in self.circle:
                neighbor = board.get_pos((pos[0] + xi, pos[1] + yi))
                if neighbor is None:
                    Space.append((pos[0] + xi, pos[1] + yi))
                if neighbor is True:
                    Flag_num += 1
            return (Space, Flag_num)

    def create_self(self, pos: tuple, board: board):
        nearby = self.near(pos, board, 'sf')
        NB = self.near(pos, board)
        fake = len(self.circle)
        for i in NB:
            if i == 'off board':
                fake -= 1
        MB = [_ for _ in range(0, fake)]
        try:
            MB.pop(nearby[1])
        except:
            pass
        self.value = sorted([nearby[1], choice(MB)])

    def permution(self, pos: tuple, board: board):
        nearby = self.near(pos, board, 'sf')
        Space_num = len(nearby[0])
        Flag_num = nearby[1]
        poss = []
        pem = self.permu(Space_num, Flag_num)
        for i in pem:
            poss.append(board.clone())
            for space_pos in nearby[0]:
                if i & 1:
                    poss[-1].set_pos(space_pos, True)
                else:
                    poss[-1].set_pos(space_pos, False)
                i >>= 1
        return poss


class clue_1M(clue):
    def __init__(self, value: int):
        self.value = value
        self.circle = [(0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1)]

    def __str__(self):
        return str(self.value) + '(1M)'

    def permu(self, W_Space: int, B_Space: int, W_Flag: int, B_Flag: int):
        Flag_num = (W_Flag << 1) + B_Flag
        RT = []
        for i in range(W_Space + 1):
            if self.value - Flag_num - (i << 1) < 0 or self.value - Flag_num - (i << 1) > B_Space:
                continue
            RT.append((full_permu(W_Space, i), full_permu(B_Space, self.value - Flag_num - (i << 1))))
        return RT

    def near(self, pos: tuple, board: board, model: str = 'nearby'):
        if model == 'nearby':
            nearby = []
            for xi, yi in self.circle:
                neighbor = board.get_pos((pos[0] + xi, pos[1] + yi))
                neighbor_dye = board.get_dye((pos[0] + xi, pos[1] + yi))
                nearby.append((neighbor, neighbor_dye))
            return nearby
        if model == 'sf':
            W_Space = []
            B_Space = []
            W_Flag = 0
            B_Flag = 0
            for xi, yi in self.circle:
                neighbor = board.get_pos((pos[0] + xi, pos[1] + yi))
                neighbor_dye = board.get_dye((pos[0] + xi, pos[1] + yi))
                if neighbor is None:
                    if neighbor_dye:
                        W_Space.append((pos[0] + xi, pos[1] + yi))
                    else:
                        B_Space.append((pos[0] + xi, pos[1] + yi))
                if neighbor is True:
                    if neighbor_dye:
                        W_Flag += 1
                    else:
                        B_Flag += 1
            return (W_Space, B_Space, W_Flag, B_Flag)

    def create_self(self, pos: tuple, board: board):
        nearby = self.near(pos, board, 'sf')
        self.value = (nearby[2] * 2) + nearby[3]

    def permution(self, pos: tuple, board: board):
        W_Space, B_Space, W_Flag, B_Flag = self.near(pos, board, 'sf')
        pem = self.permu(len(W_Space), len(B_Space), W_Flag, B_Flag)
        poss = []
        for Wpem, Bpem in pem:
            for Wi in Wpem:
                step_W = board.clone()
                for space_pos in W_Space:
                    if Wi & 1:
                        step_W.set_pos(space_pos, True)
                    else:
                        step_W.set_pos(space_pos, False)
                    Wi >>= 1
                for Bi in Bpem:
                    step_B = step_W.clone()
                    for space_pos in B_Space:
                        if Bi & 1:
                            step_B.set_pos(space_pos, True)
                        else:
                            step_B.set_pos(space_pos, False)
                        Bi >>= 1
                    poss.append(step_B.clone())
        return poss


class clue_1W(clue):
    def __init__(self, value: list[int]):
        self.value = value
        self.par = len(value)
        self.circle = [(0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1)]

    def __str__(self):
        S = ''
        for i in self.value:
            S += str(i) + '_'
        if S == '':
            S = '0'
        else:
            S = S[:-1]
        return S + '(1W)'

    def permu(self, nearby: list):
        poss = full_permu(len(self.circle), sum(self.value))
        for i in range(len(self.circle)):
            new_poss = []
            if nearby[i] is True:
                for j in poss:
                    if ((j >> i) & 1) == 1:
                        new_poss.append(j)
            elif nearby[i] is not None:
                for j in poss:
                    if ((j >> i) & 1) == 0:
                        new_poss.append(j)
            else:
                continue
            poss = new_poss[:]
        new_poss = []
        for i in poss:
            poss_i = i
            Ivalue = []
            for j in range(len(self.circle)):
                if (poss_i >> j) & 1:
                    queue = [j]
                    for k in queue:
                        poss_i -= (1 << k)
                        if (poss_i >> ((k + 1) % len(self.circle))) & 1:
                            queue.append((k + 1) % len(self.circle))
                        if (poss_i >> ((k - 1) % len(self.circle))) & 1:
                            queue.append((k - 1) % len(self.circle))
                    Ivalue.append(len(queue))
            Ivalue.sort()
            if Ivalue == self.value:
                new_poss.append(i)
        return new_poss

    def near(self, pos: tuple, board: board, model: str = 'nearby'):
        if model == 'nearby':
            nearby = []
            for xi, yi in self.circle:
                neighbor = board.get_pos((pos[0] + xi, pos[1] + yi))
                nearby.append(neighbor)
            return nearby
        if model == 'sf':
            Space = []
            Flag_num = 0
            for xi, yi in self.circle:
                neighbor = board.get_pos((pos[0] + xi, pos[1] + yi))
                if neighbor is None:
                    Space.append((pos[0] + xi, pos[1] + yi))
                if neighbor is True:
                    Flag_num += 1
            return (Space, Flag_num)

    def create_self(self, pos: tuple, board: board):
        nearby = self.near(pos, board)
        self.value = []
        self.par = 0
        for i in range(len(self.circle)):
            if nearby[i] is True:
                queue = [i]
                for j in queue:
                    nearby[j] = False
                    if nearby[(j - 1) % len(self.circle)] is True:
                        queue.append(j - 1)
                    if nearby[(j + 1) % len(self.circle)] is True:
                        queue.append(j + 1)
                self.value.append(len(queue))
                self.par += 1
        self.value.sort()

    def permution(self, pos: tuple, board: board):
        nearby = self.near(pos, board)
        pem = self.permu(nearby)
        poss = []
        for i in pem:
            poss.append(board.clone())
            for j in range(len(self.circle)):
                if nearby[j] is None:
                    if i & 1:
                        poss[-1].set_pos((pos[0] + self.circle[j][0], pos[1] + self.circle[j][1]), True)
                    else:
                        poss[-1].set_pos((pos[0] + self.circle[j][0], pos[1] + self.circle[j][1]), False)
                i >>= 1
        return poss


class clue_1N(clue):
    def __init__(self, value: int):
        self.value = value
        self.circle = [(0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1)]

    def __str__(self):
        return str(self.value) + '(1N)'

    def permu(self, W_Space: int, B_Space: int, W_Flag: int, B_Flag: int):
        RT = []
        if self.value == 0:
            for i in range(W_Space + 1):
                if W_Flag + i - B_Flag < 0 or W_Flag + i - B_Flag > B_Space:
                    continue
                RT.append((full_permu(W_Space, i), full_permu(B_Space, W_Flag + i - B_Flag)))
        else:
            for i in range(W_Space + 1):
                if W_Flag + i < B_Flag + self.value or W_Flag + i > B_Flag + B_Space + self.value:
                    continue
                RT.append((full_permu(W_Space, i), full_permu(B_Space, W_Flag + i - B_Flag - self.value)))
            for i in range(W_Space + 1):
                if W_Flag + i < B_Flag - self.value or W_Flag + i > B_Flag + B_Space - self.value:
                    continue
                RT.append((full_permu(W_Space, i), full_permu(B_Space, W_Flag + i - B_Flag + self.value)))
        return RT

    def near(self, pos: tuple, board: board, model: str = 'nearby'):
        if model == 'nearby':
            nearby = []
            for xi, yi in self.circle:
                neighbor = board.get_pos((pos[0] + xi, pos[1] + yi))
                neighbor_dye = board.get_dye((pos[0] + xi, pos[1] + yi))
                nearby.append((neighbor, neighbor_dye))
            return nearby
        if model == 'sf':
            W_Space = []
            B_Space = []
            W_Flag = 0
            B_Flag = 0
            for xi, yi in self.circle:
                neighbor = board.get_pos((pos[0] + xi, pos[1] + yi))
                neighbor_dye = board.get_dye((pos[0] + xi, pos[1] + yi))
                if neighbor is None:
                    if neighbor_dye:
                        W_Space.append((pos[0] + xi, pos[1] + yi))
                    else:
                        B_Space.append((pos[0] + xi, pos[1] + yi))
                if neighbor is True:
                    if neighbor_dye:
                        W_Flag += 1
                    else:
                        B_Flag += 1
            return (W_Space, B_Space, W_Flag, B_Flag)

    def create_self(self, pos: tuple, board: board):
        nearby = self.near(pos, board, 'sf')
        self.value = abs(nearby[3] - nearby[2])

    def permution(self, pos: tuple, board: board):
        W_Space, B_Space, W_Flag, B_Flag = self.near(pos, board, 'sf')
        pem = self.permu(len(W_Space), len(B_Space), W_Flag, B_Flag)
        poss = []
        for Wpem, Bpem in pem:
            for Wi in Wpem:
                step_W = board.clone()
                for space_pos in W_Space:
                    if Wi & 1:
                        step_W.set_pos(space_pos, True)
                    else:
                        step_W.set_pos(space_pos, False)
                    Wi >>= 1
                for Bi in Bpem:
                    step_B = step_W.clone()
                    for space_pos in B_Space:
                        if Bi & 1:
                            step_B.set_pos(space_pos, True)
                        else:
                            step_B.set_pos(space_pos, False)
                        Bi >>= 1
                    poss.append(step_B.clone())
        return poss


class clue_1X(clue):
    def __init__(self, value):
        self.value = value
        self.circle = [(0, -1), (0, -2), (1, 0), (2, 0), (0, 1), (0, 2), (-1, 0), (-2, 0)]

    def __str__(self):
        return str(self.value) + '(1X)'

    def permu(self, Space_num, Flag_num):
        if Space_num + Flag_num < self.value or Flag_num > self.value:
            return []
        return full_permu(Space_num, self.value - Flag_num)

    def near(self, pos: tuple, board: board, model: str = 'nearby'):
        if model == 'nearby':
            nearby = []
            for xi, yi in self.circle:
                neighbor = board.get_pos((pos[0] + xi, pos[1] + yi))
                nearby.append(neighbor)
            return nearby
        if model == 'sf':
            Space = []
            Flag_num = 0
            for xi, yi in self.circle:
                neighbor = board.get_pos((pos[0] + xi, pos[1] + yi))
                if neighbor is None:
                    Space.append((pos[0] + xi, pos[1] + yi))
                if neighbor is True:
                    Flag_num += 1
            return (Space, Flag_num)

    def create_self(self, pos: tuple, board: board):
        nearby = self.near(pos, board, 'sf')
        self.value = nearby[1]

    def permution(self, pos: tuple, board: board):
        nearby = self.near(pos, board, 'sf')
        Space_num = len(nearby[0])
        Flag_num = nearby[1]
        poss = []
        if Space_num + Flag_num < self.value or Flag_num > self.value:
            return False
        pem = self.permu(Space_num, Flag_num)
        for i in pem:
            poss.append(board.clone())
            for space_pos in nearby[0]:
                if i & 1:
                    poss[-1].set_pos(space_pos, True)
                else:
                    poss[-1].set_pos(space_pos, False)
                i >>= 1
        return poss


class clue_1P(clue):
    def __init__(self, value: list[int]):
        self.value = value
        self.circle = [(0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1)]

    def __str__(self):
        return str(self.value) + '(1P)'

    def permu(self, nearby: list):
        poss = []
        if self.value > 1:
            for i in range(self.value, len(self.circle) - self.value + 1):
                poss += full_permu(len(self.circle), i)
        elif self.value == 1:
            for i in range(1, len(self.circle)):
                poss += full_permu(len(self.circle), i)
        elif self.value == 0:
            poss = [0]
        for i in range(len(self.circle)):
            new_poss = []
            if nearby[i] is True:
                for j in poss:
                    if ((j >> i) & 1) == 1:
                        new_poss.append(j)
            elif nearby[i] is not None:
                for j in poss:
                    if ((j >> i) & 1) == 0:
                        new_poss.append(j)
            else:
                continue
            poss = new_poss[:]
        new_poss = []
        for i in poss:
            poss_i = i
            Ivalue = 0
            for j in range(len(self.circle)):
                if (poss_i >> j) & 1:
                    queue = [j]
                    for k in queue:
                        poss_i -= (1 << k)
                        if (poss_i >> ((k + 1) % len(self.circle))) & 1:
                            queue.append((k + 1) % len(self.circle))
                        if (poss_i >> ((k - 1) % len(self.circle))) & 1:
                            queue.append((k - 1) % len(self.circle))
                    Ivalue += 1
            if Ivalue == self.value:
                new_poss.append(i)
        return new_poss

    def near(self, pos: tuple, board: board, model: str = 'nearby'):
        if model == 'nearby':
            nearby = []
            for xi, yi in self.circle:
                neighbor = board.get_pos((pos[0] + xi, pos[1] + yi))
                nearby.append(neighbor)
            return nearby
        if model == 'sf':
            Space = []
            Flag_num = 0
            for xi, yi in self.circle:
                neighbor = board.get_pos((pos[0] + xi, pos[1] + yi))
                if neighbor is None:
                    Space.append((pos[0] + xi, pos[1] + yi))
                if neighbor is True:
                    Flag_num += 1
            return (Space, Flag_num)

    def create_self(self, pos: tuple, board: board):
        nearby = self.near(pos, board)
        self.value = 0
        for i in range(len(self.circle)):
            if nearby[i] is True:
                queue = [i]
                for j in queue:
                    nearby[j] = False
                    if nearby[(j - 1) % len(self.circle)] is True:
                        queue.append(j - 1)
                    if nearby[(j + 1) % len(self.circle)] is True:
                        queue.append(j + 1)
                self.value += 1

    def permution(self, pos: tuple, board: board):
        nearby = self.near(pos, board)
        pem = self.permu(nearby)
        poss = []
        for i in pem:
            poss.append(board.clone())
            for j in range(len(self.circle)):
                if nearby[j] is None:
                    if i & 1:
                        poss[-1].set_pos((pos[0] + self.circle[j][0], pos[1] + self.circle[j][1]), True)
                    else:
                        poss[-1].set_pos((pos[0] + self.circle[j][0], pos[1] + self.circle[j][1]), False)
                i >>= 1
        return poss


class clue_1W_sp(clue):
    def __init__(self, value: int):
        self.value = value
        self.par = len(value)
        self.circle = [(0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1)]

    def __str__(self):
        return str(self.value) + '(1W\')'

    def permu(self, nearby: list):
        poss = []
        for i in range(self.value,
                       max(len(self.circle) - (len(self.circle) + self.value) // (self.value + 1), self.value) + 1):
            poss += full_permu(len(self.circle), i)
        for i in range(len(self.circle)):
            new_poss = []
            if nearby[i] is True:
                for j in poss:
                    if ((j >> i) & 1) == 1:
                        new_poss.append(j)
            elif nearby[i] is not None:
                for j in poss:
                    if ((j >> i) & 1) == 0:
                        new_poss.append(j)
            else:
                continue
            poss = new_poss[:]
        new_poss = []
        for i in poss:
            poss_i = i
            Ivalue = 0
            for j in range(len(self.circle)):
                if (poss_i >> j) & 1:
                    queue = [j]
                    for k in queue:
                        poss_i -= (1 << k)
                        if (poss_i >> ((k + 1) % len(self.circle))) & 1:
                            queue.append((k + 1) % len(self.circle))
                        if (poss_i >> ((k - 1) % len(self.circle))) & 1:
                            queue.append((k - 1) % len(self.circle))
                    Ivalue = max(len(queue), Ivalue)
            if Ivalue == self.value:
                new_poss.append(i)
        return new_poss

    def near(self, pos: tuple, board: board, model: str = 'nearby'):
        if model == 'nearby':
            nearby = []
            for xi, yi in self.circle:
                neighbor = board.get_pos((pos[0] + xi, pos[1] + yi))
                nearby.append(neighbor)
            return nearby
        if model == 'sf':
            Space = []
            Flag_num = 0
            for xi, yi in self.circle:
                neighbor = board.get_pos((pos[0] + xi, pos[1] + yi))
                if neighbor is None:
                    Space.append((pos[0] + xi, pos[1] + yi))
                if neighbor is True:
                    Flag_num += 1
            return (Space, Flag_num)

    def create_self(self, pos: tuple, board: board):
        nearby = self.near(pos, board)
        self.value = 0
        self.par = 0
        for i in range(len(self.circle)):
            if nearby[i] is True:
                queue = [i]
                for j in queue:
                    nearby[j] = False
                    if nearby[(j - 1) % len(self.circle)] is True:
                        queue.append(j - 1)
                    if nearby[(j + 1) % len(self.circle)] is True:
                        queue.append(j + 1)
                self.value = max(len(queue), self.value)

    def permution(self, pos: tuple, board: board):
        nearby = self.near(pos, board)
        pem = self.permu(nearby)
        poss = []
        for i in pem:
            poss.append(board.clone())
            for j in range(len(self.circle)):
                if nearby[j] is None:
                    if i & 1:
                        poss[-1].set_pos((pos[0] + self.circle[j][0], pos[1] + self.circle[j][1]), True)
                    else:
                        poss[-1].set_pos((pos[0] + self.circle[j][0], pos[1] + self.circle[j][1]), False)
                i >>= 1
        return poss


class clue_1X_sp(clue):
    def __init__(self, value):
        self.value = value
        self.circle = [(0, -1), (1, 0), (0, 1), (-1, 0)]

    def __str__(self):
        return str(self.value) + '(1X\')'

    def permu(self, Space_num, Flag_num):
        if Space_num + Flag_num < self.value or Flag_num > self.value:
            return []
        return full_permu(Space_num, self.value - Flag_num)

    def near(self, pos: tuple, board: board, model: str = 'nearby'):
        if model == 'nearby':
            nearby = []
            for xi, yi in self.circle:
                neighbor = board.get_pos((pos[0] + xi, pos[1] + yi))
                nearby.append(neighbor)
            return nearby
        if model == 'sf':
            Space = []
            Flag_num = 0
            for xi, yi in self.circle:
                neighbor = board.get_pos((pos[0] + xi, pos[1] + yi))
                if neighbor is None:
                    Space.append((pos[0] + xi, pos[1] + yi))
                if neighbor is True:
                    Flag_num += 1
            return (Space, Flag_num)

    def create_self(self, pos: tuple, board: board):
        nearby = self.near(pos, board, 'sf')
        self.value = nearby[1]

    def permution(self, pos: tuple, board: board):
        nearby = self.near(pos, board, 'sf')
        Space_num = len(nearby[0])
        Flag_num = nearby[1]
        poss = []
        if Space_num + Flag_num < self.value or Flag_num > self.value:
            return False
        pem = self.permu(Space_num, Flag_num)
        for i in pem:
            poss.append(board.clone())
            for space_pos in nearby[0]:
                if i & 1:
                    poss[-1].set_pos(space_pos, True)
                else:
                    poss[-1].set_pos(space_pos, False)
                i >>= 1
        return poss


class clue_1K(clue):
    def __init__(self, value):
        self.value = value
        self.circle = [(-1, -2), (1, -2), (2, -1), (2, 1), (1, 2), (-1, 2), (-2, 1), (-2, -1)]

    def __str__(self):
        return str(self.value) + '(1K)'

    def permu(self, Space_num, Flag_num):
        if Space_num + Flag_num < self.value or Flag_num > self.value:
            return []
        return full_permu(Space_num, self.value - Flag_num)

    def near(self, pos: tuple, board: board, model: str = 'nearby'):
        if model == 'nearby':
            nearby = []
            for xi, yi in self.circle:
                neighbor = board.get_pos((pos[0] + xi, pos[1] + yi))
                nearby.append(neighbor)
            return nearby
        if model == 'sf':
            Space = []
            Flag_num = 0
            for xi, yi in self.circle:
                neighbor = board.get_pos((pos[0] + xi, pos[1] + yi))
                if neighbor is None:
                    Space.append((pos[0] + xi, pos[1] + yi))
                if neighbor is True:
                    Flag_num += 1
            return (Space, Flag_num)

    def create_self(self, pos: tuple, board: board):
        nearby = self.near(pos, board, 'sf')
        self.value = nearby[1]

    def permution(self, pos: tuple, board: board):
        nearby = self.near(pos, board, 'sf')
        Space_num = len(nearby[0])
        Flag_num = nearby[1]
        poss = []
        if Space_num + Flag_num < self.value or Flag_num > self.value:
            return False
        pem = self.permu(Space_num, Flag_num)
        for i in pem:
            poss.append(board.clone())
            for space_pos in nearby[0]:
                if i & 1:
                    poss[-1].set_pos(space_pos, True)
                else:
                    poss[-1].set_pos(space_pos, False)
                i >>= 1
        return poss


class clue_1L(clue):
    def __init__(self, value: int):
        self.value = value
        self.circle = [(0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1)]

    def __str__(self):
        return str(self.value) + '(1L)'

    def permu(self, Space_num, Flag_num):
        pem = []
        if Space_num + Flag_num < self.value - 1 or Flag_num > self.value - 1:
            pass
        else:
            pem += full_permu(Space_num, self.value - Flag_num - 1)
        if Space_num + Flag_num < self.value + 1 or Flag_num > self.value + 1:
            pass
        else:
            pem += full_permu(Space_num, self.value - Flag_num + 1)
        return pem

    def near(self, pos: tuple, board: board, model: str = 'nearby'):
        if model == 'nearby':
            nearby = []
            for xi, yi in self.circle:
                neighbor = board.get_pos((pos[0] + xi, pos[1] + yi))
                nearby.append(neighbor)
            return nearby
        if model == 'sf':
            Space = []
            Flag_num = 0
            for xi, yi in self.circle:
                neighbor = board.get_pos((pos[0] + xi, pos[1] + yi))
                if neighbor is None:
                    Space.append((pos[0] + xi, pos[1] + yi))
                if neighbor is True:
                    Flag_num += 1
            return (Space, Flag_num)

    def create_self(self, pos: tuple, board: board):
        nearby = self.near(pos, board, 'sf')
        self.value = abs(nearby[1] + (randint(0, 1) * 2 - 1))

    def permution(self, pos: tuple, board: board):
        nearby = self.near(pos, board, 'sf')
        Space_num = len(nearby[0])
        Flag_num = nearby[1]
        poss = []
        pem = self.permu(Space_num, Flag_num)
        for i in pem:
            poss.append(board.clone())
            for space_pos in nearby[0]:
                if i & 1:
                    poss[-1].set_pos(space_pos, True)
                else:
                    poss[-1].set_pos(space_pos, False)
                i >>= 1
        return poss


class clue_1E(clue):
    def __init__(self, value: int):
        self.value = value

    def __str__(self):
        return str(self.value) + '(1E)'

    def permu(self, Space: list, pos: int, length: int):
        poss = []
        for i in range(length + 1):
            if (pos - i - 1 < -1) or (pos - i + length > len(Space)) or (
                    pos - i - 1 > -1 and (Space[pos - i - 1] is False or isinstance(Space[pos - i - 1], clue))) or (
                    pos - i + length < len(Space) and (
                    Space[pos - i + length] is False or isinstance(Space[pos - i + length], clue))):
                continue
            for j in range(pos - i, pos - i + length):
                if Space[j] is True:
                    break
            else:
                poss.append((pos - i, pos - i + length))
        return poss

    def near(self, pos: tuple, board: board, model: str = 'nearby'):
        if model == 'nearby':
            nearby = []
        if model == 'sf':
            h_Space = []
            v_Space = []
            for xi in range(board.Size_N):
                h_Space.append(board.get_pos((xi, pos[1])))
            for yi in range(board.Size_H):
                v_Space.append(board.get_pos((pos[0], yi)))
            return (h_Space, v_Space, pos)

    def create_self(self, pos: tuple, board: board):
        self.value = 1
        for i in range(pos[1] - 1, -1, -1):
            if board.get_pos((pos[0], i)) is True:
                break
            self.value += 1
        for i in range(pos[1] + 1, board.Size_H):
            if board.get_pos((pos[0], i)) is True:
                break
            self.value += 1
        for i in range(pos[0] - 1, -1, -1):
            if board.get_pos((i, pos[1])) is True:
                break
            self.value += 1
        for i in range(pos[0] + 1, board.Size_N):
            if board.get_pos((i, pos[1])) is True:
                break
            self.value += 1

    def permution(self, pos: tuple, board: board):
        h_Space, v_Space, pos = self.near(pos, board, 'sf')
        poss = []
        for h_num in range(1, self.value + 1):
            h_pem = self.permu(h_Space, pos[0], h_num)
            v_pem = self.permu(v_Space, pos[1], self.value - h_num + 1)
            if h_pem and v_pem:
                for Hi in h_pem:
                    step_H = board.clone()
                    if step_H.get_pos((Hi[0] - 1, pos[1])) is None:
                        step_H.set_pos((Hi[0] - 1, pos[1]), True)
                    if step_H.get_pos((Hi[1], pos[1])) is None:
                        step_H.set_pos((Hi[1], pos[1]), True)
                    for j in range(Hi[0], Hi[1]):
                        if step_H.get_pos((j, pos[1])) is None:
                            step_H.set_pos((j, pos[1]), False)
                    for Vi in v_pem:
                        step_V = step_H.clone()
                        if step_V.get_pos((pos[0], Vi[0] - 1)) is None:
                            step_V.set_pos((pos[0], Vi[0] - 1), True)
                        if step_V.get_pos((pos[0], Vi[1])) is None:
                            step_V.set_pos((pos[0], Vi[1]), True)
                        for j in range(Vi[0], Vi[1]):
                            if step_V.get_pos((pos[0], j)) is None:
                                step_V.set_pos((pos[0], j), False)
                        poss.append(step_V.clone())
        return poss


class clue_1L1M(clue):
    def __init__(self, value: int):
        self.value = value
        self.circle = [(0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1)]

    def __str__(self):
        return str(self.value) + '(1L1M)'

    def permu(self, W_Space: int, B_Space: int, W_Flag: int, B_Flag: int):
        Flag_num = (W_Flag << 1) + B_Flag
        RT = []
        for i in range(W_Space + 1):
            if self.value - Flag_num - (i << 1) - 1 < 0 or self.value - Flag_num - (i << 1) - 1 > B_Space:
                continue
            RT.append((full_permu(W_Space, i), full_permu(B_Space, self.value - Flag_num - (i << 1) - 1)))
        for i in range(W_Space + 1):
            if self.value - Flag_num - (i << 1) + 1 < 0 or self.value - Flag_num - (i << 1) + 1 > B_Space:
                continue
            RT.append((full_permu(W_Space, i), full_permu(B_Space, self.value - Flag_num - (i << 1) + 1)))
        return RT

    def near(self, pos: tuple, board: board, model: str = 'nearby'):
        if model == 'nearby':
            nearby = []
            for xi, yi in self.circle:
                neighbor = board.get_pos((pos[0] + xi, pos[1] + yi))
                neighbor_dye = board.get_dye((pos[0] + xi, pos[1] + yi))
                nearby.append((neighbor, neighbor_dye))
            return nearby
        if model == 'sf':
            W_Space = []
            B_Space = []
            W_Flag = 0
            B_Flag = 0
            for xi, yi in self.circle:
                neighbor = board.get_pos((pos[0] + xi, pos[1] + yi))
                neighbor_dye = board.get_dye((pos[0] + xi, pos[1] + yi))
                if neighbor is None:
                    if neighbor_dye:
                        W_Space.append((pos[0] + xi, pos[1] + yi))
                    else:
                        B_Space.append((pos[0] + xi, pos[1] + yi))
                if neighbor is True:
                    if neighbor_dye:
                        W_Flag += 1
                    else:
                        B_Flag += 1
            return (W_Space, B_Space, W_Flag, B_Flag)

    def create_self(self, pos: tuple, board: board):
        nearby = self.near(pos, board, 'sf')
        self.value = abs((nearby[2] * 2) + nearby[3] + (randint(0, 1) * 2 - 1))

    def permution(self, pos: tuple, board: board):
        W_Space, B_Space, W_Flag, B_Flag = self.near(pos, board, 'sf')
        pem = self.permu(len(W_Space), len(B_Space), W_Flag, B_Flag)
        poss = []
        for Wpem, Bpem in pem:
            for Wi in Wpem:
                step_W = board.clone()
                for space_pos in W_Space:
                    if Wi & 1:
                        step_W.set_pos(space_pos, True)
                    else:
                        step_W.set_pos(space_pos, False)
                    Wi >>= 1
                for Bi in Bpem:
                    step_B = step_W.clone()
                    for space_pos in B_Space:
                        if Bi & 1:
                            step_B.set_pos(space_pos, True)
                        else:
                            step_B.set_pos(space_pos, False)
                        Bi >>= 1
                    poss.append(step_B.clone())
        return poss


class clue_1M1X(clue):
    def __init__(self, value: int):
        self.value = value
        self.circle = [(0, -1), (0, -2), (1, 0), (2, 0), (0, 1), (0, 2), (-1, 0), (-2, 0)]

    def __str__(self):
        return str(self.value) + '(1M1X)'

    def permu(self, W_Space: int, B_Space: int, W_Flag: int, B_Flag: int):
        Flag_num = (W_Flag << 1) + B_Flag
        RT = []
        for i in range(W_Space + 1):
            if self.value - Flag_num - (i << 1) < 0 or self.value - Flag_num - (i << 1) > B_Space:
                continue
            RT.append((full_permu(W_Space, i), full_permu(B_Space, self.value - Flag_num - (i << 1))))
        return RT

    def near(self, pos: tuple, board: board, model: str = 'nearby'):
        if model == 'nearby':
            nearby = []
            for xi, yi in self.circle:
                neighbor = board.get_pos((pos[0] + xi, pos[1] + yi))
                neighbor_dye = board.get_dye((pos[0] + xi, pos[1] + yi))
                nearby.append((neighbor, neighbor_dye))
            return nearby
        if model == 'sf':
            W_Space = []
            B_Space = []
            W_Flag = 0
            B_Flag = 0
            for xi, yi in self.circle:
                neighbor = board.get_pos((pos[0] + xi, pos[1] + yi))
                neighbor_dye = board.get_dye((pos[0] + xi, pos[1] + yi))
                if neighbor is None:
                    if neighbor_dye:
                        W_Space.append((pos[0] + xi, pos[1] + yi))
                    else:
                        B_Space.append((pos[0] + xi, pos[1] + yi))
                if neighbor is True:
                    if neighbor_dye:
                        W_Flag += 1
                    else:
                        B_Flag += 1
            return (W_Space, B_Space, W_Flag, B_Flag)

    def create_self(self, pos: tuple, board: board):
        nearby = self.near(pos, board, 'sf')
        self.value = (nearby[2] * 2) + nearby[3]

    def permution(self, pos: tuple, board: board):
        W_Space, B_Space, W_Flag, B_Flag = self.near(pos, board, 'sf')
        pem = self.permu(len(W_Space), len(B_Space), W_Flag, B_Flag)
        poss = []
        for Wpem, Bpem in pem:
            for Wi in Wpem:
                step_W = board.clone()
                for space_pos in W_Space:
                    if Wi & 1:
                        step_W.set_pos(space_pos, True)
                    else:
                        step_W.set_pos(space_pos, False)
                    Wi >>= 1
                for Bi in Bpem:
                    step_B = step_W.clone()
                    for space_pos in B_Space:
                        if Bi & 1:
                            step_B.set_pos(space_pos, True)
                        else:
                            step_B.set_pos(space_pos, False)
                        Bi >>= 1
                    poss.append(step_B.clone())
        return poss


class clue_1M1N(clue):
    def __init__(self, value: int):
        self.value = value
        self.circle = [(0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1)]

    def __str__(self):
        return str(self.value) + '(1M1N)'

    def permu(self, W_Space: int, B_Space: int, W_Flag: int, B_Flag: int):
        RT = []
        if self.value == 0:
            for i in range(W_Space + 1):
                if (W_Flag + i) * 2 - B_Flag < 0 or (W_Flag + i) * 2 - B_Flag > B_Space:
                    continue
                RT.append((full_permu(W_Space, i), full_permu(B_Space, (W_Flag + i) * 2 - B_Flag)))
        else:
            for i in range(W_Space + 1):
                if (W_Flag + i) * 2 < B_Flag + self.value or (W_Flag + i) * 2 > B_Flag + B_Space + self.value:
                    continue
                RT.append((full_permu(W_Space, i), full_permu(B_Space, (W_Flag + i) * 2 - B_Flag - self.value)))
            for i in range(W_Space + 1):
                if (W_Flag + i) * 2 < B_Flag - self.value or (W_Flag + i) * 2 > B_Flag + B_Space - self.value:
                    continue
                RT.append((full_permu(W_Space, i), full_permu(B_Space, (W_Flag + i) * 2 - B_Flag + self.value)))
        return RT

    def near(self, pos: tuple, board: board, model: str = 'nearby'):
        if model == 'nearby':
            nearby = []
            for xi, yi in self.circle:
                neighbor = board.get_pos((pos[0] + xi, pos[1] + yi))
                neighbor_dye = board.get_dye((pos[0] + xi, pos[1] + yi))
                nearby.append((neighbor, neighbor_dye))
            return nearby
        if model == 'sf':
            W_Space = []
            B_Space = []
            W_Flag = 0
            B_Flag = 0
            for xi, yi in self.circle:
                neighbor = board.get_pos((pos[0] + xi, pos[1] + yi))
                neighbor_dye = board.get_dye((pos[0] + xi, pos[1] + yi))
                if neighbor is None:
                    if neighbor_dye:
                        W_Space.append((pos[0] + xi, pos[1] + yi))
                    else:
                        B_Space.append((pos[0] + xi, pos[1] + yi))
                if neighbor is True:
                    if neighbor_dye:
                        W_Flag += 1
                    else:
                        B_Flag += 1
            return (W_Space, B_Space, W_Flag, B_Flag)

    def create_self(self, pos: tuple, board: board):
        nearby = self.near(pos, board, 'sf')
        self.value = abs(nearby[3] - (nearby[2] * 2))

    def permution(self, pos: tuple, board: board):
        W_Space, B_Space, W_Flag, B_Flag = self.near(pos, board, 'sf')
        pem = self.permu(len(W_Space), len(B_Space), W_Flag, B_Flag)
        poss = []
        for Wpem, Bpem in pem:
            for Wi in Wpem:
                step_W = board.clone()
                for space_pos in W_Space:
                    if Wi & 1:
                        step_W.set_pos(space_pos, True)
                    else:
                        step_W.set_pos(space_pos, False)
                    Wi >>= 1
                for Bi in Bpem:
                    step_B = step_W.clone()
                    for space_pos in B_Space:
                        if Bi & 1:
                            step_B.set_pos(space_pos, True)
                        else:
                            step_B.set_pos(space_pos, False)
                        Bi >>= 1
                    poss.append(step_B.clone())
        return poss


class clue_1N1X(clue):
    def __init__(self, value: int):
        self.value = value
        self.circle = [(0, -1), (0, -2), (1, 0), (2, 0), (0, 1), (0, 2), (-1, 0), (-2, 0)]

    def __str__(self):
        return str(self.value) + '(1N1X)'

    def permu(self, W_Space: int, B_Space: int, W_Flag: int, B_Flag: int):
        RT = []
        if self.value == 0:
            for i in range(W_Space + 1):
                if W_Flag + i - B_Flag < 0 or W_Flag + i - B_Flag > B_Space:
                    continue
                RT.append((full_permu(W_Space, i), full_permu(B_Space, W_Flag + i - B_Flag)))
        else:
            for i in range(W_Space + 1):
                if W_Flag + i < B_Flag + self.value or W_Flag + i > B_Flag + B_Space + self.value:
                    continue
                RT.append((full_permu(W_Space, i), full_permu(B_Space, W_Flag + i - B_Flag - self.value)))
            for i in range(W_Space + 1):
                if W_Flag + i < B_Flag - self.value or W_Flag + i > B_Flag + B_Space - self.value:
                    continue
                RT.append((full_permu(W_Space, i), full_permu(B_Space, W_Flag + i - B_Flag + self.value)))
        return RT

    def near(self, pos: tuple, board: board, model: str = 'nearby'):
        if model == 'nearby':
            nearby = []
            for xi, yi in self.circle:
                neighbor = board.get_pos((pos[0] + xi, pos[1] + yi))
                neighbor_dye = board.get_dye((pos[0] + xi, pos[1] + yi))
                nearby.append((neighbor, neighbor_dye))
            return nearby
        if model == 'sf':
            W_Space = []
            B_Space = []
            W_Flag = 0
            B_Flag = 0
            for xi, yi in self.circle:
                neighbor = board.get_pos((pos[0] + xi, pos[1] + yi))
                neighbor_dye = board.get_dye((pos[0] + xi, pos[1] + yi))
                if neighbor is None:
                    if neighbor_dye:
                        W_Space.append((pos[0] + xi, pos[1] + yi))
                    else:
                        B_Space.append((pos[0] + xi, pos[1] + yi))
                if neighbor is True:
                    if neighbor_dye:
                        W_Flag += 1
                    else:
                        B_Flag += 1
            return (W_Space, B_Space, W_Flag, B_Flag)

    def create_self(self, pos: tuple, board: board):
        nearby = self.near(pos, board, 'sf')
        self.value = abs(nearby[3] - nearby[2])

    def permution(self, pos: tuple, board: board):
        W_Space, B_Space, W_Flag, B_Flag = self.near(pos, board, 'sf')
        pem = self.permu(len(W_Space), len(B_Space), W_Flag, B_Flag)
        poss = []
        for Wpem, Bpem in pem:
            for Wi in Wpem:
                step_W = board.clone()
                for space_pos in W_Space:
                    if Wi & 1:
                        step_W.set_pos(space_pos, True)
                    else:
                        step_W.set_pos(space_pos, False)
                    Wi >>= 1
                for Bi in Bpem:
                    step_B = step_W.clone()
                    for space_pos in B_Space:
                        if Bi & 1:
                            step_B.set_pos(space_pos, True)
                        else:
                            step_B.set_pos(space_pos, False)
                        Bi >>= 1
                    poss.append(step_B.clone())
        return poss


class clue_MNX(clue):
    def __init__(self, value: int):
        self.value = value
        self.circle = [(0, -1), (0, -2), (1, 0), (2, 0), (0, 1), (0, 2), (-1, 0), (-2, 0)]

    def __str__(self):
        return str(self.value) + '(MNX)'

    def permu(self, W_Space: int, B_Space: int, W_Flag: int, B_Flag: int):
        RT = []
        if self.value == 0:
            for i in range(W_Space + 1):
                if (W_Flag + i) * 2 - B_Flag < 0 or (W_Flag + i) * 2 - B_Flag > B_Space:
                    continue
                RT.append((full_permu(W_Space, i), full_permu(B_Space, (W_Flag + i) * 2 - B_Flag)))
        else:
            for i in range(W_Space + 1):
                if (W_Flag + i) * 2 < B_Flag + self.value or (W_Flag + i) * 2 > B_Flag + B_Space + self.value:
                    continue
                RT.append((full_permu(W_Space, i), full_permu(B_Space, (W_Flag + i) * 2 - B_Flag - self.value)))
            for i in range(W_Space + 1):
                if (W_Flag + i) * 2 < B_Flag - self.value or (W_Flag + i) * 2 > B_Flag + B_Space - self.value:
                    continue
                RT.append((full_permu(W_Space, i), full_permu(B_Space, (W_Flag + i) * 2 - B_Flag + self.value)))
        return RT

    def near(self, pos: tuple, board: board, model: str = 'nearby'):
        if model == 'nearby':
            nearby = []
            for xi, yi in self.circle:
                neighbor = board.get_pos((pos[0] + xi, pos[1] + yi))
                neighbor_dye = board.get_dye((pos[0] + xi, pos[1] + yi))
                nearby.append((neighbor, neighbor_dye))
            return nearby
        if model == 'sf':
            W_Space = []
            B_Space = []
            W_Flag = 0
            B_Flag = 0
            for xi, yi in self.circle:
                neighbor = board.get_pos((pos[0] + xi, pos[1] + yi))
                neighbor_dye = board.get_dye((pos[0] + xi, pos[1] + yi))
                if neighbor is None:
                    if neighbor_dye:
                        W_Space.append((pos[0] + xi, pos[1] + yi))
                    else:
                        B_Space.append((pos[0] + xi, pos[1] + yi))
                if neighbor is True:
                    if neighbor_dye:
                        W_Flag += 1
                    else:
                        B_Flag += 1
            return (W_Space, B_Space, W_Flag, B_Flag)

    def create_self(self, pos: tuple, board: board):
        nearby = self.near(pos, board, 'sf')
        self.value = abs(nearby[3] - (nearby[2] * 2))

    def permution(self, pos: tuple, board: board):
        W_Space, B_Space, W_Flag, B_Flag = self.near(pos, board, 'sf')
        pem = self.permu(len(W_Space), len(B_Space), W_Flag, B_Flag)
        poss = []
        for Wpem, Bpem in pem:
            for Wi in Wpem:
                step_W = board.clone()
                for space_pos in W_Space:
                    if Wi & 1:
                        step_W.set_pos(space_pos, True)
                    else:
                        step_W.set_pos(space_pos, False)
                    Wi >>= 1
                for Bi in Bpem:
                    step_B = step_W.clone()
                    for space_pos in B_Space:
                        if Bi & 1:
                            step_B.set_pos(space_pos, True)
                        else:
                            step_B.set_pos(space_pos, False)
                        Bi >>= 1
                    poss.append(step_B.clone())
        return poss


class clue_1L1N(clue):
    def __init__(self, value: int):
        self.value = value
        self.circle = [(0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1)]

    def __str__(self):
        return str(self.value) + '(1L1N)'

    def permu(self, W_Space: int, B_Space: int, W_Flag: int, B_Flag: int):
        RT = []
        if self.value + 1 == 0:
            for i in range(W_Space + 1):
                if W_Flag + i - B_Flag < 0 or W_Flag + i - B_Flag > B_Space:
                    continue
                RT.append((full_permu(W_Space, i), full_permu(B_Space, W_Flag + i - B_Flag)))
        else:
            for i in range(W_Space + 1):
                if W_Flag + i < B_Flag + self.value + 1 or W_Flag + i > B_Flag + B_Space + self.value + 1:
                    continue
                RT.append((full_permu(W_Space, i), full_permu(B_Space, W_Flag + i - B_Flag - self.value - 1)))
            for i in range(W_Space + 1):
                if W_Flag + i < B_Flag - self.value - 1 or W_Flag + i > B_Flag + B_Space - self.value - 1:
                    continue
                RT.append((full_permu(W_Space, i), full_permu(B_Space, W_Flag + i - B_Flag + self.value + 1)))
        if self.value - 1 == 0:
            for i in range(W_Space + 1):
                if W_Flag + i - B_Flag < 0 or W_Flag + i - B_Flag > B_Space:
                    continue
                RT.append((full_permu(W_Space, i), full_permu(B_Space, W_Flag + i - B_Flag)))
        else:
            for i in range(W_Space + 1):
                if W_Flag + i < B_Flag + self.value - 1 or W_Flag + i > B_Flag + B_Space + self.value - 1:
                    continue
                RT.append((full_permu(W_Space, i), full_permu(B_Space, W_Flag + i - B_Flag - self.value + 1)))
            for i in range(W_Space + 1):
                if W_Flag + i < B_Flag - self.value + 1 or W_Flag + i > B_Flag + B_Space - self.value + 1:
                    continue
                RT.append((full_permu(W_Space, i), full_permu(B_Space, W_Flag + i - B_Flag + self.value - 1)))
        return RT

    def near(self, pos: tuple, board: board, model: str = 'nearby'):
        if model == 'nearby':
            nearby = []
            for xi, yi in self.circle:
                neighbor = board.get_pos((pos[0] + xi, pos[1] + yi))
                neighbor_dye = board.get_dye((pos[0] + xi, pos[1] + yi))
                nearby.append((neighbor, neighbor_dye))
            return nearby
        if model == 'sf':
            W_Space = []
            B_Space = []
            W_Flag = 0
            B_Flag = 0
            for xi, yi in self.circle:
                neighbor = board.get_pos((pos[0] + xi, pos[1] + yi))
                neighbor_dye = board.get_dye((pos[0] + xi, pos[1] + yi))
                if neighbor is None:
                    if neighbor_dye:
                        W_Space.append((pos[0] + xi, pos[1] + yi))
                    else:
                        B_Space.append((pos[0] + xi, pos[1] + yi))
                if neighbor is True:
                    if neighbor_dye:
                        W_Flag += 1
                    else:
                        B_Flag += 1
            return (W_Space, B_Space, W_Flag, B_Flag)

    def create_self(self, pos: tuple, board: board):
        nearby = self.near(pos, board, 'sf')
        self.value = abs(nearby[3] - nearby[2] + (randint(0, 1) * 2 - 1))

    def permution(self, pos: tuple, board: board):
        W_Space, B_Space, W_Flag, B_Flag = self.near(pos, board, 'sf')
        pem = self.permu(len(W_Space), len(B_Space), W_Flag, B_Flag)
        poss = []
        for Wpem, Bpem in pem:
            for Wi in Wpem:
                step_W = board.clone()
                for space_pos in W_Space:
                    if Wi & 1:
                        step_W.set_pos(space_pos, True)
                    else:
                        step_W.set_pos(space_pos, False)
                    Wi >>= 1
                for Bi in Bpem:
                    step_B = step_W.clone()
                    for space_pos in B_Space:
                        if Bi & 1:
                            step_B.set_pos(space_pos, True)
                        else:
                            step_B.set_pos(space_pos, False)
                        Bi >>= 1
                    poss.append(step_B.clone())
        return poss


class clue_1E_sp(clue):
    def __init__(self, value: int):
        self.value = value

    def __str__(self):
        return str(self.value) + '(1E\')'

    def permu(self, Space: list, pos: int, length: int):
        poss = []
        for i in range(length + 1):
            if (pos - i - 1 < -1) or (pos - i + length > len(Space)) or (
                    pos - i - 1 > -1 and (Space[pos - i - 1] is False or isinstance(Space[pos - i - 1], clue))) or (
                    pos - i + length < len(Space) and (
                    Space[pos - i + length] is False or isinstance(Space[pos - i + length], clue))):
                continue
            for j in range(pos - i, pos - i + length):
                if Space[j] is True:
                    break
            else:
                poss.append((pos - i, pos - i + length))
        return poss

    def near(self, pos: tuple, board: board, model: str = 'nearby'):
        if model == 'nearby':
            nearby = []
        if model == 'sf':
            h_Space = []
            v_Space = []
            for xi in range(board.Size_N):
                h_Space.append(board.get_pos((xi, pos[1])))
            for yi in range(board.Size_H):
                v_Space.append(board.get_pos((pos[0], yi)))
            return (h_Space, v_Space, pos)

    def create_self(self, pos: tuple, board: board):
        self.value = 0
        for i in range(pos[1] - 1, -1, -1):
            if board.get_pos((pos[0], i)) is True:
                break
            self.value += 1
        for i in range(pos[1] + 1, board.Size_H):
            if board.get_pos((pos[0], i)) is True:
                break
            self.value += 1
        for i in range(pos[0] - 1, -1, -1):
            if board.get_pos((i, pos[1])) is True:
                break
            self.value -= 1
        for i in range(pos[0] + 1, board.Size_N):
            if board.get_pos((i, pos[1])) is True:
                break
            self.value -= 1

    def permution(self, pos: tuple, board: board):
        h_Space, v_Space, pos = self.near(pos, board, 'sf')
        poss = []
        for h_num in range(1, board.Size_N + 1):
            h_pem = self.permu(h_Space, pos[0], h_num)
            v_pem = self.permu(v_Space, pos[1], h_num + self.value)
            if h_pem and v_pem:
                for Hi in h_pem:
                    step_H = board.clone()
                    if step_H.get_pos((Hi[0] - 1, pos[1])) is None:
                        step_H.set_pos((Hi[0] - 1, pos[1]), True)
                    if step_H.get_pos((Hi[1], pos[1])) is None:
                        step_H.set_pos((Hi[1], pos[1]), True)
                    for j in range(Hi[0], Hi[1]):
                        if step_H.get_pos((j, pos[1])) is None:
                            step_H.set_pos((j, pos[1]), False)
                    for Vi in v_pem:
                        step_V = step_H.clone()
                        if step_V.get_pos((pos[0], Vi[0] - 1)) is None:
                            step_V.set_pos((pos[0], Vi[0] - 1), True)
                        if step_V.get_pos((pos[0], Vi[1])) is None:
                            step_V.set_pos((pos[0], Vi[1]), True)
                        for j in range(Vi[0], Vi[1]):
                            if step_V.get_pos((pos[0], j)) is None:
                                step_V.set_pos((pos[0], j), False)
                        poss.append(step_V.clone())
        return poss


class clue_2X(clue):
    def __init__(self, value: list[int]):
        self.value = value
        self.circle = [(0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1)]

    def __str__(self):
        return str(self.value[0]) + '_' + str(self.value[1]) + '(2X)'

    def permu(self, W_Space: int, B_Space: int, W_Flag: int, B_Flag: int):
        Flag_num = (W_Flag << 1) + B_Flag
        RT = []
        if W_Space + W_Flag >= self.value[0] >= W_Flag and B_Space + B_Flag >= self.value[1] >= B_Flag:
            RT.append((full_permu(W_Space, self.value[0] - W_Flag), full_permu(B_Space, self.value[1] - B_Flag)))
        if W_Space + W_Flag >= self.value[1] >= W_Flag and B_Space + B_Flag >= self.value[0] >= B_Flag and self.value[
            0] != self.value[1]:
            RT.append((full_permu(W_Space, self.value[1] - W_Flag), full_permu(B_Space, self.value[0] - B_Flag)))
        return RT

    def near(self, pos: tuple, board: board, model: str = 'nearby'):
        if model == 'nearby':
            nearby = []
            for xi, yi in self.circle:
                neighbor = board.get_pos((pos[0] + xi, pos[1] + yi))
                neighbor_dye = board.get_dye((pos[0] + xi, pos[1] + yi))
                nearby.append((neighbor, neighbor_dye))
            return nearby
        if model == 'sf':
            W_Space = []
            B_Space = []
            W_Flag = 0
            B_Flag = 0
            for xi, yi in self.circle:
                neighbor = board.get_pos((pos[0] + xi, pos[1] + yi))
                neighbor_dye = board.get_dye((pos[0] + xi, pos[1] + yi))
                if neighbor is None:
                    if neighbor_dye:
                        W_Space.append((pos[0] + xi, pos[1] + yi))
                    else:
                        B_Space.append((pos[0] + xi, pos[1] + yi))
                if neighbor is True:
                    if neighbor_dye:
                        W_Flag += 1
                    else:
                        B_Flag += 1
            return (W_Space, B_Space, W_Flag, B_Flag)

    def create_self(self, pos: tuple, board: board):
        nearby = self.near(pos, board, 'sf')
        self.value = sorted([nearby[2], nearby[3]])

    def permution(self, pos: tuple, board: board):
        W_Space, B_Space, W_Flag, B_Flag = self.near(pos, board, 'sf')
        pem = self.permu(len(W_Space), len(B_Space), W_Flag, B_Flag)
        poss = []
        for Wpem, Bpem in pem:
            for Wi in Wpem:
                step_W = board.clone()
                for space_pos in W_Space:
                    if Wi & 1:
                        step_W.set_pos(space_pos, True)
                    else:
                        step_W.set_pos(space_pos, False)
                    Wi >>= 1
                for Bi in Bpem:
                    step_B = step_W.clone()
                    for space_pos in B_Space:
                        if Bi & 1:
                            step_B.set_pos(space_pos, True)
                        else:
                            step_B.set_pos(space_pos, False)
                        Bi >>= 1
                    poss.append(step_B.clone())
        return poss


class clue_2D(clue):
    def __init__(self, value: int):
        self.value = value
        self.circle = [(0, -2), (1, -2), (1, -1), (1, 0), (0, -1), (-1, 0), (-1, -1), (-1, -2)]

    def __str__(self):
        return str(self.value) + '(2D)'

    def permu(self, Space_num, Flag_num):
        if Space_num + Flag_num < self.value or Flag_num > self.value:
            return []
        return full_permu(Space_num, self.value - Flag_num)

    def near(self, pos: tuple, board: board, model: str = 'nearby'):
        if model == 'nearby':
            nearby = []
            for xi, yi in self.circle:
                neighbor = board.get_pos((pos[0] + xi, pos[1] + yi))
                nearby.append(neighbor)
            return nearby
        if model == 'sf':
            Space = []
            Flag_num = 0
            for xi, yi in self.circle:
                neighbor = board.get_pos((pos[0] + xi, pos[1] + yi))
                if neighbor is None:
                    Space.append((pos[0] + xi, pos[1] + yi))
                if neighbor is True:
                    Flag_num += 1
            return (Space, Flag_num)

    def create_self(self, pos: tuple, board: board):
        nearby = self.near(pos, board, 'sf')
        self.value = nearby[1]

    def permution(self, pos: tuple, board: board):
        nearby = self.near(pos, board, 'sf')
        Space_num = len(nearby[0])
        Flag_num = nearby[1]
        poss = []
        if Space_num + Flag_num < self.value or Flag_num > self.value:
            return False
        pem = self.permu(Space_num, Flag_num)
        for i in pem:
            poss.append(board.clone())
            for space_pos in nearby[0]:
                if i & 1:
                    poss[-1].set_pos(space_pos, True)
                else:
                    poss[-1].set_pos(space_pos, False)
                i >>= 1
        return poss


class clue_2M(clue):
    def __init__(self, value: int):
        self.value = value
        self.circle = [(0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1)]

    def __str__(self):
        return str(self.value) + '(2M)'

    def permu(self, Space_num, Flag_num):
        RT = []
        for i in range(0, len(self.circle) // 3 + 1):
            if Space_num + Flag_num >= self.value + i * 3 >= Flag_num:
                RT += full_permu(Space_num, self.value + i * 3 - Flag_num)
        return RT

    def near(self, pos: tuple, board: board, model: str = 'nearby'):
        if model == 'nearby':
            nearby = []
            for xi, yi in self.circle:
                neighbor = board.get_pos((pos[0] + xi, pos[1] + yi))
                nearby.append(neighbor)
            return nearby
        if model == 'sf':
            Space = []
            Flag_num = 0
            for xi, yi in self.circle:
                neighbor = board.get_pos((pos[0] + xi, pos[1] + yi))
                if neighbor is None:
                    Space.append((pos[0] + xi, pos[1] + yi))
                if neighbor is True:
                    Flag_num += 1
            return (Space, Flag_num)

    def create_self(self, pos: tuple, board: board):
        nearby = self.near(pos, board, 'sf')
        self.value = nearby[1] % 3

    def permution(self, pos: tuple, board: board):
        nearby = self.near(pos, board, 'sf')
        Space_num = len(nearby[0])
        Flag_num = nearby[1]
        poss = []
        pem = self.permu(Space_num, Flag_num)
        for i in pem:
            poss.append(board.clone())
            for space_pos in nearby[0]:
                if i & 1:
                    poss[-1].set_pos(space_pos, True)
                else:
                    poss[-1].set_pos(space_pos, False)
                i >>= 1
        return poss


class clue_2P(clue):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        if self.value == 1:
            return '1(2P)'
        ori_I = 1
        ori_F = self.value
        i = 2
        while ori_F > i:
            while ori_F % (i * i) == 0:
                ori_F //= (i * i)
                ori_I *= i
            i += 1
        if ori_I == 1:
            return '√' + str(ori_F) + '(2P)'
        elif ori_F == 1:
            return str(ori_I) + '(2P)'
        else:
            return str(ori_I) + '√' + str(ori_F) + '(2P)'

    def permu(self, Flag: tuple[int]):
        if Flag[0] * Flag[1] < self.value:
            return []
        elif Flag[0] * Flag[1] == self.value:
            return [(Flag[0], Flag[1])]
        else:
            RT = []
            for i in range(1, int(self.value ** 0.5) + 1):
                if self.value % i == 0:
                    if i < Flag[0] and i * min(Flag[0], self.value // i) == self.value:
                        RT.append((i, min(Flag[0], self.value // i)))
                    elif i == Flag[0]:
                        RT.append((Flag[0], self.value // i))
                        break
            return RT

    def near(self, pos: tuple, board: board, model: str = 'nearby'):
        if model == 'nearby':
            pass
        if model == 'sf':
            x, y = pos

            def square_test(N: int):
                i = 2
                while i < N:
                    while N % (i * i) == 0:
                        N //= i * i
                    i += 1
                return N <= 1

            neighbor = []
            Space = [[]]
            dis = 1
            while len(neighbor) < 2:
                Space.append([])
                for i in range(int(dis ** 0.5) + 1):
                    if square_test(dis - i * i):
                        dx = i
                        dy = int((dis - i * i) ** 0.5)
                        if dx == 0:
                            if board.get_pos((x, y + dy)) is None:
                                Space[-1].append((x, y + dy))
                            elif board.get_pos((x, y + dy)) is True:
                                neighbor.append(dis)
                            if board.get_pos((x, y - dy)) is None:
                                Space[-1].append((x, y - dy))
                            elif board.get_pos((x, y - dy)) is True:
                                neighbor.append(dis)
                        elif dy == 0:
                            if board.get_pos((x + dx, y)) is None:
                                Space[-1].append((x + dx, y))
                            elif board.get_pos((x + dx, y)) is True:
                                neighbor.append(dis)
                            if board.get_pos((x - dx, y)) is None:
                                Space[-1].append((x - dx, y))
                            elif board.get_pos((x - dx, y)) is True:
                                neighbor.append(dis)
                        else:
                            if board.get_pos((x + dx, y + dy)) is None:
                                Space[-1].append((x + dx, y + dy))
                            elif board.get_pos((x + dx, y + dy)) is True:
                                neighbor.append(dis)
                            if board.get_pos((x - dx, y + dy)) is None:
                                Space[-1].append((x - dx, y + dy))
                            elif board.get_pos((x - dx, y + dy)) is True:
                                neighbor.append(dis)
                            if board.get_pos((x + dx, y - dy)) is None:
                                Space[-1].append((x + dx, y - dy))
                            elif board.get_pos((x + dx, y - dy)) is True:
                                neighbor.append(dis)
                            if board.get_pos((x - dx, y - dy)) is None:
                                Space[-1].append((x - dx, y - dy))
                            elif board.get_pos((x - dx, y - dy)) is True:
                                neighbor.append(dis)
                if self.value == dis:
                    break
                dis += 1
            while len(neighbor) < 2:
                neighbor.append(float('inf'))
            return (Space, (neighbor[0], neighbor[1]))

    def create_self(self, pos: tuple, board: board):
        neighbor_st, neighbor_nd = self.near(pos, board, 'sf')[1]
        self.value = neighbor_st * neighbor_nd

    def permution(self, pos: tuple, board: board):
        nearby = self.near(pos, board, 'sf')
        Space_ori = nearby[0]
        pem = self.permu(nearby[1])
        poss = []
        for st, nd in pem:
            Space = []
            for row in Space_ori:
                Space.append(row[:])
            if st != nearby[1][0]:
                for _ in range(len(Space[st])):
                    Space_pos = Space[st].pop()
                    step_st = board.clone()
                    for i in range(nd):
                        for Space_pos_F in Space_ori[i]:
                            step_st.set_pos(Space_pos_F, False)
                    step_st.set_pos(Space_pos, True)
                    if nd != nearby[1][0] and nd != nearby[1][1]:
                        for Space_x, Space_y in Space[nd]:
                            poss.append(step_st.clone())
                            poss[-1].set_pos(Space_pos, True)
                    else:
                        poss.append(step_st.clone())
            else:
                step_st = board.clone()
                for i in range(nd):
                    for Space_pos_F in Space_ori[i]:
                        step_st.set_pos(Space_pos_F, False)
                if nd != nearby[1][0] and nd != nearby[1][1]:
                    for Space_pos in Space[nd]:
                        poss.append(step_st.clone())
                        poss[-1].set_pos(Space_pos, True)
                else:
                    poss.append(step_st.clone())
        return poss


class clue_2X_sp(clue):
    def __init__(self, value: list[int]):
        self.value = value
        self.circle = [(0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1)]

    def __str__(self):
        return str(self.value) + '(2X\')'

    def permu(self, W_Space: int, B_Space: int, W_Flag: int, B_Flag: int):
        Flag_num = (W_Flag << 1) + B_Flag
        RT = [[], []]
        if W_Space + W_Flag >= self.value >= W_Flag:
            RT[0] = full_permu(W_Space, self.value - W_Flag)
        if B_Space + B_Flag >= self.value >= B_Flag:
            RT[1] = full_permu(B_Space, self.value - B_Flag)
        return RT

    def near(self, pos: tuple, board: board, model: str = 'nearby'):
        if model == 'nearby':
            nearby = []
            for xi, yi in self.circle:
                neighbor = board.get_pos((pos[0] + xi, pos[1] + yi))
                neighbor_dye = board.get_dye((pos[0] + xi, pos[1] + yi))
                nearby.append((neighbor, neighbor_dye))
            return nearby
        if model == 'sf':
            W_Space = []
            B_Space = []
            W_Flag = 0
            B_Flag = 0
            for xi, yi in self.circle:
                neighbor = board.get_pos((pos[0] + xi, pos[1] + yi))
                neighbor_dye = board.get_dye((pos[0] + xi, pos[1] + yi))
                if neighbor is None:
                    if neighbor_dye:
                        W_Space.append((pos[0] + xi, pos[1] + yi))
                    else:
                        B_Space.append((pos[0] + xi, pos[1] + yi))
                if neighbor is True:
                    if neighbor_dye:
                        W_Flag += 1
                    else:
                        B_Flag += 1
            return (W_Space, B_Space, W_Flag, B_Flag)

    def create_self(self, pos: tuple, board: board):
        nearby = self.near(pos, board, 'sf')
        self.value = choice([nearby[2], nearby[3]])

    def permution(self, pos: tuple, board: board):
        W_Space, B_Space, W_Flag, B_Flag = self.near(pos, board, 'sf')
        pem = self.permu(len(W_Space), len(B_Space), W_Flag, B_Flag)
        poss = []
        Wpem = pem[0]
        Bpem = pem[1]
        for Wi in Wpem:
            step_W = board.clone()
            for space_pos in W_Space:
                if Wi & 1:
                    step_W.set_pos(space_pos, True)
                else:
                    step_W.set_pos(space_pos, False)
                Wi >>= 1
            poss.append(step_W.clone())
        for Bi in Bpem:
            step_B = board.clone()
            for space_pos in B_Space:
                if Bi & 1:
                    step_B.set_pos(space_pos, True)
                else:
                    step_B.set_pos(space_pos, False)
                Bi >>= 1
            poss.append(step_B.clone())
        return poss


class clue_2I(clue):
    def __init__(self, value: int):
        self.value = value
        self.circle_ori = [(0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1)]

    def __str__(self):
        return str(self.value) + '(2I)'

    def permu(self, Space_num, Flag_num):
        if Space_num + Flag_num < self.value or Flag_num > self.value:
            return []
        return full_permu(Space_num, self.value - Flag_num)

    def near(self, pos: tuple, board: board, circle, model: str = 'nearby'):
        if model == 'nearby':
            nearby = []
            for xi, yi in circle:
                neighbor = board.get_pos((pos[0] + xi, pos[1] + yi))
                nearby.append(neighbor)
            return nearby
        if model == 'sf':
            Space = []
            Flag_num = 0
            for xi, yi in circle:
                neighbor = board.get_pos((pos[0] + xi, pos[1] + yi))
                if neighbor is None:
                    Space.append((pos[0] + xi, pos[1] + yi))
                if neighbor is True:
                    Flag_num += 1
            return (Space, Flag_num)

    def create_self(self, pos: tuple, board: board):
        circle = []
        for i in board.subord_board_I:
            circle.append(self.circle_ori[i])
        nearby = self.near(pos, board, circle, 'sf')
        self.value = nearby[1]

    def permution(self, pos: tuple, board: board):
        poss = []
        circle_test = [_ for _ in range(len(self.circle_ori))]
        for i in board.subord_board_I[::-1]:
            circle_test.pop(i)
        for i in circle_test:
            circle = self.circle_ori[:]
            subord_board_I = [_ for _ in range(len(self.circle_ori))]
            circle.pop(i)
            subord_board_I.pop(i)
            nearby = self.near(pos, board, circle, 'sf')
            Space_num = len(nearby[0])
            Flag_num = nearby[1]
            pem = self.permu(Space_num, Flag_num)
            for i in pem:
                poss.append(board.clone())
                poss[-1].subord_board_I = subord_board_I
                for space_pos in nearby[0]:
                    if i & 1:
                        poss[-1].set_pos(space_pos, True)
                    else:
                        poss[-1].set_pos(space_pos, False)
                    i >>= 1
        return poss


class clue_2I1K(clue):
    def __init__(self, value: int):
        self.value = value
        self.circle_ori = [(-1, -2), (1, -2), (2, -1), (2, 1), (1, 2), (-1, 2), (-2, 1), (-2, -1)]

    def __str__(self):
        return str(self.value) + '(2I1K)'

    def permu(self, Space_num, Flag_num):
        if Space_num + Flag_num < self.value or Flag_num > self.value:
            return []
        return full_permu(Space_num, self.value - Flag_num)

    def near(self, pos: tuple, board: board, circle, model: str = 'nearby'):
        if model == 'nearby':
            nearby = []
            for xi, yi in circle:
                neighbor = board.get_pos((pos[0] + xi, pos[1] + yi))
                nearby.append(neighbor)
            return nearby
        if model == 'sf':
            Space = []
            Flag_num = 0
            for xi, yi in circle:
                neighbor = board.get_pos((pos[0] + xi, pos[1] + yi))
                if neighbor is None:
                    Space.append((pos[0] + xi, pos[1] + yi))
                if neighbor is True:
                    Flag_num += 1
            return (Space, Flag_num)

    def create_self(self, pos: tuple, board: board):
        circle = []
        for i in board.subord_board_I:
            circle.append(self.circle_ori[i])
        nearby = self.near(pos, board, circle, 'sf')
        self.value = nearby[1]

    def permution(self, pos: tuple, board: board):
        poss = []
        circle_test = [_ for _ in range(len(self.circle_ori))]
        for i in board.subord_board_I[::-1]:
            circle_test.pop(i)
        for i in circle_test:
            circle = self.circle_ori[:]
            subord_board_I = [_ for _ in range(len(self.circle_ori))]
            circle.pop(i)
            subord_board_I.pop(i)
            nearby = self.near(pos, board, circle, 'sf')
            Space_num = len(nearby[0])
            Flag_num = nearby[1]
            pem = self.permu(Space_num, Flag_num)
            for i in pem:
                poss.append(board.clone())
                poss[-1].subord_board_I = subord_board_I
                for space_pos in nearby[0]:
                    if i & 1:
                        poss[-1].set_pos(space_pos, True)
                    else:
                        poss[-1].set_pos(space_pos, False)
                    i >>= 1
        return poss


class clue_2X1X(clue):
    def __init__(self, value: list[int]):
        self.value = value
        self.circle = [(0, -1), (0, -2), (1, 0), (2, 0), (0, 1), (0, 2), (-1, 0), (-2, 0)]

    def __str__(self):
        return str(self.value[0]) + '_' + str(self.value[1]) + '(2X1X)'

    def permu(self, W_Space: int, B_Space: int, W_Flag: int, B_Flag: int):
        Flag_num = (W_Flag << 1) + B_Flag
        RT = []
        if W_Space + W_Flag >= self.value[0] >= W_Flag and B_Space + B_Flag >= self.value[1] >= B_Flag:
            RT.append((full_permu(W_Space, self.value[0] - W_Flag), full_permu(B_Space, self.value[1] - B_Flag)))
        if W_Space + W_Flag >= self.value[1] >= W_Flag and B_Space + B_Flag >= self.value[0] >= B_Flag and self.value[
            0] != self.value[1]:
            RT.append((full_permu(W_Space, self.value[1] - W_Flag), full_permu(B_Space, self.value[0] - B_Flag)))
        return RT

    def near(self, pos: tuple, board: board, model: str = 'nearby'):
        if model == 'nearby':
            nearby = []
            for xi, yi in self.circle:
                neighbor = board.get_pos((pos[0] + xi, pos[1] + yi))
                neighbor_dye = board.get_dye((pos[0] + xi, pos[1] + yi))
                nearby.append((neighbor, neighbor_dye))
            return nearby
        if model == 'sf':
            W_Space = []
            B_Space = []
            W_Flag = 0
            B_Flag = 0
            for xi, yi in self.circle:
                neighbor = board.get_pos((pos[0] + xi, pos[1] + yi))
                neighbor_dye = board.get_dye((pos[0] + xi, pos[1] + yi))
                if neighbor is None:
                    if neighbor_dye:
                        W_Space.append((pos[0] + xi, pos[1] + yi))
                    else:
                        B_Space.append((pos[0] + xi, pos[1] + yi))
                if neighbor is True:
                    if neighbor_dye:
                        W_Flag += 1
                    else:
                        B_Flag += 1
            return (W_Space, B_Space, W_Flag, B_Flag)

    def create_self(self, pos: tuple, board: board):
        nearby = self.near(pos, board, 'sf')
        self.value = sorted([nearby[2], nearby[3]])

    def permution(self, pos: tuple, board: board):
        W_Space, B_Space, W_Flag, B_Flag = self.near(pos, board, 'sf')
        pem = self.permu(len(W_Space), len(B_Space), W_Flag, B_Flag)
        poss = []
        for Wpem, Bpem in pem:
            for Wi in Wpem:
                step_W = board.clone()
                for space_pos in W_Space:
                    if Wi & 1:
                        step_W.set_pos(space_pos, True)
                    else:
                        step_W.set_pos(space_pos, False)
                    Wi >>= 1
                for Bi in Bpem:
                    step_B = step_W.clone()
                    for space_pos in B_Space:
                        if Bi & 1:
                            step_B.set_pos(space_pos, True)
                        else:
                            step_B.set_pos(space_pos, False)
                        Bi >>= 1
                    poss.append(step_B.clone())
        return poss


class clue_2M1M(clue):
    def __init__(self, value: int):
        self.value = value
        self.circle = [(0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1)]

    def __str__(self):
        return str(self.value) + '(2M1M)'

    def permu(self, W_Space: int, B_Space: int, W_Flag: int, B_Flag: int):
        Flag_num = (W_Flag << 1) + B_Flag
        RT = []
        for i in range(0, len(self.circle) * 2 // 3 + 1):
            for j in range(W_Space + 1):
                if (self.value + i * 3) - Flag_num - (j << 1) < 0 or (self.value + i * 3) - Flag_num - (
                        j << 1) > B_Space:
                    continue
                RT.append((full_permu(W_Space, j), full_permu(B_Space, (self.value + i * 3) - Flag_num - (j << 1))))
        return RT

    def near(self, pos: tuple, board: board, model: str = 'nearby'):
        if model == 'nearby':
            nearby = []
            for xi, yi in self.circle:
                neighbor = board.get_pos((pos[0] + xi, pos[1] + yi))
                neighbor_dye = board.get_dye((pos[0] + xi, pos[1] + yi))
                nearby.append((neighbor, neighbor_dye))
            return nearby
        if model == 'sf':
            W_Space = []
            B_Space = []
            W_Flag = 0
            B_Flag = 0
            for xi, yi in self.circle:
                neighbor = board.get_pos((pos[0] + xi, pos[1] + yi))
                neighbor_dye = board.get_dye((pos[0] + xi, pos[1] + yi))
                if neighbor is None:
                    if neighbor_dye:
                        W_Space.append((pos[0] + xi, pos[1] + yi))
                    else:
                        B_Space.append((pos[0] + xi, pos[1] + yi))
                if neighbor is True:
                    if neighbor_dye:
                        W_Flag += 1
                    else:
                        B_Flag += 1
            return (W_Space, B_Space, W_Flag, B_Flag)

    def create_self(self, pos: tuple, board: board):
        nearby = self.near(pos, board, 'sf')
        self.value = ((nearby[2] * 2) + nearby[3]) % 3

    def permution(self, pos: tuple, board: board):
        W_Space, B_Space, W_Flag, B_Flag = self.near(pos, board, 'sf')
        pem = self.permu(len(W_Space), len(B_Space), W_Flag, B_Flag)
        poss = []
        for Wpem, Bpem in pem:
            for Wi in Wpem:
                step_W = board.clone()
                for space_pos in W_Space:
                    if Wi & 1:
                        step_W.set_pos(space_pos, True)
                    else:
                        step_W.set_pos(space_pos, False)
                    Wi >>= 1
                for Bi in Bpem:
                    step_B = step_W.clone()
                    for space_pos in B_Space:
                        if Bi & 1:
                            step_B.set_pos(space_pos, True)
                        else:
                            step_B.set_pos(space_pos, False)
                        Bi >>= 1
                    poss.append(step_B.clone())
        return poss


class clue_J_3S(clue):
    def __init__(self, value: list[int]):
        self.value = value
        self.circle_T = [(-1, 0), (-1, -1), (0, -1), (1, -1), (1, 0)]
        self.circle_B = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0)]

    def __str__(self):
        return str(self.value[0]) + '_' + str(self.value[1]) + '(J_3S)'

    def permu(self, T_Space: int, B_Space: int, T_Flag: int, B_Flag: int):
        RT = []
        if T_Space + T_Flag >= self.value[0] >= T_Flag and B_Space + B_Flag >= self.value[1] >= B_Flag:
            RT.append((full_permu(T_Space, self.value[0] - T_Flag), full_permu(B_Space, self.value[1] - B_Flag)))
        if T_Space + T_Flag >= self.value[1] >= T_Flag and B_Space + B_Flag >= self.value[0] >= B_Flag and self.value[
            0] != self.value[1]:
            RT.append((full_permu(T_Space, self.value[1] - T_Flag), full_permu(B_Space, self.value[0] - B_Flag)))
        return RT

    def near(self, pos: tuple, board: board, model: str = 'nearby'):
        if model == 'nearby':
            nearby = []
            return nearby
        if model == 'sf':
            T_Space = []
            B_Space = []
            T_Flag = 0
            B_Flag = 0
            for i in range(5):
                xi, yi = self.circle_T[i]
                xj, yj = self.circle_B[i]
                neighbor_T = board.get_pos((pos[0] + xi, pos[1] + yi))
                neighbor_B = board.get_pos((pos[0] + xj, pos[1] + yj))
                if neighbor_T is None:
                    T_Space.append((pos[0] + xi, pos[1] + yi))
                if neighbor_B is None:
                    B_Space.append((pos[0] + xj, pos[1] + yj))
                if neighbor_T is True:
                    T_Flag += 1
                if neighbor_B is True:
                    B_Flag += 1
            return (T_Space, B_Space, T_Flag, B_Flag)

    def create_self(self, pos: tuple, board: board):
        nearby = self.near(pos, board, 'sf')
        self.value = sorted([nearby[2], nearby[3]])

    def permution(self, pos: tuple, board: board):
        W_Space, B_Space, W_Flag, B_Flag = self.near(pos, board, 'sf')
        pem = self.permu(len(W_Space), len(B_Space), W_Flag, B_Flag)
        poss = []
        for Wpem, Bpem in pem:
            for Wi in Wpem:
                step_W = board.clone()
                for space_pos in W_Space:
                    if Wi & 1:
                        step_W.set_pos(space_pos, True)
                    else:
                        step_W.set_pos(space_pos, False)
                    Wi >>= 1
                for Bi in Bpem:
                    step_B = step_W.clone()
                    for space_pos in B_Space:
                        if Bi & 1:
                            step_B.set_pos(space_pos, True)
                        else:
                            step_B.set_pos(space_pos, False)
                        Bi >>= 1
                    poss.append(step_B.clone())
        return poss


class clue_J_3N(clue):
    def __init__(self, value: int):
        self.value = value
        self.circle_T = [(-1, -1), (0, -1), (1, -1), (1, 0)]
        self.circle_B = [(1, 1), (0, 1), (-1, 1), (-1, 0)]

    def __str__(self):
        return str(self.value) + '(J_3N)'

    def permu(self, T_Flag: list[int], B_Flag: list[int]):
        RT = []
        Flag = 0
        Space = []
        T_Space = [0 for _ in range(4)]
        T_pre = 0
        B_Space = [0 for _ in range(4)]
        B_pre = 0
        for i in range(4):
            if isinstance(T_Flag[i], bool) and isinstance(B_Flag[i], bool) and T_Flag[i] != B_Flag[i]:
                Flag += 1
            elif not (isinstance(T_Flag[i], bool) and isinstance(B_Flag[i], bool)):
                Space.append(i)
                if not isinstance(T_Flag[i], bool):
                    T_Space[i] = T_pre
                    T_pre += 1
                if not (isinstance(B_Flag[i], bool)):
                    B_Space[i] = B_pre
                    B_pre += 1
        if len(Space) + Flag >= self.value >= Flag:
            real_poss = full_permu(len(Space), self.value - Flag)
            for poss in real_poss:
                T_poss = [0]
                B_poss = [0]
                for i in range(len(Space)):
                    if (poss >> i) & 1:
                        if T_Flag[Space[i]] is None and B_Flag[Space[i]] is None:
                            for _ in range(len(T_poss)):
                                Ti = T_poss.pop(0)
                                T_poss.append(Ti + (1 << (T_Space[Space[i]])))
                                T_poss.append(Ti)
                            for _ in range(len(B_poss)):
                                Bi = B_poss.pop(0)
                                B_poss.append(Bi)
                                B_poss.append(Bi + (1 << (B_Space[Space[i]])))
                        elif T_Flag[Space[i]] is None and B_Flag[Space[i]] is False:
                            for _ in range(len(T_poss)):
                                Ti = T_poss.pop(0)
                                T_poss.append(Ti + (1 << (T_Space[Space[i]])))
                        elif T_Flag[Space[i]] is False and B_Flag[Space[i]] is None:
                            for _ in range(len(B_poss)):
                                Bi = B_poss.pop(0)
                                B_poss.append(Bi + (1 << (B_Space[Space[i]])))
                    else:
                        if T_Flag[Space[i]] is None and B_Flag[Space[i]] is None:
                            for _ in range(len(T_poss)):
                                Ti = T_poss.pop(0)
                                T_poss.append(Ti + (1 << (T_Space[Space[i]])))
                                T_poss.append(Ti)
                            for _ in range(len(B_poss)):
                                Bi = B_poss.pop(0)
                                B_poss.append(Bi + (1 << (B_Space[Space[i]])))
                                B_poss.append(Bi)
                        elif T_Flag[Space[i]] is None and B_Flag[Space[i]] is True:
                            for _ in range(len(T_poss)):
                                Ti = T_poss.pop(0)
                                T_poss.append(Ti + (1 << (T_Space[Space[i]])))
                        elif T_Flag[Space[i]] is True and B_Flag[Space[i]] is None:
                            for _ in range(len(B_poss)):
                                Bi = B_poss.pop(0)
                                B_poss.append(Bi + (1 << (B_Space[Space[i]])))
                for i in range(len(T_poss)):
                    RT.append((T_poss[i], B_poss[i]))
        return RT

    def near(self, pos: tuple, board: board, model: str = 'nearby'):
        if model == 'nearby':
            nearby = []
            return nearby
        if model == 'sf':
            T_Space = []
            B_Space = []
            T_Flag = [False for _ in range(4)]
            B_Flag = [False for _ in range(4)]
            for i in range(4):
                xi, yi = self.circle_T[i]
                xj, yj = self.circle_B[i]
                neighbor_T = board.get_pos((pos[0] + xi, pos[1] + yi))
                neighbor_B = board.get_pos((pos[0] + xj, pos[1] + yj))
                if neighbor_T is None:
                    T_Space.append((pos[0] + xi, pos[1] + yi))
                    T_Flag[i] = None
                if neighbor_B is None:
                    B_Space.append((pos[0] + xj, pos[1] + yj))
                    B_Flag[i] = None
                if neighbor_T is True:
                    T_Flag[i] = True
                if neighbor_B is True:
                    B_Flag[i] = True
            return (T_Space, B_Space, T_Flag, B_Flag)

    def create_self(self, pos: tuple, board: board):
        nearby = self.near(pos, board, 'sf')
        self.value = 0
        for i in range(4):
            self.value += ((nearby[2][i] is True and nearby[3][i] is not True) or (
                        nearby[2][i] is not True and nearby[3][i] is True))

    def permution(self, pos: tuple, board: board):
        W_Space, B_Space, W_Flag, B_Flag = self.near(pos, board, 'sf')
        pem = self.permu(W_Flag, B_Flag)
        poss = []
        for Wi, Bi in pem:
            step_W = board.clone()
            for space_pos in W_Space:
                if Wi & 1:
                    step_W.set_pos(space_pos, True)
                else:
                    step_W.set_pos(space_pos, False)
                Wi >>= 1
            for space_pos in B_Space:
                if Bi & 1:
                    step_W.set_pos(space_pos, True)
                else:
                    step_W.set_pos(space_pos, False)
                Bi >>= 1
            poss.append(step_W.clone())
        return poss


class clue_J_3P(clue):
    def __init__(self, value: int):
        self.value = value
        self.circle = [(-1, -1), (0, -1), (1, -1), (-1, 0), (0, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]

    def __str__(self):
        return str(self.value) + '(J_3P)'

    def permu(self, Space_num, Flag_num):
        if Space_num + Flag_num < self.value or Flag_num > self.value:
            return []
        return full_permu(Space_num, self.value - Flag_num)

    def near(self, pos: tuple, board: board, model: str = 'nearby'):
        if model == 'nearby':
            P_pos = (board.Size_N - pos[0] - 1, board.Size_H - pos[1] - 1)
            nearby = []
            for xi, yi in self.circle:
                neighbor = board.get_pos((P_pos[0] + xi, P_pos[1] + yi))
                nearby.append(neighbor)
            return nearby
        if model == 'sf':
            P_pos = (board.Size_N - pos[0] - 1, board.Size_H - pos[1] - 1)
            Space = []
            Flag_num = 0
            for xi, yi in self.circle:
                neighbor = board.get_pos((P_pos[0] + xi, P_pos[1] + yi))
                if neighbor is None:
                    Space.append((P_pos[0] + xi, P_pos[1] + yi))
                if neighbor is True:
                    Flag_num += 1
            return (Space, Flag_num)

    def create_self(self, pos: tuple, board: board):
        nearby = self.near(pos, board, 'sf')
        self.value = nearby[1]

    def permution(self, pos: tuple, board: board):
        nearby = self.near(pos, board, 'sf')
        Space_num = len(nearby[0])
        Flag_num = nearby[1]
        poss = []
        if Space_num + Flag_num < self.value or Flag_num > self.value:
            return False
        pem = self.permu(Space_num, Flag_num)
        for i in pem:
            poss.append(board.clone())
            for space_pos in nearby[0]:
                if i & 1:
                    poss[-1].set_pos(space_pos, True)
                else:
                    poss[-1].set_pos(space_pos, False)
                i >>= 1
        return poss


class clue_2L(clue):
    def __init__(self, value: int):
        self.value = value
        self.circle = [(0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1)]

    def __str__(self):
        return str(self.value) + '(2L)'

    def permu(self, Space_num, Flag_num, clue_bool):
        if clue_bool:
            if Space_num + Flag_num < self.value or Flag_num > self.value:
                return []
            return full_permu(Space_num, self.value - Flag_num)
        else:
            RT = []
            if Space_num + Flag_num >= self.value + 1 >= Flag_num:
                RT += full_permu(Space_num, self.value - Flag_num + 1)
            if Space_num + Flag_num >= self.value - 1 >= Flag_num:
                RT += full_permu(Space_num, self.value - Flag_num - 1)
            return RT

    def near(self, pos: tuple, board: board, model: str = 'nearby'):
        if model == 'nearby':
            nearby = []
            for xi, yi in self.circle:
                neighbor = board.get_pos((pos[0] + xi, pos[1] + yi))
                nearby.append(neighbor)
            return nearby
        if model == 'sf':
            Space = []
            Flag_num = 0
            for xi, yi in self.circle:
                neighbor = board.get_pos((pos[0] + xi, pos[1] + yi))
                if neighbor is None:
                    Space.append((pos[0] + xi, pos[1] + yi))
                if neighbor is True:
                    Flag_num += 1
            return (Space, Flag_num)

    def create_self(self, pos: tuple, board: board):
        nearby = self.near(pos, board, 'sf')
        clue_bool = not (board.get_subord_pos(pos))
        if clue_bool:
            self.value = nearby[1]
        else:
            self.value = abs(nearby[1] + (randint(0, 1) * 2 - 1))

    def permution(self, pos: tuple, board: board):
        nearby = self.near(pos, board, 'sf')
        Space_num = len(nearby[0])
        Flag_num = nearby[1]
        poss = []
        if board.get_subord_pos(pos) is None:
            pem_T = self.permu(Space_num, Flag_num, True)
            board_S_T = board.clone()
            board_S_T.set_subord_pos(pos, False)
            for i in range(board.Size_N):
                row_num = 0
                col_num = 0
                if board_S_T.get_subord_pos((pos[0], i)) is False:
                    row_num += 1
                if board_S_T.get_subord_pos((i, pos[1])) is False:
                    col_num += 1
            if row_num < board.Size_N and col_num < board.Size_N:
                for i in pem_T:
                    poss.append(board_S_T.clone())
                    for space_pos in nearby[0]:
                        if i & 1:
                            poss[-1].set_pos(space_pos, True)
                            poss[-1].set_subord_pos(space_pos, False)
                        else:
                            poss[-1].set_pos(space_pos, False)
                        i >>= 1
            pem_F = self.permu(Space_num, Flag_num, False)
            board_S_F = board.clone()
            for i in range(board.Size_N):
                if board_S_F.get_subord_pos((pos[0], i)) is True or board_S_F.get_subord_pos((i, pos[1])) is True:
                    break
                board_S_F.set_subord_pos((pos[0], i), False)
                board_S_F.set_subord_pos((i, pos[1]), False)
            else:
                board_S_F.set_subord_pos(pos, True)
                for i in pem_F:
                    poss.append(board_S_F.clone())
                    for space_pos in nearby[0]:
                        if i & 1:
                            poss[-1].set_pos(space_pos, True)
                            poss[-1].set_subord_pos(space_pos, False)
                        else:
                            poss[-1].set_pos(space_pos, False)
                        i >>= 1
        else:
            pem = self.permu(Space_num, Flag_num, not (board.get_subord_pos(pos)))
            for i in pem:
                poss.append(board.clone())
                for space_pos in nearby[0]:
                    if i & 1:
                        poss[-1].set_pos(space_pos, True)
                        poss[-1].set_subord_pos(space_pos, False)
                    else:
                        poss[-1].set_pos(space_pos, False)
                    i >>= 1
        new_poss = []
        for _ in range(len(poss)):
            B = poss.pop()
            for i in range(board.Size_N):
                row_Fnum = 0
                col_Fnum = 0
                row_Space = ()
                col_Space = ()
                for j in range(board.Size_N):
                    if B.get_subord_pos((i, j)) is False:
                        row_Fnum += 1
                    elif B.get_subord_pos((i, j)) is None:
                        row_Space = (i, j)
                    if B.get_subord_pos((j, i)) is False:
                        col_Fnum += 1
                    elif B.get_subord_pos((j, i)) is None:
                        col_Space = (j, i)
                if row_Fnum == board.Size_N or col_Fnum == board.Size_N:
                    break
                if row_Fnum == board.Size_N - 1 and row_Space:
                    for j in range(board.Size_N):
                        B.set_subord_pos((j, row_Space[1]), False)
                    B.set_subord_pos(row_Space, True)
                    if B.get_pos(row_Space) is None:
                        B.set_pos(row_Space, False)
                if col_Fnum == board.Size_N - 1 and col_Space:
                    for j in range(board.Size_N):
                        B.set_subord_pos((col_Space[0], j), False)
                    B.set_subord_pos(col_Space, True)
                    if B.get_pos(col_Space) is None:
                        B.set_pos(col_Space, False)
            else:
                '''
                print('\n'*20)
                for row in B.subord_board:
                    print(row)
                '''
                new_poss.append(B)
        return new_poss


class clue_2Q(clue):
    def __init__(self, value: int):
        self.value = value
        self.circle = [(0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1)]

    def __str__(self):
        return str(self.value) + '(2Q)'

    def permu(self, Space_num, Flag_num):
        if Space_num + Flag_num < self.value or Flag_num > self.value:
            return []
        return full_permu(Space_num, self.value - Flag_num)

    def near(self, pos: tuple, board: board, model: str = 'nearby'):
        if model == 'nearby':
            nearby = []
            for xi, yi in self.circle:
                neighbor = board.get_pos((pos[0] + xi, pos[1] + yi))
                nearby.append(neighbor)
            return nearby
        if model == 'sf':
            Space = []
            Flag_num = 0
            for xi, yi in self.circle:
                V_Space = []
                for Ei in range(1, board.Size_N):
                    neighbor = board.get_pos((pos[0] + Ei * xi, pos[1] + Ei * yi))
                    if neighbor == 'off board':
                        if V_Space:
                            Space.append(V_Space[:])
                        break
                    elif neighbor is None:
                        V_Space.append((pos[0] + Ei * xi, pos[1] + Ei * yi))
                    elif neighbor is True:
                        Flag_num += 1
                        break
                else:
                    Space.append(V_Space[:])
            return (Space, Flag_num)

    def create_self(self, pos: tuple, board: board):
        nearby = self.near(pos, board, 'sf')
        self.value = nearby[1]

    def permution(self, pos: tuple, board: board):
        nearby = self.near(pos, board, 'sf')
        Space_num = len(nearby[0])
        Flag_num = nearby[1]
        poss = []
        if Space_num + Flag_num < self.value or Flag_num > self.value:
            return False
        pem = self.permu(Space_num, Flag_num)
        for i in pem:
            poss_list = [board.clone()]
            for Space in nearby[0]:
                if i & 1:
                    for _ in range(len(poss_list)):
                        poss_poss = poss_list.pop(0)
                        for space_pos in Space:
                            poss_list.append(poss_poss.clone())
                            poss_list[-1].set_pos(space_pos, True)
                else:
                    for _ in range(len(poss_list)):
                        poss_poss = poss_list.pop(0)
                        poss_list.append(poss_poss.clone())
                        for space_pos in Space:
                            poss_list[-1].set_pos(space_pos, False)
                i >>= 1
            poss += poss_list
        return poss


class clue_2Q1K(clue):
    def __init__(self, value: int):
        self.value = value
        self.circle = [(-1, -2), (1, -2), (2, -1), (2, 1), (1, 2), (-1, 2), (-2, 1), (-2, -1)]

    def __str__(self):
        return str(self.value) + '(2Q1K)'

    def permu(self, Space_num, Flag_num):
        if Space_num + Flag_num < self.value or Flag_num > self.value:
            return []
        return full_permu(Space_num, self.value - Flag_num)

    def near(self, pos: tuple, board: board, model: str = 'nearby'):
        if model == 'nearby':
            nearby = []
            for xi, yi in self.circle:
                neighbor = board.get_pos((pos[0] + xi, pos[1] + yi))
                nearby.append(neighbor)
            return nearby
        if model == 'sf':
            Space = []
            Flag_num = 0
            for xi, yi in self.circle:
                V_Space = []
                for Ei in range(1, board.Size_N):
                    neighbor = board.get_pos((pos[0] + Ei * xi, pos[1] + Ei * yi))
                    if neighbor == 'off board':
                        if V_Space:
                            Space.append(V_Space[:])
                        break
                    elif neighbor is None:
                        V_Space.append((pos[0] + Ei * xi, pos[1] + Ei * yi))
                    elif neighbor is True:
                        Flag_num += 1
                        break
                else:
                    Space.append(V_Space[:])
            return (Space, Flag_num)

    def create_self(self, pos: tuple, board: board):
        nearby = self.near(pos, board, 'sf')
        self.value = nearby[1]

    def permution(self, pos: tuple, board: board):
        nearby = self.near(pos, board, 'sf')
        Space_num = len(nearby[0])
        Flag_num = nearby[1]
        poss = []
        if Space_num + Flag_num < self.value or Flag_num > self.value:
            return False
        pem = self.permu(Space_num, Flag_num)
        for i in pem:
            poss_list = [board.clone()]
            for Space in nearby[0]:
                if i & 1:
                    for _ in range(len(poss_list)):
                        poss_poss = poss_list.pop(0)
                        for space_pos in Space:
                            poss_list.append(poss_poss.clone())
                            poss_list[-1].set_pos(space_pos, True)
                else:
                    for _ in range(len(poss_list)):
                        poss_poss = poss_list.pop(0)
                        poss_list.append(poss_poss.clone())
                        for space_pos in Space:
                            poss_list[-1].set_pos(space_pos, False)
                i >>= 1
            poss += poss_list
        return poss


class clue_tem(clue):
    def __init__(self, value: int):
        self.value = value
        self.circle = [(0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1)]

    def __str__(self):
        return str(self.value) + '(tem)'

    def permu(self, W_Space: int, B_Space: int, W_Flag: int, B_Flag: int, B_all: int):
        RT = []
        if self.value == 0:
            for i in range(W_Space + 1):
                if W_Flag + i - B_Flag < 0 or W_Flag + i - B_Flag > B_Space:
                    continue
                RT.append((full_permu(W_Space, i), full_permu(B_Space, W_Flag + i - B_Flag)))
        else:
            for i in range(W_Space + 1):
                if W_Flag + i < B_Flag + self.value - B_all or W_Flag + i > B_Flag + B_Space + self.value - B_all:
                    continue
                RT.append((full_permu(W_Space, i), full_permu(B_Space, W_Flag + i - B_Flag - self.value + B_all)))
        return RT

    def near(self, pos: tuple, board: board, model: str = 'nearby'):
        if model == 'nearby':
            nearby = []
            for xi, yi in self.circle:
                neighbor = board.get_pos((pos[0] + xi, pos[1] + yi))
                neighbor_dye = board.get_dye((pos[0] + xi, pos[1] + yi))
                nearby.append((neighbor, neighbor_dye))
            return nearby
        if model == 'sf':
            W_Space = []
            B_Space = []
            W_Flag = 0
            B_Flag = 0
            B_all = int(board.get_dye(pos) is False)
            for xi, yi in self.circle:
                neighbor = board.get_pos((pos[0] + xi, pos[1] + yi))
                neighbor_dye = board.get_dye((pos[0] + xi, pos[1] + yi))
                if neighbor is None:
                    if neighbor_dye:
                        W_Space.append((pos[0] + xi, pos[1] + yi))
                    else:
                        B_Space.append((pos[0] + xi, pos[1] + yi))
                if neighbor is True:
                    if neighbor_dye:
                        W_Flag += 1
                    else:
                        B_Flag += 1
                if neighbor_dye is False:
                    B_all += 1
            return (W_Space, B_Space, W_Flag, B_Flag, B_all)

    def create_self(self, pos: tuple, board: board):
        nearby = self.near(pos, board, 'sf')
        self.value = nearby[2] - nearby[3] + nearby[4]

    def permution(self, pos: tuple, board: board):
        W_Space, B_Space, W_Flag, B_Flag, B_all = self.near(pos, board, 'sf')
        pem = self.permu(len(W_Space), len(B_Space), W_Flag, B_Flag, B_all)
        poss = []
        for Wpem, Bpem in pem:
            for Wi in Wpem:
                step_W = board.clone()
                for space_pos in W_Space:
                    if Wi & 1:
                        step_W.set_pos(space_pos, True)
                    else:
                        step_W.set_pos(space_pos, False)
                    Wi >>= 1
                for Bi in Bpem:
                    step_B = step_W.clone()
                    for space_pos in B_Space:
                        if Bi & 1:
                            step_B.set_pos(space_pos, True)
                        else:
                            step_B.set_pos(space_pos, False)
                        Bi >>= 1
                    poss.append(step_B.clone())
        return poss
