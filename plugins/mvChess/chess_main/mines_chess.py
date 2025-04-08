from .answer_and_setter import *


class MVChess:
    def __init__(self, choice_clue_list=None, rules=None, dye='@c'):
        if rules is None:
            rules = []
        if choice_clue_list is None:
            choice_clue_list = ['V', '1M', '1W', '1N', '1X', '1P', '1K', '1L',
                                '1E', '1L1M', '1M1X', '1M1N', '1N1X', '1X\'',
                                '1W\'', '1E\'', '2X', '2D', '2M', '2P']
        self.Q = board(8, dye=dye)
        self.clue_list = choice_clue_list
        self.rules = rules

        self.Q.create_photo(output_name="mines_game.png", size=100)

    def game_round(self, input_clue: clue, input_str_pos: str):
        input_pos = (ord(input_str_pos[0]) - 65, int(input_str_pos[1]) - 1)
        old_Q = self.Q.clone()
        if not (self.Q.set_pos(input_pos, input_clue)):
            raise ValueError(input_str_pos)
        A_Q = answer(self.Q, rules=self.rules, all_check=False)
        self.Q.create_photo(output_name='mines_game.png', size=100)
        if A_Q is False:
            self.over(old_Q)
            return 'over'
        return 'again'

    def over(self, input_board):
        return answer(input_board, rules=self.rules, all_check=False).create_photo(
            output_name='mines_game_over.png', size=100)

    def choice_clue(self, val=5):
        choice_list = []
        for i in range(val):
            new_clue = find_clue(choice(self.clue_list))
            # new_clue=find_clue(choice(['V','1M','1W','1N','1X','1P','1K','1L','1E','1M1L','1M1X','1M1N','1N1X','1X\'','1W\'','1E\'','2X','2D','2M','2P']))
            if isinstance(new_clue, clue_1E):
                new_clue.value = randint(1, self.Q.Size_N) + randint(1, self.Q.Size_H) - 1
            elif isinstance(new_clue, clue_2I):
                new_clue.value = randint(0, 7)
            elif isinstance(new_clue, clue_2X):
                new_clue.value = [randint(0, 2) + randint(0, 2), randint(0, 2) + randint(0, 2)]
            elif isinstance(new_clue, clue_2M):
                new_clue.value = randint(0, 2)
            elif isinstance(new_clue, clue_2P):
                new_clue.value = randint(1, 3) ** 2 + randint(1, 3) ** 2
            elif isinstance(new_clue, clue_1E_sp):
                new_clue.value = randint(1, self.Q.Size_N) - randint(1, self.Q.Size_H)
            elif isinstance(new_clue, clue_1M):
                new_clue.value = randint(0, 6) + randint(0, 6)
            elif isinstance(new_clue, clue_1L):
                new_clue.value = randint(0, 3) + randint(0, 3) + randint(0, 3)
            elif isinstance(new_clue, clue_1L1M):
                new_clue.value = randint(0, 4) + randint(0, 4) + randint(0, 5)
            elif isinstance(new_clue, (clue_1X_sp, clue_1P, clue_1N, clue_1N1X)):
                new_clue.value = randint(0, 4)
            elif isinstance(new_clue, clue_1W):
                match randint(0, 1) + randint(0, 2):
                    case 0:
                        new_clue.value = []
                    case 1:
                        new_clue.value = [randint(1, 8)]
                    case 2:
                        new_clue.value = []
                        new_clue.value.append(randint(1, 5))
                        new_clue.value.append(randint(1, 6 - new_clue.value[0]))
                        new_clue.value.sort()
                    case 3:
                        match randint(1, 5):
                            case 1:
                                new_clue.value = [1, 1, 1, 1]
                            case 2:
                                new_clue.value = [1, 1, 1]
                            case 3:
                                new_clue.value = [1, 1, 2]
                            case 4:
                                new_clue.value = [1, 2, 2]
                            case 5:
                                new_clue.value = [1, 1, 3]
            else:
                new_clue.value = randint(0, 8)
            choice_list.append(new_clue)
        return choice_list
