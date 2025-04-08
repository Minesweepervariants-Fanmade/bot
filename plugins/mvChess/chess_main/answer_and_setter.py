from .clue import *
from .rule import *
import random as r


def answer(Q_board: board, rules: list[str] = ['R'], all_check=False):
    str_rules = rules[:]
    rules = []
    for i in str_rules:
        rules.append(find_rule(i))
    ATPOTP = [Q_board.clone()]
    A_board = Q_board.clone()
    for pos, value in Q_board('C'):
        ATPOTP_new = []
        for poss in ATPOTP:
            pem = value.permution(pos, poss)
            if pem:
                for pem_poss in pem:
                    lazy_pem_poss = None
                    while lazy_pem_poss != pem_poss:
                        lazy_pem_poss = pem_poss.clone()
                        for rl in rules:
                            if not (rl.easy_check(pem_poss)):
                                break
                        else:
                            continue
                        break
                    else:
                        ATPOTP_new.append(pem_poss)
        ATPOTP = ATPOTP_new
        #print(ATPOTP[0])
    if len(ATPOTP) == 0:
        return False

    if all_check:
        for rl in rules:
            ATPOTP_new = []
            for poss in ATPOTP:
                pem = rl.check(poss)
                if pem:
                    ATPOTP_new += pem
            ATPOTP = ATPOTP_new

        if ATPOTP == []:
            return False

    first_poss = ATPOTP.pop()
    for pos, value in Q_board('N'):
        first_value = first_poss.get_pos(pos)
        for j in ATPOTP:
            if j.get_pos(pos) != first_value:
                break
        else:
            A_board.set_pos(pos, first_value)
    return A_board


def setter(N, choice_list=['V'], model='@c', rules=['R'], R=None, H=None, str_board: list[str] = False):
    str_rules = rules[:]
    rules = []
    for i in str_rules:
        rules.append(find_rule(i))
    count = float('inf')
    if H is None:
        H = N
    if R is None:
        R = ((N * H + 1) << 1) // 5
        if N == H:
            for rl in rules:
                if isinstance(rl, (rule_1B, rule_2B)):
                    R = ((R + (N >> 1)) // N) * N
                    break
                if isinstance(rl, (rule_1D, rule_1H, rule_1D_sp, rule_1U, rule_1A, rule_3T)):
                    R = (((N * N) // 3) >> 1) << 1
                    break
                if isinstance(rl, (rule_2T)):
                    R = (N * N) >> 1
                    break
    while count > (N * H - R) * 3 // 2:
        Q = board(N, H, model)
        Q_random = Q.random(choice_list, R, rules, str_board=str_board)
        if Q_random is False:
            continue
        elif isinstance(Q_random, list):
            liar_pos = Q_random
        else:
            liar_pos = []
        clue_list = []
        for pos, value in Q('C'):
            clue_list.append(pos)
        lazy_Q = []
        clue_size = []
        count = 0
        clue_del_num = 0
        while clue_del_num == 0:
            if len(clue_list) == 0:
                for pos, value in Q('C'):
                    clue_list.append(pos)
                clue_del_num = 0
            if lazy_Q == Q:
                count += 3 - Q.get_pos(pos).weak()
                print(str(count) + '/' + str((N * H - R) * 3 // 2))
                Q.create_txt('board_topic.txt', rules=str_rules)
            else:
                print('\n' * 20)
                print(Q)
                pass
            if count > (N * H - R):
                break
            lazy_Q = Q.clone()
            pos = clue_list.pop(r.randint(0, len(clue_list) - 1))
            print('surplus:' + str(len(clue_list)))
            Q_test = Q.clone()

            Q_test.set_pos(pos, None)
            A_Q_test = answer(Q_test, str_rules, all_check=(len(rules) > 1))
            if A_Q_test is False:
                count = float('inf')
                break
            if A_Q_test.has_None():
                Q.set_pos(pos, None)
                continue

            if pos in liar_pos:
                continue

            Q_test.set_pos(pos, False)
            A_Q_test = answer(Q_test, str_rules, all_check=(len(rules) > 1))
            if A_Q_test is False:
                count = float('inf')
                break
            if A_Q_test.has_None():
                count += 2 - Q.get_pos(pos).weak()
                print(str(count) + '/' + str((N * H - R) * 3 // 2))
                Q.set_pos(pos, False)
                Q.set_subord_pos(pos, False)
                continue
    return Q


def main():
    rules = ['1Q', '1D']
    clue_list = ['V']
    size = 8
    mini_bool = (len(clue_list) > 1) or ('1E\'' in clue_list) or ('1#' in clue_list) or ('1#\'' in clue_list) or (
            '2#' in clue_list) or ('自创' in clue_list) or ('all' in clue_list)
    Q = setter(N=size, choice_list=clue_list, model='@', rules=rules)  #,str_board=str_B)
    A_Q = answer(Q, rules=rules, all_check=False)
    print('\n' * 20)
    print(Q)
    Q.create_photo('board_topic.png', 80, mini_bool)
    Q.create_txt('board_topic.txt', rules=rules)
    print(A_Q)
    A_Q.create_photo('board_answer.png', 80, mini_bool)
    #answer(Q,rules=[]).create_photo('board_answer_NR.png',80,mini_bool)


if __name__ == '__main__':
    main()
