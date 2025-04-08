from .answer_and_setter import *

if __name__ == '__main__':
    Q, rules = encode_txt_to_board(input='main.txt')
    print(Q)
    A_Q = answer(Q, rules=['1A'])
    print(A_Q)
    A_Q.create_photo(size=100, mini_bool=True)
    #print(encode_txt_to_board(input='board_topic.txt')[0])
