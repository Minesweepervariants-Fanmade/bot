from .class_board import board as board_class
from random import randint,choice
from .clue import clue

def full_permu(N,R,record_bool=True,record=[]):
        if R<0 or R>N:
            return []
        if record_bool:
            record=[[False for _ in range(R+1)] for _ in range(N+1)]
        elif record[N][R]:
            return record[N][R]
        if R==0:
            record[N][R]=[0]
            return [0]
        if R==N:
            record[N][R]=[(1<<N)-1]
            return [(1<<N)-1]
        strs=[]
        if N & 1:
            strs=full_permu(N-1,R,False,record)
            for i in full_permu(N-1,R-1,False,record):
                strs.append((1<<(N-1))+i)
            record[N][R]=strs[:]
            return strs
        for i in range(max(R-(N>>1),0),min((N>>1),R)+1):
            K=full_permu((N>>1),R-i,False,record)
            for j in full_permu((N>>1),i,False,record):
                for k in K:
                    strs.append((j<<(N>>1))+k)
        record[N][R]=strs[:]
        return strs

def find_rule(rule_str:str):
    match rule_str:
        case 'R':
            return rule_R()
        case '1Q':
            return rule_1Q()
        case '1T':
            return rule_1T()
        case '1D':
            return rule_1D()
        case '1B':
            return rule_1B()
        case '1H':
            return rule_1H(model='@h')
        case '~1H':
            return rule_1H(model='@v')
        case '1A':
            return rule_1A()
        case '1D\'':
            return rule_1D_sp()
        case '1U':
            return rule_1U()
        case '2H':
            return rule_2H(model='@h')
        case '~2H':
            return rule_2H(model='@v')
        case '2F':
            return rule_2F()
        case '2S':
            return rule_2S(model='@h')
        case '~2S':
            return rule_2S(model='@v')
        case '2B':
            return rule_2B(model='@h')
        case '~2B':
            return rule_2B(model='@v')
        case '2T':
            return rule_2T()
        case '2Z':
            return rule_2Z(model='@h')
        case '~2Z':
            return rule_2Z(model='@v')
        case '3T':
            return rule_3T()

class rule:
    def __init__(self):
        pass

class rule_R(rule):
    def check(self,board:board_class)->list[board_class]:
        if board.mines_R==-1:
            return [board.clone()]
        mines_R=0
        Space=[]
        for pos,value in board('NF'):
            if value is True:
                mines_R+=1
            elif value is None:
                Space.append(pos)
        if mines_R>board.mines_R or mines_R+len(Space)<board.mines_R:
            return False
        pem=full_permu(len(Space),board.mines_R-mines_R)
        poss=[]
        for i in pem:
            poss.append(board.clone())
            for space_pos in Space:
                if i & 1:
                    poss[-1].set_pos(space_pos,True)
                else:
                    poss[-1].set_pos(space_pos,False)
                i>>=1
        return poss
    def easy_check(self,board:board_class)->bool:
        mines=0
        space=0
        for pos,value in board('NF'):
            if value is True:
                mines+=1
            elif value is None:
                space+=1
        if mines>board.mines_R or mines+space<board.mines_R:
            return False
        elif mines==board.mines_R:
            for pos,value in board('N'):
                board.set_pos(pos,False)
        elif mines+space==board.mines_R:
            for pos,value in board('N'):
                board.set_pos(pos,True)
        return True
    def r_check(self,board:board_class)->list[list]:
        return board.board
    
class rule_1Q(rule):
    def __init__(self):
        self.circle=[(-1,-1),(0,-1),(-1,0),(0,0)]
    def check(self,board:board_class)->list[board_class]:
        poss=[board.clone()]
        for y in range(1,board.Size_H):
            for x in range(1,board.Size_N):
                new_poss=[]
                for poss_poss in poss:
                    Space=[]
                    Safe_num=0
                    for dx,dy in self.circle:
                        if poss_poss.get_pos((x+dx,y+dy)) is True:
                            break
                        elif poss_poss.get_pos((x+dx,y+dy)) is None:
                            Space.append((x+dx,y+dy))
                        else:
                            Safe_num+=1
                    else:
                        if Safe_num==4:
                            return []
                        else:
                            for pos in Space:
                                pem_poss_T=poss_poss.clone()
                                pem_poss_T.set_pos(pos,True)
                                new_poss.append(pem_poss_T)
                            continue
                    new_poss.append(poss_poss.clone())
                poss=new_poss
        return poss
    def easy_check(self,board:board_class)->bool:
        for y in range(1,board.Size_H):
            for x in range(1,board.Size_N):
                Safe_num=0
                Space_pos=(-1,-1)
                for dx,dy in self.circle:
                    if board.get_pos((x+dx,y+dy)) is True:
                        break
                    elif board.get_pos((x+dx,y+dy)) is not None:
                        Safe_num+=1
                    else:
                        Space_pos=(x+dx,y+dy)
                else:
                    if Safe_num==4:
                        return False
                    elif Safe_num==3:
                        board.set_pos(Space_pos,True)
        return True
    def r_check(self,board:board_class)->list[list]:
        bool_list=[[False for _ in range(board.Size_N)] for _ in range(board.Size_H)]
        count=0
        mines=0
        dR=0
        bool_list_pos=[]
        for (dx,dy),_ in board('F'):
            bool_list[dy][dx]=True
            mines+=1
        for y in range(1,board.Size_H):
            for x in range(1,board.Size_N):
                Space=[]
                for dx,dy in self.circle:
                    if board.get_pos((x+dx,y+dy)) is True:
                        break
                    if board.get_pos((x+dx,y+dy)) is None:
                        Space.append((x+dx,y+dy))
                else:
                    if len(Space)==1:
                        dR+=1
                        mines+=1
                        dx,dy=Space.pop()
                        board.set_pos((dx,dy),True)
                        bool_list[dy][dx]=True
                    else:
                        for dx,dy in Space:
                            if bool_list[dy][dx]:
                                for xi,yi in bool_list_pos[bool_list[dy][dx]-1]:
                                    if (xi,yi) not in Space:
                                        bool_list[yi][xi]=False
                                break
                        else:
                            count+=1
                            for dx,dy in Space:
                                bool_list[dy][dx]=count
                            bool_list_pos.append(Space[:])
        if mines+count==board.mines_R:
            for pos,_ in board('N'):
                if bool_list[pos[1]][pos[0]] is False:
                    board.set_pos(pos,False)
        return board.board

class rule_1C(rule):
    def __init__(self):
        self.circle=[(0,-1),(1,-1),(1,0),(1,1),(0,1),(-1,1),(-1,0),(-1,-1)]
    def min_dis(self,board:board_class)->tuple[list[list],int]:
        Q=[[False for _ in range(board.Size_N)] for _ in range(board.Size_H)]
        for pos,value in board('NF'):
            Q[pos[1]][pos[0]]=value
        all_dis=[[1 for _ in range(board.Size_N)] for _ in range(board.Size_H)]
        Flag_pos=[[False for _ in range(board.Size_N)] for _ in range(board.Size_H)]
        for y in range(board.Size_H):
            for x in range(board.Size_N):
                if Q[y][x] is True and Flag_pos[y][x] is False:
                    pos_queue=[(x,y)]
                    lco_dis=[[float("inf") for _ in range(board.Size_N)] for _ in range(board.Size_H)]
                    all_dis[y][x]-=1
                    Flag_pos[y][x]=True
                    lco_dis[y][x]=0
                    for dis_x,dis_y in pos_queue:
                        for dx,dy in self.circle:
                            if -1<dis_y+dy<board.Size_H and -1<dis_x+dx<board.Size_N and Flag_pos[dis_y+dy][dis_x+dx] is False:
                                if Q[dis_y+dy][dis_x+dx] is True:
                                    pos_queue.append((dis_x+dx,dis_y+dy))
                                    Flag_pos[dis_y+dy][dis_x+dx]=True
                                else:
                                    lco_dis[dis_y+dy][dis_x+dx]=0
                    changed=True
                    while changed:
                        changed=False
                        for dis_y in range(board.Size_H):
                            for dis_x in range(board.Size_N):
                                if Q[dis_y][dis_x] is not False:
                                    lazy_value=lco_dis[dis_y][dis_x]
                                    for dx,dy in self.circle:
                                        if -1<dis_y+dy<board.Size_H and -1<dis_x+dx<board.Size_N and Q[dis_y+dy][dis_x+dx] is not False:
                                            lco_dis[dis_y][dis_x]=min(lco_dis[dis_y][dis_x],lco_dis[dis_y+dy][dis_x+dx]+(not Q[dis_y+dy][dis_x+dx]))
                                    if lazy_value!=lco_dis[dis_y][dis_x]:
                                        changed=True
                    for dis_y in range(board.Size_H):
                        for dis_x in range(board.Size_N):
                            if Q[dis_y][dis_x] is not False:
                                all_dis[dis_y][dis_x]+=lco_dis[dis_y][dis_x]
                    1==1
                elif Q[y][x] is False:
                    all_dis[y][x]=float('inf')
        RT=float('inf')
        for row in all_dis:
            RT=min(RT,min(row))
            #print(row)
        #print(RT)
        return (all_dis,RT)
    def check(self,board:board_class)->list[board_class]:
        if board.mines_R==-1:
            return [board.clone()]
        mines_R=0
        Space=[]
        for pos,value in board('NF'):
            if value is True:
                mines_R+=1
            elif value is None:
                Space.append(pos)
        if mines_R>board.mines_R or mines_R+len(Space)<board.mines_R:
            return False
        pem=full_permu(len(Space),board.mines_R-mines_R)
        poss=[]
        for i in pem:
            poss.append(board.clone())
            for space_pos in Space:
                if i & 1:
                    poss[-1].set_pos(space_pos,True)
                else:
                    poss[-1].set_pos(space_pos,False)
                i>>=1
        return poss
    def easy_check(self,board:board_class)->bool:
        return True
    def r_check(self,board:board_class)->list[list]:
        _,min_D=self.min_dis(board)
        mines=0
        for pos,_ in board('F'):
            mines+=1
        if min_D+mines==board.mines_R:
            all_path=[[False for _ in range(board.Size_N)] for _ in range(board.Size_H)]
            queue=[board.clone()]
            for c_brd in queue:
                all_dis,min_D=self.min_dis(queue.pop(0))
                if min_D:
                    for y in range(board.Size_H):
                        for x in range(board.Size_N):
                            if all_dis[y][x]==min_D and c_brd.get_pos((x,y)) is None:
                                queue.append(c_brd.clone())
                                queue[-1].set_pos((x,y),True)
                else:
                    for pos,_ in c_brd('F'):
                        all_path[pos[1]][pos[0]]=True
            for y in range(board.Size_H):
                for x in range(board.Size_N):
                    if all_path[y][x] is False:
                        board.set_pos((x,y),False)
        return board.board

class rule_1T(rule):
    def __init__(self):
        self.circle=[(1,0,2,0),(-1,1,-2,2),(0,1,0,2),(1,1,2,2)]
    def check(self,board:board_class)->list[board_class]:
        poss=[board.clone()]
        for y in range(0,board.Size_H):
            for x in range(0,board.Size_N):
                for _ in range(len(poss)):
                    poss_poss=poss.pop(0)
                    if poss_poss.get_pos((x,y)) is True:
                        T_poss=[poss_poss.clone()]
                        for dxi,dyi,dxj,dyj in self.circle:
                            I=poss_poss.get_pos((x+dxi,y+dyi))
                            J=poss_poss.get_pos((x+dxj,y+dyj))
                            if I is True:
                                if J is None:
                                    for _ in range(len(T_poss)):
                                        T_test=T_poss.pop()
                                        T_poss.append(T_test.clone())
                                        T_poss[-1].set_pos((x+dxj,y+dyj),False)
                                elif J is True:
                                    return []
                            elif I is None:
                                if J is True:
                                    for _ in range(len(T_poss)):
                                        T_test=T_poss.pop()
                                        T_poss.append(T_test.clone())
                                        T_poss[-1].set_pos((x+dxi,y+dyi),False)
                                elif J is None:
                                    for _ in range(len(T_poss)):
                                        T_test=T_poss.pop()
                                        T_poss.append(T_test.clone())
                                        T_poss[-1].set_pos((x+dxj,y+dyj),False)
                                        T_poss.append(T_test.clone())
                                        T_poss[-1].set_pos((x+dxi,y+dyi),False)
                        poss+=T_poss
                    elif poss_poss.get_pos((x,y)) is None:
                        T_poss=[poss_poss.clone()]
                        for dxi,dyi,dxj,dyj in self.circle:
                            I=poss_poss.get_pos((x+dxi,y+dyi))
                            J=poss_poss.get_pos((x+dxj,y+dyj))
                            if (I is True)and(J is True):
                                poss.append(poss_poss.clone())
                                poss[-1].set_pos((x,y),False)
                                break
                            elif (I is None)and((J is True)or(J is None)):
                                if len(T_poss)==1:
                                    T_poss[-1].set_pos((x,y),False)
                                T_poss.append(poss_poss.clone())
                                T_poss[-1].set_pos((x+dxi,y+dyi),False)
                        else:
                            poss+=T_poss
                    else:
                        poss.append(poss_poss.clone())       
        return poss
    def easy_check(self,board:board_class):
        for pos,value in board('NF'):
                if value is True:
                    x,y=pos
                    for dxi,dyi,dxj,dyj in self.circle:
                        if (board.get_pos((x+dxi,y+dyi)) is True and board.get_pos((x+dxj,y+dyj)) is True):
                            return False
                if value is None:
                    x,y=pos
                    for dxi,dyi,dxj,dyj in self.circle:
                        if (board.get_pos((x+dxi,y+dyi)) is True and board.get_pos((x+dxj,y+dyj)) is True)or(board.get_pos((x-dxi,y-dyi)) is True and board.get_pos((x-dxj,y-dyj)) is True)or(board.get_pos((x+dxi,y+dyi)) is True and board.get_pos((x-dxi,y-dyi)) is True):
                            board.set_pos(pos,False)
        return True
    def r_check(self,board_Y:board_class)->list[list]:
        for pos,_ in board_Y('N'):
            x,y=pos
            for dxi,dyi,dxj,dyj in self.circle:
                if (board_Y.get_pos((x+dxi,y+dyi)) is True and board_Y.get_pos((x+dxj,y+dyj)) is True)or(board_Y.get_pos((x-dxi,y-dyi)) is True and board_Y.get_pos((x-dxj,y-dyj)) is True)or(board_Y.get_pos((x+dxi,y+dyi)) is True and board_Y.get_pos((x-dxi,y-dyi)) is True):
                    board_Y.set_pos((x,y),False)
                    break
        return board_Y.board

class rule_1D(rule):
    def __init__(self):
        self.V_circle=[(0,-1),(1,-1),(1,0),(1,1),(0,1),(-1,1),(-1,0),(-1,-1)]
        self.circle=[(0,-1,[(-1,0),(1,0),(0,1)]),(1,0,[(0,-1),(-1,0),(0,1)]),(0,1,[(0,-1),(-1,0),(1,0)]),(-1,0,[(0,-1),(1,0),(0,1)])]
        self.circle=[(0,-1,[(0,-2),(-1,-1),(1,-1),(-1,0),(1,0),(0,1)]),(1,0,[(0,-1),(1,-1),(-1,0),(2,0),(0,1),(1,1)]),(0,1,[(0,-1),(-1,0),(1,0),(-1,1),(1,1),(0,2)]),(-1,0,[(-1,-1),(0,-1),(-2,0),(1,0),(-1,1),(0,1)])]
    def check(self,board:board_class)->list[board_class]:
        lazy_poss=[]
        poss=[board.clone()]
        while lazy_poss!=poss:
            lazy_poss=poss[:]
            for y in range(0,board.Size_H):
                for x in range(0,board.Size_N):
                    for _ in range(len(poss)):
                        poss_poss=poss.pop(0)
                        if poss_poss.get_pos((x,y)) is True:
                            Flag=[]
                            Space=[]
                            for i in range(4):
                                dx,dy,_=self.circle[i]
                                if poss_poss.get_pos((x+dx,y+dy)) is True:
                                    Flag.append(i)
                                elif poss_poss.get_pos((x+dx,y+dy)) is None:
                                    Space.append(i)
                            if len(Flag)==1:
                                dx,dy,near=self.circle[Flag[0]]
                                D_poss_poss=poss_poss.clone()
                                for ddx,ddy in near:
                                    if poss_poss.get_pos((x+ddx,y+ddy)) is True:
                                        break
                                    elif poss_poss.get_pos((x+ddx,y+ddy)) is None:
                                        D_poss_poss.set_pos((x+ddx,y+ddy),False)
                                else:
                                    poss.append(D_poss_poss.clone())
                            else:
                                for i in Space:
                                    dx,dy,near=self.circle[i]
                                    D_poss_poss=poss_poss.clone()
                                    for ddx,ddy in near:
                                        if poss_poss.get_pos((x+ddx,y+ddy)) is True:
                                            break
                                        elif poss_poss.get_pos((x+ddx,y+ddy)) is None:
                                            D_poss_poss.set_pos((x+ddx,y+ddy),False)
                                    else:
                                        D_poss_poss.set_pos((x+dx,y+dy),True)
                                        poss.append(D_poss_poss.clone())
                        elif poss_poss.get_pos((x,y)) is None:
                            Flag=0
                            Space=0
                            for i in range(4):
                                dx,dy,_=self.circle[i]
                                if poss_poss.get_pos((x+dx,y+dy)) is True:
                                    Flag+=1
                                elif poss_poss.get_pos((x+dx,y+dy)) is None:
                                    Space+=1
                            if Flag>1 or Flag+Space==0:
                                poss_poss.set_pos((x,y),False)
                            poss.append(poss_poss.clone())
                        else:
                            poss.append(poss_poss.clone())
        return poss
    def easy_check(self,board:board_class):
        lazy_board=False
        while lazy_board!=board:
            lazy_board=board.clone()
            for pos,value in board('F'):
                x,y=pos
                Flag=[]
                Space=[]
                for i in range(4):
                    dx,dy,near=self.circle[i]
                    for ddx,ddy in near:
                        if board.get_pos((x+ddx,y+ddy)) is True:
                            if board.get_pos((x+dx,y+dy)) is None:
                                board.set_pos((x+dx,y+dy),False)
                            break
                    else:
                        if board.get_pos((x+dx,y+dy)) is True:
                            Flag.append(i)
                        elif board.get_pos((x+dx,y+dy)) is None:
                            Space.append(i)
                if len(Flag)+len(Space)==0 or len(Flag)>1:
                    return False
                elif len(Flag)==1:
                    dx,dy,near=self.circle[Flag.pop()]
                    for ddx,ddy in near:
                        if board.get_pos((x+ddx,y+ddy)) is None:
                            board.set_pos((x+ddx,y+ddy),False)
                elif len(Space)==1:
                    dx,dy,near=self.circle[Space.pop()]
                    board.set_pos((x+dx,y+dy),True)
                    for ddx,ddy in near:
                        if board.get_pos((x+ddx,y+ddy)) is None:
                            board.set_pos((x+ddx,y+ddy),False)
                elif len(Space)==2 and ((Space[0]-Space[1]) & 1):
                    match Space:
                        case [0,1]:
                            if board.get_pos((1,-1)) is None:
                                board.set_pos((1,-1),False)
                        case [1,2]:
                            if board.get_pos((1,1)) is None:
                                board.set_pos((1,1),False)
                        case [2,3]:
                            if board.get_pos((-1,1)) is None:
                                board.set_pos((-1,1),False)
                        case [0,3]:
                            if board.get_pos((-1,-1)) is None:
                                board.set_pos((-1,-1),False)
            for pos,value in board('N'):
                x,y=pos
                Flag=0
                Space=0
                for i in range(4):
                    dx,dy,near=self.circle[i]
                    for ddx,ddy in near:
                        if board.get_pos((x+ddx,y+ddy)) is True:
                            break
                    else:
                        if board.get_pos((x+dx,y+dy)) is True:
                            Flag+=1
                        elif board.get_pos((x+dx,y+dy)) is None:
                            Space+=1
                if Flag>1 or Flag+Space==0:
                    board.set_pos((x,y),False)
        return True
    def r_check(self,board:board_class)->list[list]:
        for pos,value in board('F'):
            x,y=pos
            Flag=[]
            Space=[]
            for i in range(4):
                dx,dy,_=self.circle[i]
                if board.get_pos((x+dx,y+dy)) is True:
                    Flag.append(i)
                elif board.get_pos((x+dx,y+dy)) is None:
                    Space.append(i)
            if len(Flag)==1:
                dx,dy,near=self.circle[Flag[0]]
                for ddx,ddy in near:
                    if board.get_pos((x+ddx,y+ddy)) is None:
                        board.set_pos((x+ddx,y+ddy),False)
            else:
                Flag=[]
                for i in Space:
                    dx,dy,near=self.circle[i]
                    for ddx,ddy in near:
                        if board.get_pos((x+ddx,y+ddy)) is True:
                            board.set_pos((x+dx,y+dy),False)
                            break
                    else:
                        Flag.append(i)
                if len(Flag)==1:
                    dx,dy,near=self.circle[Flag[0]]
                    board.set_pos((x+dx,y+dy),True)
                    for ddx,ddy in near:
                        if board.get_pos((x+ddx,y+ddy)) is None:
                            board.set_pos((x+ddx,y+ddy),False)
                elif len(Flag)==2 and (Flag[0]-Flag[1])%2:
                    if Flag[0]==0 and Flag[1]==3:
                        board.set_pos((x-1,y-1),False)
                    else:
                        board.set_pos((x+self.V_circle[Flag[0]+Flag[1]][0],y+self.V_circle[Flag[0]+Flag[1]][0]),False)
        for pos,value in board('F'):
            x,y=pos
            Flag=0
            Space=0
            for i in range(4):
                dx,dy,_=self.circle[i]
                if board.get_pos((x+dx,y+dy)) is True:
                    Flag+=1
                elif board.get_pos((x+dx,y+dy)) is None:
                    Space+=1
            if Flag>1 or Flag+Space==0:
                board.set_pos((x,y),False)
        return board.board

class rule_1B(rule):
    def check(self,board:board_class)->list[board_class]:
        if board.mines_R<0:
            pass
        elif board.Size_H!=board.Size_N or board.mines_R%board.Size_N>0:
            return [board.clone()]
        else:
            row_num=board.mines_R//board.Size_N
        ATPOTP=[board.clone()]
        for y in range(board.Size_N):
            row_Flag=0
            row_Space=[]
            col_Flag=0
            col_Space=0
            for x in range(board.Size_N):
                if board.get_pos((x,y)) is True:
                    row_Flag+=1
                elif board.get_pos((x,y)) is None:
                    row_Space.append(x)
                if board.get_pos((y,x)) is True:
                    col_Flag+=1
                elif board.get_pos((y,x)) is None:
                    col_Space+=1
            if row_Flag+len(row_Space)<row_num or row_Flag>row_num or col_Flag+col_Space<row_num or col_Flag>row_num:
                return []
            row_pem=full_permu(len(row_Space),row_num-row_Flag)
            for _ in range(len(ATPOTP)):
                B=ATPOTP.pop(0)
                for i in row_pem:
                    ATPOTP.append(B.clone())
                    for j in row_Space:
                        if i & 1:
                            ATPOTP[-1].set_pos((j,y),True)
                        else:
                            ATPOTP[-1].set_pos((j,y),False)
                        i>>=1
        for _ in range(len(ATPOTP)):
            B=ATPOTP.pop(0)
            for x in range(board.Size_N):
                col_Flag=0
                for y in range(board.Size_N):
                    if B.get_pos((x,y)) is True:
                        col_Flag+=1
                if col_Flag!=row_num:
                    break
            else:
                ATPOTP.append(B)
        return ATPOTP
    def easy_check(self,board:board_class)->bool:
        if board.Size_H!=board.Size_N or board.mines_R%board.Size_N>0:
            return True
        row_num=board.mines_R//board.Size_N
        for y in range(board.Size_N):
            row_Flag=0
            row_Space=[]
            col_Flag=0
            col_Space=[]
            for x in range(board.Size_N):
                if board.get_pos((x,y)) is True:
                    row_Flag+=1
                elif board.get_pos((x,y)) is None:
                    row_Space.append(x)
                if board.get_pos((y,x)) is True:
                    col_Flag+=1
                elif board.get_pos((y,x)) is None:
                    col_Space.append(x)
            if row_Flag+len(row_Space)<row_num or row_Flag>row_num or col_Flag+len(col_Space)<row_num or col_Flag>row_num:
                return False
            if row_Flag+len(row_Space)==row_num :
                for i in row_Space:
                    board.set_pos((i,y),True)
            elif row_Flag==row_num:
                for i in row_Space:
                    board.set_pos((i,y),False)
            if col_Flag+len(col_Space)==row_num :
                for i in col_Space:
                    board.set_pos((y,i),True)
            elif col_Flag==row_num:
                for i in col_Space:
                    board.set_pos((y,i),False)
        return True
    def r_check(self,board:board_class)->list[list]:
        if board.Size_H!=board.Size_N or board.mines_R%board.Size_N>0:
            return board.board
        row_num=board.mines_R//board.Size_N
        for y in range(board.Size_N):
            row_Flag=0
            row_Space=[]
            col_Flag=0
            col_Space=[]
            for x in range(board.Size_N):
                if board.get_pos((x,y)) is True:
                    row_Flag+=1
                elif board.get_pos((x,y)) is None:
                    row_Space.append(x)
                if board.get_pos((y,x)) is True:
                    col_Flag+=1
                elif board.get_pos((y,x)) is None:
                    col_Space.append(x)
            if row_Flag+len(row_Space)==row_num :
                for i in row_Space:
                    board.set_pos((i,y),True)
            elif row_Flag==row_num:
                for i in row_Space:
                    board.set_pos((i,y),False)
            if col_Flag+len(col_Space)==row_num :
                for i in col_Space:
                    board.set_pos((y,i),True)
            elif col_Flag==row_num:
                for i in col_Space:
                    board.set_pos((y,i),False)
        return board.board

class rule_1H(rule):
    def __init__(self,model='@h'):
        self.model=model
        if model=='@h':
            self.circle=[(-1,0),(1,0)]
        if model=='@v':
            self.circle=[(0,-1),(0,1)]
    def check(self,board:board_class)->list[board_class]:
        if self.easy_check(board):
            poss=[board.clone()]
            for pos,_ in board('N'):
                for _ in range(len(poss)):
                    NF_poss=poss.pop(0)
                    poss.append(NF_poss.clone())
                    if NF_poss.get_pos(pos) is None:
                        poss[-1].set_pos(pos,False)
                        poss.append(NF_poss.clone())
                        poss[-1].set_pos(pos,True)
                        for dx,dy in self.circle:
                            if NF_poss.get_pos((pos[0]+dx,pos[1]+dy)) is None:
                                poss[-1].set_pos((pos[0]+dx,pos[1]+dy),False)
            return poss
        return []
    def easy_check(self,board:board_class)->bool:
        for pos,_ in board('F'):
            for dx,dy in self.circle:
                if board.get_pos((pos[0]+dx,pos[1]+dy)) is True:
                    return False
        for pos,_ in board('F'):
            for dx,dy in self.circle:
                if board.get_pos((pos[0]+dx,pos[1]+dy)) is None:
                    board.set_pos((pos[0]+dx,pos[1]+dy),False)
        return True
    def r_check(self,board:board_class)->list[list]:
        for pos,_ in board('F'):
            for dx,dy in self.circle:
                if board.get_pos((pos[0]+dx,pos[1]+dy)) is None:
                    board.set_pos((pos[0]+dx,pos[1]+dy),False)
        return board.board

class rule_1A(rule):
    def __init__(self):
        self.circle=[(-1,-2),(1,-2),(2,-1),(2,1),(1,2),(-1,2),(-2,1),(-2,-1)]
    def check(self,board:board_class)->list[board_class]:
        if self.easy_check(board):
            poss=[board.clone()]
            for pos,_ in board('N'):
                for _ in range(len(poss)):
                    NF_poss=poss.pop(0)
                    poss.append(NF_poss.clone())
                    if NF_poss.get_pos(pos) is None:
                        poss[-1].set_pos(pos,False)
                        poss.append(NF_poss.clone())
                        poss[-1].set_pos(pos,True)
                        for dx,dy in self.circle:
                            if NF_poss.get_pos((pos[0]+dx,pos[1]+dy)) is None:
                                poss[-1].set_pos((pos[0]+dx,pos[1]+dy),False)
            return poss
        return []
    def easy_check(self,board:board_class)->bool:
        for pos,_ in board('F'):
            for dx,dy in self.circle:
                if board.get_pos((pos[0]+dx,pos[1]+dy)) is True:
                    return False
        for pos,_ in board('F'):
            for dx,dy in self.circle:
                if board.get_pos((pos[0]+dx,pos[1]+dy)) is None:
                    board.set_pos((pos[0]+dx,pos[1]+dy),False)
        return True
    def r_check(self,board:board_class)->list[list]:
        for pos,_ in board('F'):
            for dx,dy in self.circle:
                if board.get_pos((pos[0]+dx,pos[1]+dy)) is None:
                    board.set_pos((pos[0]+dx,pos[1]+dy),False)
        return board.board

class rule_1T_sp(rule):
    def __init__(self):
        self.circle=[(1,0,2,0),(-1,1,-2,2),(0,1,0,2),(1,1,2,2),(-1,0,-2,0),(1,-1,2,-2),(0,-1,0,-2),(-1,-1,-2,-2),(1,0,-1,0),(-1,1,1,-1),(0,1,0,-1),(1,1,-1,-1)]
    def check(self,board:board_class)->list[board_class]:
        poss=[board.clone()]
        for y in range(0,board.Size_H):
            for x in range(0,board.Size_N):
                for _ in range(len(poss)):
                    poss_poss=poss.pop(0)
                    if poss_poss.get_pos((x,y)) is True:
                        T_poss=[]
                        for dxi,dyi,dxj,dyj in self.circle:
                            match (poss_poss.get_pos((x+dxi,y+dyi)),poss_poss.get_pos((x+dxj,y+dyj))):
                                case (True,True):
                                    T_poss=[poss_poss.clone()]
                                    break
                                case (None,True)|(True,None)|(None,None):
                                    T_poss.append(poss_poss.clone())
                                    T_poss[-1].set_pos((x+dxi,y+dyi),True)
                                    T_poss[-1].set_pos((x+dxj,y+dyj),True)
                        poss+=T_poss
                    else:
                        poss.append(poss_poss.clone())
        return poss
    def easy_check(self,board:board_class):
        for pos,value in board('F'):
            x,y=pos
            T_sp_v=[]
            for dxi,dyi,dxj,dyj in self.circle:
                match (board.get_pos((x+dxi,y+dyi)),board.get_pos((x+dxj,y+dyj))):
                    case (True,True):
                        break
                    case (True,None)|(None,True)|(None,None):
                        T_sp_v.append((dxi,dyi,dxj,dyj))
            else:
                if len(T_sp_v)==0:
                    return False
                elif len(T_sp_v)==1:
                    dxi,dyi,dxj,dyj=T_sp_v.pop()
                    if board.get_pos((x+dxi,y+dyi))is None:
                        board.set_pos((x+dxi,y+dyi),True)
                    if board.get_pos((x+dxj,y+dyj))is None:
                        board.set_pos((x+dxj,y+dyj),True)
        return True
    def r_check(self,board_Y:board_class)->list[list]:
        mines=0
        for pos,value in board_Y('F'):
            mines+=1
            x,y=pos
            T_sp_v=[]
            for dxi,dyi,dxj,dyj in self.circle:
                match (board_Y.get_pos((x+dxi,y+dyi)),board_Y.get_pos((x+dxj,y+dyj))):
                    case (True,True):
                        break
                    case (True,None)|(None,True)|(None,None):
                        T_sp_v.append((dxi,dyi,dxj,dyj))
            else:
                if len(T_sp_v)==1:
                    dxi,dyi,dxj,dyj=T_sp_v.pop()
                    if board_Y.get_pos((x+dxi,y+dyi))is None:
                        board_Y.set_pos((x+dxi,y+dyi),True)
                        mines+=1
                    if board_Y.get_pos((x+dxj,y+dyj))is None:
                        board_Y.set_pos((x+dxj,y+dyj),True)
                        mines+=1

        return board_Y.board
    

        min_mines=float('inf')
        min_mines_board=board_Y.clone()
        mines=0
        for pos,value in board_Y('NF'):
            if value is None:
                min_mines_board.set_pos(pos,False)
            else:
                mines+=1
        if mines<(board_Y.mines_R*2//3):
            return board_Y.board
        poss=self.check(board_Y)
        for TB in poss:
            mines=0
            for _ in TB('F'):
                mines+=1
            if min_mines>mines:
                min_mines=mines
                min_mines_board=board_Y.clone()
                for pos,_ in board_Y('N'):
                    min_mines_board.set_pos(pos,False)
            if min_mines==mines:
                for pos,_ in TB('F'):
                    if min_mines_board.get_pos(pos) is False:
                        min_mines_board.set_pos(pos,None)
        if min_mines==board_Y.mines_R:
            return min_mines_board.board
        return board_Y.board
    
        min_mines=0
        mines=0
        for pos,_ in board_Y('F'):
            mines+=1
            x,y=pos
            lco_min_mines=2
            Space=[]
            for dxi,dyi,dxj,dyj in self.circle:
                match (board_Y.get_pos((x+dxi,y+dyi)),board_Y.get_pos((x+dxj,y+dyj))):
                    case (True,True):
                        break
                    case (True,None)|(None,True):
                        lco_min_mines=1
                        Space.append((dxi,dyi,dxj,dyj))
                    case (None,None):
                        Space.append((dxi,dyi,dxj,dyj))
            else:
                if len(Space)==1:
                    dxi,dyi,dxj,dyj=Space.pop()
                    if board_Y.get_pos((x+dxi,y+dyi)) is None:
                        board_Y.set_pos((x+dxi,y+dyi),True)
                    if board_Y.get_pos((x+dxj,y+dyj)) is None:
                        board_Y.set_pos((x+dxj,y+dyj),True)
                else:
                    min_mines+=lco_min_mines
        return board_Y.board

class rule_1D_sp(rule):
    def __init__(self):
        self.circle=[(-1,-1),(1,-1),(1,1),(-1,1)]
    def check(self,board:board_class)->list[board_class]:
        if self.easy_check(board):
            poss=[board.clone()]
            for pos,_ in board('N'):
                for _ in range(len(poss)):
                    NF_poss=poss.pop(0)
                    poss.append(NF_poss.clone())
                    if NF_poss.get_pos(pos) is None:
                        poss[-1].set_pos(pos,False)
                        poss.append(NF_poss.clone())
                        poss[-1].set_pos(pos,True)
                        for dx,dy in self.circle:
                            if NF_poss.get_pos((pos[0]+dx,pos[1]+dy)) is None:
                                poss[-1].set_pos((pos[0]+dx,pos[1]+dy),False)
                    for i in range(board.Size_N):
                        queue=[]
                        for j in range(board.Size_H):
                            queue.append((not isinstance(board.get_pos((i,j)),clue))and(poss[-1].get_pos((i,j))))
                            if len(queue)==5:
                                Flag_num=0
                                Space=False
                                for k in range(5):
                                    if queue[k] is True:
                                        Flag_num+=1
                                    elif queue[k] is None:
                                        Space=(i,j+k-4)
                                    else:
                                        break
                                else:
                                    if Flag_num==5:
                                        break
                                    elif Flag_num==4 and Space:
                                        poss[-1].set_pos(Space,False)
                                queue.pop(0)
                        if len(queue)==5:
                            poss.pop()
                            break
                    else:
                        for i in range(board.Size_H):
                            queue=[]
                            for j in range(board.Size_N):
                                queue.append((not isinstance(board.get_pos((j,i)),clue))and(board.get_pos((j,i))))
                                if len(queue)==5:
                                    Flag_num=0
                                    Space=False
                                    for k in range(5):
                                        if queue[k] is True:
                                            Flag_num+=1
                                        elif queue[k] is None:
                                            Space=(j+k-4,i)
                                        else:
                                            break
                                    else:
                                        if Flag_num==5:
                                            break
                                        elif Flag_num==4 and Space:
                                            board.set_pos(Space,False)
                                    queue.pop(0)
                            if len(queue)==5:
                                poss.pop()
                                break
            return poss
        return []
    def easy_check(self,board:board_class)->bool:
        for pos,_ in board('F'):
            for dx,dy in self.circle:
                if board.get_pos((pos[0]+dx,pos[1]+dy)) is True:
                    return False
        for pos,_ in board('F'):
            for dx,dy in self.circle:
                if board.get_pos((pos[0]+dx,pos[1]+dy)) is None:
                    board.set_pos((pos[0]+dx,pos[1]+dy),False)
        for i in range(board.Size_N):
            queue=[]
            for j in range(board.Size_H):
                queue.append((not isinstance(board.get_pos((i,j)),clue))and(board.get_pos((i,j))))
                if len(queue)==5:
                    Flag_num=0
                    Space=False
                    for k in range(5):
                        if queue[k] is True:
                            Flag_num+=1
                        elif queue[k] is None:
                            Space=(i,j+k-4)
                        else:
                            break
                    else:
                        if Flag_num==5:
                            return False
                        elif Flag_num==4 and Space:
                            board.set_pos(Space,False)
                    queue.pop(0)
        for i in range(board.Size_H):
            queue=[]
            for j in range(board.Size_N):
                queue.append((not isinstance(board.get_pos((j,i)),clue))and(board.get_pos((j,i))))
                if len(queue)==5:
                    Flag_num=0
                    Space=False
                    for k in range(5):
                        if queue[k] is True:
                            Flag_num+=1
                        elif queue[k] is None:
                            Space=(j+k-4,i)
                        else:
                            break
                    else:
                        if Flag_num==5:
                            return False
                        elif Flag_num==4 and Space:
                            board.set_pos(Space,False)
                    queue.pop(0)
        return True
    def r_check(self,board:board_class)->list[list]:
        for pos,_ in board('F'):
            for dx,dy in self.circle:
                if board.get_pos((pos[0]+dx,pos[1]+dy)) is None:
                    board.set_pos((pos[0]+dx,pos[1]+dy),False)
        for i in range(board.Size_N):
            queue=[]
            for j in range(board.Size_H):
                queue.append((not isinstance(board.get_pos((i,j)),clue))and(board.get_pos((i,j))))
                if len(queue)==5:
                    Flag_num=0
                    Space=False
                    for k in range(5):
                        if queue[k] is True:
                            Flag_num+=1
                        elif queue[k] is None:
                            Space=(i,j+k-4)
                        else:
                            break
                    else:
                        if Flag_num==4 and Space:
                            board.set_pos(Space,False)
                    queue.pop(0)
        for i in range(board.Size_H):
            queue=[]
            for j in range(board.Size_N):
                queue.append((not isinstance(board.get_pos((j,i)),clue))and(board.get_pos((j,i))))
                if len(queue)==5:
                    Flag_num=0
                    Space=False
                    for k in range(5):
                        if queue[k] is True:
                            Flag_num+=1
                        elif queue[k] is None:
                            Space=(j+k-4,i)
                        else:
                            break
                    else:
                        if Flag_num==4 and Space:
                            board.set_pos(Space,False)
                    queue.pop(0)
        return board.board

class rule_1U(rule):
    def __init__(self):
        self.circle=[(0,-1),(1,0),(0,1),(-1,0)]
    def check(self,board:board_class)->list[board_class]:
        if self.easy_check(board):
            poss=[board.clone()]
            for pos,_ in board('N'):
                for _ in range(len(poss)):
                    NF_poss=poss.pop(0)
                    poss.append(NF_poss.clone())
                    if NF_poss.get_pos(pos) is None:
                        poss[-1].set_pos(pos,False)
                        poss.append(NF_poss.clone())
                        poss[-1].set_pos(pos,True)
                        for dx,dy in self.circle:
                            if NF_poss.get_pos((pos[0]+dx,pos[1]+dy)) is None:
                                poss[-1].set_pos((pos[0]+dx,pos[1]+dy),False)
            return poss
        return []
    def easy_check(self,board:board_class)->bool:
        for pos,_ in board('F'):
            for dx,dy in self.circle:
                if board.get_pos((pos[0]+dx,pos[1]+dy)) is True:
                    return False
        for pos,_ in board('F'):
            for dx,dy in self.circle:
                if board.get_pos((pos[0]+dx,pos[1]+dy)) is None:
                    board.set_pos((pos[0]+dx,pos[1]+dy),False)
        return True
    def r_check(self,board:board_class)->list[list]:
        for pos,_ in board('F'):
            for dx,dy in self.circle:
                if board.get_pos((pos[0]+dx,pos[1]+dy)) is None:
                    board.set_pos((pos[0]+dx,pos[1]+dy),False)
        return board.board

class rule_2H(rule):
    def __init__(self,model='@h'):
        self.model=model
        if model=='@h':
            self.circle=[(-1,0),(1,0)]
        if model=='@v':
            self.circle=[(0,-1),(0,1)]
    def check(self,board:board_class)->list[board_class]:
        poss=[board.clone()]
        for pos,_ in board('F'):
            for _ in range(len(poss)):
                H_poss=poss.pop(0)
                new_poss=[]
                for dx,dy in self.circle:
                    if H_poss.get_pos((pos[0]+dx,pos[1]+dy)) is True:
                        poss.append(H_poss.clone())
                        break
                    elif H_poss.get_pos((pos[0]+dx,pos[1]+dy)) is None:
                        new_poss.append(H_poss.clone())
                        new_poss[-1].set_pos((pos[0]+dx,pos[1]+dy),True)
                else:
                    poss+=new_poss
        return poss
    def easy_check(self,board:board_class)->bool:
        for pos,_ in board('F'):
            Space=[]
            for dx,dy in self.circle:
                if board.get_pos((pos[0]+dx,pos[1]+dy)) is True:
                    break
                elif board.get_pos((pos[0]+dx,pos[1]+dy)) is None:
                    Space.append((pos[0]+dx,pos[1]+dy))
            else:
                if len(Space)==0:
                    return False
                elif len(Space)==1:
                    board.set_pos(Space.pop(),True)
        return True
    def r_check(self,board:board_class)->list[list]:
        bool_list=[[False for _ in range(board.Size_N)] for _ in range(board.Size_H)]
        bool_list_pos=[]
        count=0
        mines=0
        for pos,_ in board('F'):
            if bool_list[pos[1]][pos[0]]:
                continue
            Space=[]
            bool_list[pos[1]][pos[0]]=True
            mines+=1
            for dx,dy in self.circle:
                if board.get_pos((pos[0]+dx,pos[1]+dy)) is True:
                    bool_list[pos[1]+dy][pos[0]+dx]=True
                    mines+=1
                    break
                elif board.get_pos((pos[0]+dx,pos[1]+dy)) is None:
                    Space.append((pos[0]+dx,pos[1]+dy))
            else:
                if len(Space)==1:
                    xi,yi=Space.pop()
                    board.set_pos((xi,yi),True)
                    bool_list[yi][xi]=True
                    mines+=1
                else:
                    for dx,dy in Space:
                        if bool_list[dy][dx]:
                            for xi,yi in bool_list_pos[bool_list[dy][dx]-1]:
                                if (xi,yi) not in Space:
                                    bool_list[yi][xi]=False
                            break
                    else:
                        count+=1
                        for dx,dy in Space:
                            bool_list[dy][dx]=count
                        bool_list_pos.append(Space[:])
        if mines+count==board.mines_R:
            for pos,_ in board('N'):
                if bool_list[pos[1]][pos[0]] is False:
                    board.set_pos(pos,False)
        return board.board

class rule_2C_1(rule):
    def __init__(self):
        self.circle=[(-1,-1),(0,-1),(-1,0),(0,0)]
    def check(self,board:board_class)->list[board_class]:
        poss=[board.clone()]
        for y in range(1,board.Size_H):
            for x in range(1,board.Size_N):
                new_poss=[]
                for poss_poss in poss:
                    Space=[]
                    Safe_num=0
                    for dx,dy in self.circle:
                        if poss_poss.get_pos((x+dx,y+dy)) is None:
                            Space.append((x+dx,y+dy))
                        elif poss_poss.get_pos((x+dx,y+dy)) is not True:
                            Safe_num+=1
                    else:
                        if Safe_num==0:
                            pem_poss_T=poss_poss.clone()
                            for pos in Space:
                                pem_poss_T.set_pos(pos,True)
                            new_poss.append(pem_poss_T)
                            match len(Space):
                                case 2:
                                    pem_poss_T=poss_poss.clone()
                                    pem_poss_T.set_pos(Space[0],False)
                                    pem_poss_T.set_pos(Space[1],False)
                                    new_poss.append(pem_poss_T)
                                case 3:
                                    for I,J in [(0,1),(0,2),(1,2)]:
                                        pem_poss_T=poss_poss.clone()
                                        pem_poss_T.set_pos(Space[I],False)
                                        pem_poss_T.set_pos(Space[J],False)
                                        new_poss.append(pem_poss_T)
                                case 4:
                                    for I,J in [(0,1),(0,2),(0,3),(1,2),(1,3),(2,3)]:
                                        pem_poss_T=poss_poss.clone()
                                        pem_poss_T.set_pos(Space[I],False)
                                        pem_poss_T.set_pos(Space[J],False)
                                        new_poss.append(pem_poss_T)
                        if Safe_num==1:
                            match len(Space):
                                case 1:
                                    pem_poss_T=poss_poss.clone()
                                    pem_poss_T.set_pos(Space[0],False)
                                    new_poss.append(pem_poss_T)
                                case 2:
                                    for I in range(2):
                                        pem_poss_T=poss_poss.clone()
                                        pem_poss_T.set_pos(Space[I],False)
                                        new_poss.append(pem_poss_T)
                                case 3:
                                    for I in range(3):
                                        pem_poss_T=poss_poss.clone()
                                        pem_poss_T.set_pos(Space[I],False)
                                        new_poss.append(pem_poss_T) 
                poss=new_poss
        return poss
    def easy_check(self,board:board_class)->bool:
        for y in range(1,board.Size_H):
            for x in range(1,board.Size_N):
                Flag_num=0
                Safe_num=0
                Space_pos=(-1,-1)
                for dx,dy in self.circle:
                    if board.get_pos((x+dx,y+dy)) is True:
                        Flag_num+=1
                    elif board.get_pos((x+dx,y+dy)) is not None:
                        Safe_num+=1
                    else:
                        Space_pos=(x+dx,y+dy)
                if Flag_num==3 and Safe_num==1:
                    return False
                elif Flag_num==3 and Safe_num==0:
                    board.set_pos(Space_pos,True)
                elif Flag_num==2 and Safe_num==1:
                    board.set_pos(Space_pos,False)
        return True
    def r_check(self,board:board_class)->list[list]:
        bool_list=[[False for _ in range(board.Size_N)] for _ in range(board.Size_H)]
        count=0
        mines=0
        dR=0
        bool_list_pos=[]
        for (dx,dy),_ in board('F'):
            bool_list[dy][dx]=True
            mines+=1
        for y in range(1,board.Size_H):
            for x in range(1,board.Size_N):
                Space=[]
                for dx,dy in self.circle:
                    if board.get_pos((x+dx,y+dy)) is True:
                        break
                    if board.get_pos((x+dx,y+dy)) is None:
                        Space.append((x+dx,y+dy))
                else:
                    if len(Space)==1:
                        dR+=1
                        mines+=1
                        dx,dy=Space.pop()
                        board.set_pos((dx,dy),True)
                        bool_list[dy][dx]=True
                    else:
                        for dx,dy in Space:
                            if bool_list[dy][dx]:
                                for xi,yi in bool_list_pos[bool_list[dy][dx]-1]:
                                    if (xi,yi) not in Space:
                                        bool_list[yi][xi]=False
                                break
                        else:
                            count+=1
                            for dx,dy in Space:
                                bool_list[dy][dx]=count
                            bool_list_pos.append(Space[:])
        if mines+count==board.mines_R:
            for pos,_ in board('N'):
                if bool_list[pos[1]][pos[0]] is False:
                    board.set_pos(pos,False)
        return board.board

class rule_2F(rule):
    def __init__(self):
        self.V_circle=[(0,-1),(1,-1),(1,0),(1,1),(0,1),(-1,1),(-1,0),(-1,-1)]
        self.circle=[(0,-1,[(-1,0),(1,0),(0,1)]),(1,0,[(0,-1),(-1,0),(0,1)]),(0,1,[(0,-1),(-1,0),(1,0)]),(-1,0,[(0,-1),(1,0),(0,1)])]
    def check(self,board:board_class)->list[board_class]:
        lazy_poss=[]
        poss=[board.clone()]
        while lazy_poss!=poss:
            lazy_poss=poss[:]
            for y in range(0,board.Size_H):
                for x in range(0,board.Size_N):
                    for _ in range(len(poss)):
                        poss_poss=poss.pop(0)
                        if poss_poss.get_dye((x,y)) is True and poss_poss.get_pos((x,y)) is True:
                            Flag=[]
                            Space=[]
                            for i in range(4):
                                dx,dy,_=self.circle[i]
                                if poss_poss.get_pos((x+dx,y+dy)) is True:
                                    Flag.append(i)
                                elif poss_poss.get_pos((x+dx,y+dy)) is None:
                                    Space.append(i)
                            if len(Flag)==1:
                                dx,dy,near=self.circle[Flag[0]]
                                D_poss_poss=poss_poss.clone()
                                for ddx,ddy in near:
                                    if poss_poss.get_pos((x+ddx,y+ddy)) is True:
                                        break
                                    elif poss_poss.get_pos((x+ddx,y+ddy)) is None:
                                        D_poss_poss.set_pos((x+ddx,y+ddy),False)
                                else:
                                    poss.append(D_poss_poss.clone())
                            else:
                                for i in Space:
                                    dx,dy,near=self.circle[i]
                                    D_poss_poss=poss_poss.clone()
                                    for ddx,ddy in near:
                                        if poss_poss.get_pos((x+ddx,y+ddy)) is True:
                                            break
                                        elif poss_poss.get_pos((x+ddx,y+ddy)) is None:
                                            D_poss_poss.set_pos((x+ddx,y+ddy),False)
                                    else:
                                        D_poss_poss.set_pos((x+dx,y+dy),True)
                                        poss.append(D_poss_poss.clone())
                        elif poss_poss.get_dye((x,y)) is True and poss_poss.get_pos((x,y)) is None:
                            Flag=0
                            Space=0
                            for i in range(4):
                                dx,dy,_=self.circle[i]
                                if poss_poss.get_pos((x+dx,y+dy)) is True:
                                    Flag+=1
                                elif poss_poss.get_pos((x+dx,y+dy)) is None:
                                    Space+=1
                            if Flag>1 or Flag+Space==0:
                                poss_poss.set_pos((x,y),False)
                            poss.append(poss_poss.clone())
                        else:
                            poss.append(poss_poss.clone())
        return poss
    def easy_check(self,board:board_class):
        for pos,value in board('F'):
            x,y=pos
            if board.get_dye((x,y)) is True:
                Flag=[]
                Space=[]
                for i in range(4):
                    dx,dy,_=self.circle[i]
                    if board.get_pos((x+dx,y+dy)) is True:
                        Flag.append(i)
                    elif board.get_pos((x+dx,y+dy)) is None:
                        Space.append(i)
                if len(Flag)>1 or (len(Space)+len(Flag)==0):
                    return False
                elif len(Flag)==1:
                    dx,dy,near=self.circle[Flag[0]]
                    for ddx,ddy in near:
                        if board.get_pos((x+ddx,y+ddy)) is True:
                            return False
                    for ddx,ddy in near:
                        if board.get_pos((x+ddx,y+ddy)) is None:
                            board.set_pos((x+ddx,y+ddy),False)
                else:
                    Flag=[]
                    for i in Space:
                        dx,dy,near=self.circle[i]
                        for ddx,ddy in near:
                            if board.get_pos((x+ddx,y+ddy)) is True:
                                board.set_pos((x+dx,y+dy),False)
                                break
                        else:
                            Flag.append(i)
                    if len(Flag)==0:
                        return False
                    elif len(Flag)==1:
                        dx,dy,near=self.circle[Flag[0]]
                        board.set_pos((x+dx,y+dy),True)
                        for ddx,ddy in near:
                            if board.get_pos((x+ddx,y+ddy)) is None:
                                board.set_pos((x+ddx,y+ddy),False)
        for pos,value in board('N'):
            x,y=pos
            if board.get_dye((x,y)) is True:
                Flag=0
                Space=0
                for i in range(4):
                    dx,dy,_=self.circle[i]
                    if board.get_pos((x+dx,y+dy)) is True:
                        Flag+=1
                    elif board.get_pos((x+dx,y+dy)) is None:
                        Space+=1
                if Flag>1 or Flag+Space==0:
                    board.set_pos((x,y),False)
        return True
    def r_check(self,board:board_class)->list[list]:
        for pos,value in board('F'):
            x,y=pos
            if board.get_dye((x,y)) is True:
                Flag=[]
                Space=[]
                for i in range(4):
                    dx,dy,_=self.circle[i]
                    if board.get_pos((x+dx,y+dy)) is True:
                        Flag.append(i)
                    elif board.get_pos((x+dx,y+dy)) is None:
                        Space.append(i)
                if len(Flag)==1:
                    dx,dy,near=self.circle[Flag[0]]
                    for ddx,ddy in near:
                        if board.get_pos((x+ddx,y+ddy)) is None:
                            board.set_pos((x+ddx,y+ddy),False)
                else:
                    Flag=[]
                    for i in Space:
                        dx,dy,near=self.circle[i]
                        for ddx,ddy in near:
                            if board.get_pos((x+ddx,y+ddy)) is True:
                                board.set_pos((x+dx,y+dy),False)
                                break
                        else:
                            Flag.append(i)
                    if len(Flag)==1:
                        dx,dy,near=self.circle[Flag[0]]
                        board.set_pos((x+dx,y+dy),True)
                        for ddx,ddy in near:
                            if board.get_pos((x+ddx,y+ddy)) is None:
                                board.set_pos((x+ddx,y+ddy),False)
        for pos,value in board('F'):
            x,y=pos
            if board.get_dye((x,y)) is True:
                Flag=0
                Space=0
                for i in range(4):
                    dx,dy,_=self.circle[i]
                    if board.get_pos((x+dx,y+dy)) is True:
                        Flag+=1
                    elif board.get_pos((x+dx,y+dy)) is None:
                        Space+=1
                if Flag>1 or Flag+Space==0:
                    board.set_pos((x,y),False)
        return board.board

class rule_2S(rule):
    def __init__(self,model='@h'):
        self.model=model
    def check(self,board:board_class)->list[board_class]:
        poss=[board.clone()]
        if self.model=='@h':
            for y in range(board.Size_H):
                pem=[]
                for i in range(board.Size_N):
                    for j in range(i+1,board.Size_N+1):
                        pem.append((1<<j)-(1<<i))
                for x in range(board.Size_N):
                    if board.get_pos((x,y)) is True:
                        for _ in range(len(pem)):
                            num=pem.pop(0)
                            if (num>>x) & 1 == 1:
                                pem.append(num)
                    elif board.get_pos((x,y)) is not None:
                        for _ in range(len(pem)):
                            num=pem.pop(0)
                            if (num>>x) & 1 == 0:
                                pem.append(num)
                for _ in range(len(poss)):
                    S_poss=poss.pop(0)
                    for i in pem:
                        poss.append(S_poss.clone())
                        for j in range(board.Size_N):
                            if poss[-1].get_pos((j,y)) is None:
                                poss[-1].set_pos((j,y),(i & 1 == 1))
                            i>>=1
                if not(poss):
                    return []
        if self.model=='@v':
            for x in range(board.Size_N):
                pem=[]
                for i in range(board.Size_H):
                    for j in range(i+1,board.Size_H+1):
                        pem.append((1<<j)-(1<<i))
                for y in range(board.Size_H):
                    if board.get_pos((x,y)) is True:
                        for _ in range(len(pem)):
                            num=pem.pop(0)
                            if (num>>y) & 1 == 1:
                                pem.append(num)
                    elif board.get_pos((x,y)) is not None:
                        for _ in range(len(pem)):
                            num=pem.pop(0)
                            if (num>>y) & 1 == 0:
                                pem.append(num)
                for _ in range(len(poss)):
                    S_poss=poss.pop(0)
                    for i in pem:
                        poss.append(S_poss.clone())
                        for j in range(board.Size_H):
                            if poss[-1].get_pos((x,j)) is None:
                                poss[-1].set_pos((x,j),(i & 1 == 1))
                            i>>=1
                if not(poss):
                    return []
        return poss
    def easy_check(self,board:board_class)->bool:
        if self.model=='@h':
            for y in range(board.Size_H):
                pem=[]
                Space=[]
                for i in range(board.Size_N):
                    for j in range(i+1,board.Size_N+1):
                        pem.append((1<<j)-(1<<i))
                for x in range(board.Size_N):
                    if board.get_pos((x,y)) is True:
                        for _ in range(len(pem)):
                            num=pem.pop(0)
                            if (num>>x) & 1 == 1:
                                pem.append(num)
                    elif board.get_pos((x,y)) is not None:
                        for _ in range(len(pem)):
                            num=pem.pop(0)
                            if (num>>x) & 1 == 0:
                                pem.append(num)
                    else:
                        Space.append(x)
                if not(pem):
                    return False
                pem_and=1<<board.Size_N
                pem_or=0
                for num in pem:
                    pem_and&=num
                    pem_or|=num
                for x in Space:
                    if (pem_and>>x) & 1:
                        board.set_pos((x,y),True)
                    elif (pem_or>>x) & 1 == 0:
                        board.set_pos((x,y),False)
        if self.model=='@v':
            for x in range(board.Size_N):
                pem=[]
                Space=[]
                for i in range(board.Size_H):
                    for j in range(i+1,board.Size_H+1):
                        pem.append((1<<j)-(1<<i))
                for y in range(board.Size_H):
                    if board.get_pos((x,y)) is True:
                        for _ in range(len(pem)):
                            num=pem.pop(0)
                            if (num>>y) & 1 == 1:
                                pem.append(num)
                    elif board.get_pos((x,y)) is not None:
                        for _ in range(len(pem)):
                            num=pem.pop(0)
                            if (num>>y) & 1 == 0:
                                pem.append(num)
                    else:
                        Space.append(y)
                if not(pem):
                    return False
                pem_and=1<<board.Size_H
                pem_or=0
                for num in pem:
                    pem_and&=num
                    pem_or|=num
                for y in Space:
                    if (pem_and>>y) & 1:
                        board.set_pos((x,y),True)
                    elif (pem_or>>y) & 1 == 0:
                        board.set_pos((x,y),False)
        return True
    def r_check(self,board:board_class)->list[list]:
        count=0
        Space_row=0
        if self.model=='@h':
            for y in range(board.Size_H):
                Flag_min=-1
                Flag_max=-1
                for x in range(board.Size_N):
                    if board.get_pos((x,y)) is True:
                        if Flag_min<0:
                            Flag_min=x
                        Flag_max=max(Flag_max-1,x)+1
                if Flag_min==-1:
                    count+=1
                    Space_row+=1
                    continue
                for x in range(Flag_min,Flag_max):
                    board.set_pos((x,y),True)
                    count+=1
            if board.mines_R-count<board.Size_N:
                for y in range(board.Size_H):
                    Flag_min=-1
                    Flag_max=-1
                    for x in range(board.Size_N):
                        if board.get_pos((x,y)) is True:
                            if Flag_min<0:
                                Flag_min=x
                            Flag_max=max(Flag_max-1,x)+1
                    if Flag_min==-1:
                        continue
                    for x in range(Flag_min+count-board.mines_R):
                        board.set_pos((x,y),False)
                    for x in range(Flag_max+board.mines_R-count,board.Size_N):
                        board.set_pos((x,y),False)
        if self.model=='@v':
            for x in range(board.Size_N):
                Flag_min=-1
                Flag_max=-1
                for y in range(board.Size_H):
                    if board.get_pos((x,y)) is True:
                        if Flag_min<0:
                            Flag_min=x
                        Flag_max=max(Flag_max-1,y)+1
                if Flag_min==-1:
                    count+=1
                    Space_row+=1
                    continue
                for y in range(Flag_min,Flag_max):
                    board.set_pos((x,y),True)
                    count+=1
            if board.mines_R-count<board.Size_H:
                for x in range(board.Size_N):
                    Flag_min=-1
                    Flag_max=-1
                    for y in range(board.Size_H):
                        if board.get_pos((x,y)) is True:
                            if Flag_min<0:
                                Flag_min=y
                            Flag_max=max(Flag_max-1,y)+1
                    if Flag_min==-1:
                        continue
                    for y in range(Flag_min+count-board.mines_R):
                        board.set_pos((x,y),False)
                    for y in range(Flag_max+board.mines_R-count,board.Size_H):
                        board.set_pos((x,y),False)
        return board.board

class rule_2B(rule):
    def __init__(self,model='@h'):
        self.model=model
    def check(self,board:board_class)->list[board_class]:
        if board.mines_R<0:
            pass
        elif (board.mines_R%board.Size_N>0 and self.model=='@h')or(board.mines_R%board.Size_H>0 and self.model=='@v'):
            return [board.clone()]
        else:
            col_num=board.mines_R//(board.Size_N*(self.model=='@h')+board.Size_H*(self.model=='@v'))
        poss=[board.clone()]
        if self.model=='@h':
            for x in range(board.Size_N):
                for _ in range(len(poss)):
                    B_poss=poss.pop(0)
                    Space=[]
                    Flag_num=0
                    for y in range(board.Size_H):
                        if B_poss.get_pos((x,y)) is True:
                            Flag_num+=1
                        elif B_poss.get_pos((x,y)) is None:
                            Space.append((x,y))
                    if Flag_num<=col_num<=Flag_num+len(Space):
                        pem=full_permu(len(Space),col_num-Flag_num)
                        for i in pem:
                            poss.append(B_poss.clone())
                            for j in range(len(Space)):
                                poss[-1].set_pos(Space[j],((i>>j) & 1==1))
                            if x>0:
                                len_poss=len(poss)
                                u2d=[[int(poss[-1].get_pos((x-1,0)) is True)]+[0 for _ in range(board.Size_H-1)],[int(poss[-1].get_pos((x,0)) is True)]+[0 for _ in range(board.Size_H-1)]]
                                d2u=[[0 for _ in range(board.Size_H-1)]+[int(poss[-1].get_pos((x-1,board.Size_H-1)) is True)],[0 for _ in range(board.Size_H-1)]+[int(poss[-1].get_pos((x,board.Size_H-1)) is True)]]
                                for yi in range(1,board.Size_H):
                                    u2d[0][yi]=u2d[0][yi-1]+(poss[-1].get_pos((x-1,yi)) is True)
                                    u2d[1][yi]=u2d[1][yi-1]+(poss[-1].get_pos((x,yi)) is True)
                                    d2u[0][board.Size_H-yi-1]=d2u[0][board.Size_H-yi]+(poss[-1].get_pos((x-1,board.Size_H-yi-1)) is True)
                                    d2u[1][board.Size_H-yi-1]=d2u[1][board.Size_H-yi]+(poss[-1].get_pos((x,board.Size_H-yi-1)) is True)
                                for yi in range(1,board.Size_H-1):
                                    if ((poss[-1].get_pos((x,yi)) is not True)and
                                        (poss[-1].get_pos((x,yi)) is not None)and
                                        (poss[-1].get_pos((x-1,yi)) is not True)and
                                        (poss[-1].get_pos((x-1,yi)) is not None)and
                                        (u2d[0][yi-1]!=u2d[1][yi-1] or d2u[0][yi+1]!=d2u[1][yi+1])):
                                        poss.pop()
                                        break
                                if len_poss!=len(poss):
                                    continue
                            if x<board.Size_H-1:
                                for yi in range(board.Size_H):
                                    if poss[-1].get_pos((x,yi)) is True:
                                        yi_Space=[]
                                        for dy in range(-1,2):
                                            if poss[-1].get_pos((x+1,yi+dy)) is True:
                                                break
                                            elif poss[-1].get_pos((x+1,yi+dy)) is None:
                                                yi_Space.append((x+1,yi+dy))
                                        else:
                                            if len(yi_Space)==0:
                                                poss.pop()
                                                break
                                            if len(yi_Space)==1:
                                                poss[-1].set_pos(yi_Space.pop(),True)
                                    if poss[-1].get_pos((x+1,yi)) is True:
                                        for dy in range(-1,2):
                                            if poss[-1].get_pos((x,yi+dy)) is True:
                                                break
                                        else:
                                            poss.pop()
                                            break
                                    elif poss[-1].get_pos((x+1,yi)) is None:
                                        for dy in range(-1,2):
                                            if poss[-1].get_pos((x,yi+dy)) is True:
                                                break
                                        else:
                                            poss[-1].set_pos((x+1,yi),False)
        if self.model=='@v':
            for x in range(board.Size_H):
                for _ in range(len(poss)):
                    B_poss=poss.pop(0)
                    Space=[]
                    Flag_num=0
                    for y in range(board.Size_N):
                        if B_poss.get_pos((y,x)) is True:
                            Flag_num+=1
                        elif B_poss.get_pos((y,x)) is None:
                            Space.append((y,x))
                    if Flag_num<=col_num<=Flag_num+len(Space):
                        pem=full_permu(len(Space),col_num-Flag_num)
                        for i in pem:
                            poss.append(B_poss.clone())
                            for j in range(len(Space)):
                                poss[-1].set_pos(Space[j],((i>>j) & 1==1))
                            if x>0:
                                len_poss=len(poss)
                                u2d=[[int(poss[-1].get_pos((0,x-1)) is True)]+[0 for _ in range(board.Size_N-1)],[int(poss[-1].get_pos((0,x)) is True)]+[0 for _ in range(board.Size_N-1)]]
                                d2u=[[0 for _ in range(board.Size_N-1)]+[int(poss[-1].get_pos((board.Size_N-1,x-1)) is True)],[0 for _ in range(board.Size_N-1)]+[int(poss[-1].get_pos((board.Size_N-1,x)) is True)]]
                                for yi in range(1,board.Size_H):
                                    u2d[0][yi]=u2d[0][yi-1]+(poss[-1].get_pos((yi,x-1)) is True)
                                    u2d[1][yi]=u2d[1][yi-1]+(poss[-1].get_pos((yi,x)) is True)
                                    d2u[0][board.Size_N-yi-1]=d2u[0][board.Size_N-yi]+(poss[-1].get_pos((board.Size_N-yi-1,x-1)) is True)
                                    d2u[1][board.Size_N-yi-1]=d2u[1][board.Size_N-yi]+(poss[-1].get_pos((board.Size_N-yi-1,x)) is True)
                                for yi in range(1,board.Size_H-1):
                                    if ((poss[-1].get_pos((yi,x)) is not True)and
                                        (poss[-1].get_pos((yi,x)) is not None)and
                                        (poss[-1].get_pos((yi,x-1)) is not True)and
                                        (poss[-1].get_pos((yi,x-1)) is not None)and
                                        (u2d[0][yi-1]!=u2d[1][yi-1] or d2u[0][yi+1]!=d2u[1][yi+1])):
                                        poss.pop()
                                        break
                                if len_poss!=len(poss):
                                    continue
                            if x<board.Size_H-1:
                                for yi in range(board.Size_N):
                                    if poss[-1].get_pos((yi,x)) is True:
                                        yi_Space=[]
                                        for dy in range(-1,2):
                                            if poss[-1].get_pos((yi+dy,x+1)) is True:
                                                break
                                            elif poss[-1].get_pos((yi+dy,x+1)) is None:
                                                yi_Space.append((yi+dy,x+1))
                                        else:
                                            if len(yi_Space)==0:
                                                poss.pop()
                                                break
                                            if len(yi_Space)==1:
                                                poss[-1].set_pos(yi_Space.pop(),True)
                                    if poss[-1].get_pos((yi,x+1)) is True:
                                        for dy in range(-1,2):
                                            if poss[-1].get_pos((yi+dy,x)) is True:
                                                break
                                        else:
                                            poss.pop()
                                            break
                                    elif poss[-1].get_pos((yi,x+1)) is None:
                                        for dy in range(-1,2):
                                            if poss[-1].get_pos((yi+dy,x)) is True:
                                                break
                                        else:
                                            poss[-1].set_pos((yi,x+1),False)
        return poss
    def easy_check(self,board:board_class)->bool:
        if board.mines_R<0:
            pass
        elif (board.mines_R%board.Size_N>0 and self.model=='@h')or(board.mines_R%board.Size_H>0 and self.model=='@v'):
            return True
        else:
            col_num=board.mines_R//(board.Size_N*(self.model=='@h')+board.Size_H*(self.model=='@v'))
        B=board.clone()
        if self.model=='@h':
            col=[(['off board' for _ in range(board.Size_H)],[board.get_pos((0,y)) for y in range(board.Size_H)])]
            for x in range(board.Size_N):
                B_col_aft_list=[]
                B_col_pre=[None for _ in range(board.Size_H)]
                for _ in range(len(col)):
                    B_col=col.pop(0)
                    Space=[]
                    Flag_num=0
                    for y in range(board.Size_H):
                        if B_col[1][y] is True:
                            Flag_num+=1
                        elif B_col[1][y] is None:
                            Space.append(y)
                    if Flag_num<=col_num<=Flag_num+len(Space):
                        pem=full_permu(len(Space),col_num-Flag_num)
                        for i in pem:
                            B_col_aft=B_col[1][:]
                            B_col_ltr=[board.get_pos((x+1,y)) for y in range(board.Size_H)]
                            for j in range(len(Space)):
                                B_col_aft[Space[j]]=((i>>j) & 1==1)
                            if x>0:
                                u2d=[[int(B_col[0][0] is True)]+[0 for _ in range(board.Size_H-1)],[int(B_col_aft[0] is True)]+[0 for _ in range(board.Size_H-1)]]
                                d2u=[[0 for _ in range(board.Size_H-1)]+[int(B_col[0][board.Size_H-1] is True)],[0 for _ in range(board.Size_H-1)]+[int(B_col_aft[board.Size_H-1] is True)]]
                                for yi in range(1,board.Size_H):
                                    u2d[0][yi]=u2d[0][yi-1]+(B_col[0][yi] is True)
                                    u2d[1][yi]=u2d[1][yi-1]+(B_col_aft[yi] is True)
                                    d2u[0][board.Size_H-yi-1]=d2u[0][board.Size_H-yi]+(B_col[0][board.Size_H-yi-1] is True)
                                    d2u[1][board.Size_H-yi-1]=d2u[1][board.Size_H-yi]+(B_col_aft[board.Size_H-yi-1] is True)
                                for yi in range(1,board.Size_H-1):
                                    if ((B_col_aft[yi] is not True)and
                                        (B_col_aft[yi] is not None)and
                                        (B_col[0][yi] is not True)and
                                        (B_col[0][yi] is not None)and
                                        (u2d[0][yi-1]!=u2d[1][yi-1] or d2u[0][yi+1]!=d2u[1][yi+1])):
                                        B_col_aft=[]
                                        break
                                if not(B_col_aft):
                                    continue
                            if x<board.Size_H-1 and B_col_aft:
                                for yi in range(board.Size_H):
                                    if B_col_aft[yi] is True:
                                        yi_Space=[]
                                        for dy in range(-1+(yi==0),2-(yi==board.Size_H-1)):
                                            if B_col_ltr[yi+dy] is True:
                                                break
                                            elif B_col_ltr[yi+dy] is None:
                                                yi_Space.append(yi+dy)
                                        else:
                                            if len(yi_Space)==0:
                                                B_col_aft=[]
                                                break
                                            if len(yi_Space)==1:
                                                B_col_ltr[yi_Space.pop()]=True
                                    if B_col_ltr[yi] is True:
                                        for dy in range(-1+(yi==0),2-(yi==board.Size_H-1)):
                                            if B_col_aft[yi+dy] is True:
                                                break
                                        else:
                                            B_col_aft=[]
                                            break
                                    elif B_col_ltr[yi] is None:
                                        for dy in range(-1+(yi==0),2-(yi==board.Size_H-1)):
                                            if B_col_aft[yi+dy] is True:
                                                break
                                        else:
                                            B_col_ltr[yi]=False
                            if B_col_aft:
                                if B_col_aft not in B_col_aft_list:
                                    B_col_aft_list.append(B_col_aft)
                                    col.append((B_col_aft[:],B_col_ltr[:]))
                                for yi in range(board.Size_H):
                                        if B_col_pre[yi] is None:
                                            B_col_pre[yi]=B_col_aft[yi]
                                        elif B_col_pre[yi]!=B_col_aft[yi]:
                                            B_col_pre[yi]=0
                if B_col_pre:
                    for y in range(board.Size_H):
                        if isinstance(B_col_pre[y],bool):
                            B.set_pos((x-1,y),B_col_pre[y])
            if col:
                for y in range(board.Size_H):
                    if isinstance(B_col_pre[y],bool):
                        B.set_pos((x,y),B_col_pre[y])
                board=B.clone()
                return True
        if self.model=='@v':
            col=[(['off board' for _ in range(board.Size_N)],[board.get_pos((y,0)) for y in range(board.Size_N)])]
            for x in range(board.Size_H):
                B_col_aft_list=[]
                B_col_pre=[None for _ in range(board.Size_N)]
                for _ in range(len(col)):
                    B_col=col.pop(0)
                    Space=[]
                    Flag_num=0
                    for y in range(board.Size_N):
                        if B_col[1][y] is True:
                            Flag_num+=1
                        elif B_col[1][y] is None:
                            Space.append(y)
                    if Flag_num<=col_num<=Flag_num+len(Space):
                        pem=full_permu(len(Space),col_num-Flag_num)
                        for i in pem:
                            B_col_aft=B_col[1][:]
                            B_col_ltr=[board.get_pos((y,x+1)) for y in range(board.Size_N)]
                            for j in range(len(Space)):
                                B_col_aft[Space[j]]=((i>>j) & 1==1)
                            if x>0:
                                u2d=[[int(B_col[0][0] is True)]+[0 for _ in range(board.Size_N-1)],[int(B_col_aft[0] is True)]+[0 for _ in range(board.Size_N-1)]]
                                d2u=[[0 for _ in range(board.Size_N-1)]+[int(B_col[0][board.Size_N-1] is True)],[0 for _ in range(board.Size_N-1)]+[int(B_col_aft[board.Size_N-1] is True)]]
                                for yi in range(1,board.Size_N):
                                    u2d[0][yi]=u2d[0][yi-1]+(B_col[0][yi] is True)
                                    u2d[1][yi]=u2d[1][yi-1]+(B_col_aft[yi] is True)
                                    d2u[0][board.Size_N-yi-1]=d2u[0][board.Size_N-yi]+(B_col[0][board.Size_N-yi-1] is True)
                                    d2u[1][board.Size_N-yi-1]=d2u[1][board.Size_N-yi]+(B_col_aft[board.Size_N-yi-1] is True)
                                for yi in range(1,board.Size_H-1):
                                    if ((B_col_aft[yi] is not True)and
                                        (B_col_aft[yi] is not None)and
                                        (B_col[0][yi] is not True)and
                                        (B_col[0][yi] is not None)and
                                        (u2d[0][yi-1]!=u2d[1][yi-1] or d2u[0][yi+1]!=d2u[1][yi+1])):
                                        B_col_aft=[]
                                        break
                                if not(B_col_aft):
                                    continue
                            if x<board.Size_H-1 and B_col_aft:
                                for yi in range(board.Size_H):
                                    if B_col_aft[yi] is True:
                                        yi_Space=[]
                                        for dy in range(-1+(yi==0),2-(yi==board.Size_H-1)):
                                            if B_col_ltr[yi+dy] is True:
                                                break
                                            elif B_col_ltr[yi+dy] is None:
                                                yi_Space.append(yi+dy)
                                        else:
                                            if len(yi_Space)==0:
                                                B_col_aft=[]
                                                break
                                            if len(yi_Space)==1:
                                                B_col_ltr[yi_Space.pop()]=True
                                    if B_col_ltr[yi] is True:
                                        for dy in range(-1+(yi==0),2-(yi==board.Size_H-1)):
                                            if B_col_aft[yi+dy] is True:
                                                break
                                        else:
                                            B_col_aft=[]
                                            break
                                    elif B_col_ltr[yi] is None:
                                        for dy in range(-1+(yi==0),2-(yi==board.Size_H-1)):
                                            if B_col_aft[yi+dy] is True:
                                                break
                                        else:
                                            B_col_ltr[yi]=False
                            if B_col_aft:
                                if B_col_aft not in B_col_aft_list:
                                    B_col_aft_list.append(B_col_aft)
                                    col.append((B_col_aft[:],B_col_ltr[:]))
                                for yi in range(board.Size_H):
                                        if B_col_pre[yi] is None:
                                            B_col_pre[yi]=B_col_aft[yi]
                                        elif B_col_pre[yi]!=B_col_aft[yi]:
                                            B_col_pre[yi]=0
                if B_col_pre:
                    for y in range(board.Size_H):
                        if isinstance(B_col_pre[y],bool):
                            B.set_pos((y,x-1),B_col_pre[y])
            if col:
                for y in range(board.Size_H):
                    if isinstance(B_col_pre[y],bool):
                        B.set_pos((y,x),B_col_pre[y])
                board=B.clone()
                return True
        return False
    def r_check(self,board:board_class)->list[list]:
        if board.mines_R<0:
            pass
        elif (board.mines_R%board.Size_N>0 and self.model=='@h')or(board.mines_R%board.Size_H>0 and self.model=='@v'):
            return board.board
        else:
            col_num=board.mines_R//(board.Size_N*(self.model=='@h')+board.Size_H*(self.model=='@v'))
        B=board.clone()
        if self.model=='@h':
            col=[(['off board' for _ in range(board.Size_H)],[board.get_pos((0,y)) for y in range(board.Size_H)])]
            for x in range(board.Size_N):
                B_col_aft_list=[]
                B_col_pre=[None for _ in range(board.Size_H)]
                for _ in range(len(col)):
                    B_col=col.pop(0)
                    Space=[]
                    Flag_num=0
                    for y in range(board.Size_H):
                        if B_col[1][y] is True:
                            Flag_num+=1
                        elif B_col[1][y] is None:
                            Space.append(y)
                    if Flag_num<=col_num<=Flag_num+len(Space):
                        pem=full_permu(len(Space),col_num-Flag_num)
                        for i in pem:
                            B_col_aft=B_col[1][:]
                            B_col_ltr=[board.get_pos((x+1,y)) for y in range(board.Size_H)]
                            for j in range(len(Space)):
                                B_col_aft[Space[j]]=((i>>j) & 1==1)
                            if x>0:
                                u2d=[[int(B_col[0][0] is True)]+[0 for _ in range(board.Size_H-1)],[int(B_col_aft[0] is True)]+[0 for _ in range(board.Size_H-1)]]
                                d2u=[[0 for _ in range(board.Size_H-1)]+[int(B_col[0][board.Size_H-1] is True)],[0 for _ in range(board.Size_H-1)]+[int(B_col_aft[board.Size_H-1] is True)]]
                                for yi in range(1,board.Size_H):
                                    u2d[0][yi]=u2d[0][yi-1]+(B_col[0][yi] is True)
                                    u2d[1][yi]=u2d[1][yi-1]+(B_col_aft[yi] is True)
                                    d2u[0][board.Size_H-yi-1]=d2u[0][board.Size_H-yi]+(B_col[0][board.Size_H-yi-1] is True)
                                    d2u[1][board.Size_H-yi-1]=d2u[1][board.Size_H-yi]+(B_col_aft[board.Size_H-yi-1] is True)
                                for yi in range(1,board.Size_H-1):
                                    if ((B_col_aft[yi] is not True)and
                                        (B_col_aft[yi] is not None)and
                                        (B_col[0][yi] is not True)and
                                        (B_col[0][yi] is not None)and
                                        (u2d[0][yi-1]!=u2d[1][yi-1] or d2u[0][yi+1]!=d2u[1][yi+1])):
                                        B_col_aft=[]
                                        break
                                if not(B_col_aft):
                                    continue
                            if x<board.Size_H-1:
                                for yi in range(board.Size_H):
                                    if B_col_aft[yi] is True:
                                        yi_Space=[]
                                        for dy in range(-1+(yi==0),2-(yi==board.Size_H-1)):
                                            if B_col_ltr[yi+dy] is True:
                                                break
                                            elif B_col_ltr[yi+dy] is None:
                                                yi_Space.append(yi+dy)
                                        else:
                                            if len(yi_Space)==0:
                                                B_col_aft=[]
                                                break
                                            if len(yi_Space)==1:
                                                B_col_ltr[yi_Space.pop()]=True
                                    if B_col_ltr[yi] is True:
                                        for dy in range(-1+(yi==0),2-(yi==board.Size_H-1)):
                                            if B_col_aft[yi+dy] is True:
                                                break
                                        else:
                                            B_col_aft=[]
                                            break
                                    elif B_col_ltr[yi] is None:
                                        for dy in range(-1+(yi==0),2-(yi==board.Size_H-1)):
                                            if B_col_aft[yi+dy] is True:
                                                break
                                        else:
                                            B_col_ltr[yi]=False
                            if B_col_aft:
                                if B_col_aft not in B_col_aft_list:
                                    B_col_aft_list.append(B_col_aft)
                                    col.append((B_col_aft[:],B_col_ltr[:]))
                                if x>0:
                                    for yi in range(board.Size_H):
                                            if B_col_pre[yi] is None:
                                                B_col_pre[yi]=B_col[0][yi]
                                            elif B_col_pre[yi]!=B_col[0][yi]:
                                                B_col_pre[yi]=0
                if B_col_pre:
                    for y in range(board.Size_H):
                        if isinstance(B_col_pre[y],bool):
                            B.set_pos((x-1,y),B_col_pre[y])
            if col:
                for y in range(board.Size_H):
                    if isinstance(B_col_pre[y],bool):
                        B.set_pos((x,y),B_col_pre[y])
                board=B.clone()
        if self.model=='@v':
            col=[(['off board' for _ in range(board.Size_N)],[board.get_pos((y,0)) for y in range(board.Size_N)])]
            for x in range(board.Size_H):
                B_col_aft_list=[]
                B_col_pre=[None for _ in range(board.Size_N)]
                for _ in range(len(col)):
                    B_col=col.pop(0)
                    Space=[]
                    Flag_num=0
                    for y in range(board.Size_N):
                        if B_col[1][y] is True:
                            Flag_num+=1
                        elif B_col[1][y] is None:
                            Space.append(y)
                    if Flag_num<=col_num<=Flag_num+len(Space):
                        pem=full_permu(len(Space),col_num-Flag_num)
                        for i in pem:
                            B_col_aft=B_col[1][:]
                            B_col_ltr=[board.get_pos((y,x+1)) for y in range(board.Size_N)]
                            for j in range(len(Space)):
                                B_col_aft[Space[j]]=((i>>j) & 1==1)
                            if x>0:
                                u2d=[[int(B_col[0][0] is True)]+[0 for _ in range(board.Size_N-1)],[int(B_col_aft[0] is True)]+[0 for _ in range(board.Size_N-1)]]
                                d2u=[[0 for _ in range(board.Size_N-1)]+[int(B_col[0][board.Size_N-1] is True)],[0 for _ in range(board.Size_N-1)]+[int(B_col_aft[board.Size_N-1] is True)]]
                                for yi in range(1,board.Size_N):
                                    u2d[0][yi]=u2d[0][yi-1]+(B_col[0][yi] is True)
                                    u2d[1][yi]=u2d[1][yi-1]+(B_col_aft[yi] is True)
                                    d2u[0][board.Size_N-yi-1]=d2u[0][board.Size_N-yi]+(B_col[0][board.Size_N-yi-1] is True)
                                    d2u[1][board.Size_N-yi-1]=d2u[1][board.Size_N-yi]+(B_col_aft[board.Size_N-yi-1] is True)
                                for yi in range(1,board.Size_N-1):
                                    if ((B_col_aft[yi] is not True)and
                                        (B_col_aft[yi] is not None)and
                                        (B_col[0][yi] is not True)and
                                        (B_col[0][yi] is not None)and
                                        (u2d[0][yi-1]!=u2d[1][yi-1] or d2u[0][yi+1]!=d2u[1][yi+1])):
                                        B_col_aft=[]
                                        break
                                if not(B_col_aft):
                                    continue
                            if x<board.Size_H-1:
                                for yi in range(board.Size_N):
                                    if B_col_aft[yi] is True:
                                        yi_Space=[]
                                        for dy in range(-1+(yi==0),2-(yi==board.Size_N-1)):
                                            if B_col_ltr[yi+dy] is True:
                                                break
                                            elif B_col_ltr[yi+dy] is None:
                                                yi_Space.append(yi+dy)
                                        else:
                                            if len(yi_Space)==0:
                                                B_col_aft=[]
                                                break
                                            if len(yi_Space)==1:
                                                B_col_ltr[yi_Space.pop()]=True
                                    if B_col_ltr[yi] is True:
                                        for dy in range(-1+(yi==0),2-(yi==board.Size_N-1)):
                                            if B_col_aft[yi+dy] is True:
                                                break
                                        else:
                                            B_col_aft=[]
                                            break
                                    elif B_col_ltr[yi] is None:
                                        for dy in range(-1+(yi==0),2-(yi==board.Size_N-1)):
                                            if B_col_aft[yi+dy] is True:
                                                break
                                        else:
                                            B_col_ltr[yi]=False
                            if B_col_aft:
                                if B_col_aft not in B_col_aft_list:
                                    B_col_aft_list.append(B_col_aft)
                                    col.append((B_col_aft[:],B_col_ltr[:]))
                                if x>0:
                                    for yi in range(board.Size_N):
                                            if B_col_pre[yi] is None:
                                                B_col_pre[yi]=B_col[0][yi]
                                            elif B_col_pre[yi]!=B_col[0][yi]:
                                                B_col_pre[yi]=0
                if B_col_pre:
                    for y in range(board.Size_N):
                        if isinstance(B_col_pre[y],bool):
                            B.set_pos((y,x-1),B_col_pre[y])
            if col:
                for y in range(board.Size_N):
                    if isinstance(B_col_pre[y],bool):
                        B.set_pos((y,x),B_col_pre[y])
                board=B.clone()
        return board.board

class rule_2T(rule):
    def __init__(self):
        self.circle=[(1,0,2,0),(0,1,0,2)]
    def check(self,board:board_class)->list[board_class]:
        poss=[board.clone()]
        for y in range(board.Size_H):
            for x in range(board.Size_N):
                for _ in range(len(poss)):
                    poss_poss=poss.pop(0)
                    pos_value=poss_poss.get_pos((x,y))and(not isinstance(board.get_pos((x,y)),clue))
                    T_poss:list[board_class]=[poss_poss.clone()]
                    match pos_value:
                        case None:
                            for dxi,dyi,dxj,dyj in self.circle:
                                I=(not isinstance(board.get_pos((x+dxi,y+dyi)),clue))and(poss_poss.get_pos((x+dxi,y+dyi)))
                                J=(not isinstance(board.get_pos((x+dxj,y+dyj)),clue))and(poss_poss.get_pos((x+dxj,y+dyj)))
                                match (I,J):
                                    case (None,None):
                                        for _ in range(len(T_poss)):
                                            T_poss_poss=T_poss.pop(0)
                                            T_poss.append(T_poss_poss.clone())
                                            if T_poss_poss.get_pos((x,y)) is None:
                                                T_poss[-1].set_pos((x+dxi,y+dyi),False)
                                                T_poss[-1].set_pos((x+dxj,y+dyj),True)
                                                T_poss.append(T_poss_poss.clone())
                                                T_poss[-1].set_pos((x+dxi,y+dyi),True)
                                                T_poss[-1].set_pos((x+dxj,y+dyj),False)
                                                T_poss.append(T_poss_poss.clone())
                                                T_poss[-1].set_pos((x,y),True)
                                                T_poss[-1].set_pos((x+dxi,y+dyi),False)
                                                T_poss.append(T_poss_poss.clone())
                                                T_poss[-1].set_pos((x,y),True)
                                                T_poss[-1].set_pos((x+dxj,y+dyj),False)
                                                T_poss.append(T_poss_poss.clone())
                                                T_poss[-1].set_pos((x,y),False)
                                                T_poss[-1].set_pos((x+dxi,y+dyi),True)
                                                T_poss.append(T_poss_poss.clone())
                                                T_poss[-1].set_pos((x,y),False)
                                                T_poss[-1].set_pos((x+dxj,y+dyj),True)
                                            elif T_poss_poss.get_pos((x,y)) is True:
                                                T_poss[-1].set_pos((x+dxi,y+dyi),False)
                                                T_poss.append(T_poss_poss.clone())
                                                T_poss[-1].set_pos((x+dxj,y+dyj),False)
                                            elif T_poss_poss.get_pos((x,y)) is False:
                                                T_poss[-1].set_pos((x+dxi,y+dyi),True)
                                                T_poss.append(T_poss_poss.clone())
                                                T_poss[-1].set_pos((x+dxj,y+dyj),True)
                                    case (None,True):
                                        for _ in range(len(T_poss)):
                                            T_poss_poss=T_poss.pop(0)
                                            T_poss.append(T_poss_poss.clone())
                                            if T_poss_poss.get_pos((x,y)) is None:
                                                T_poss[-1].set_pos((x,y),False)
                                                T_poss.append(T_poss_poss.clone())
                                                T_poss[-1].set_pos((x+dxi,y+dyi),False)
                                            elif T_poss_poss.get_pos((x,y)) is True:
                                                T_poss[-1].set_pos((x+dxi,y+dyi),False)
                                    case (None,False):
                                        for _ in range(len(T_poss)):
                                            T_poss_poss=T_poss.pop(0)
                                            T_poss.append(T_poss_poss.clone())
                                            if T_poss_poss.get_pos((x,y)) is None:
                                                T_poss[-1].set_pos((x,y),True)
                                                T_poss.append(T_poss_poss.clone())
                                                T_poss[-1].set_pos((x+dxi,y+dyi),True)
                                            elif T_poss_poss.get_pos((x,y)) is False:
                                                T_poss[-1].set_pos((x+dxi,y+dyi),True)
                                    case (True,None):
                                        for _ in range(len(T_poss)):
                                            T_poss_poss=T_poss.pop(0)
                                            T_poss.append(T_poss_poss.clone())
                                            if T_poss_poss.get_pos((x,y)) is None:
                                                T_poss[-1].set_pos((x,y),False)
                                                T_poss.append(T_poss_poss.clone())
                                                T_poss[-1].set_pos((x+dxj,y+dyj),False)
                                            elif T_poss_poss.get_pos((x,y)) is True:
                                                T_poss[-1].set_pos((x+dxj,y+dyj),False)
                                    case (False,None):
                                        for _ in range(len(T_poss)):
                                            T_poss_poss=T_poss.pop(0)
                                            T_poss.append(T_poss_poss.clone())
                                            if T_poss_poss.get_pos((x,y)) is None:
                                                T_poss[-1].set_pos((x,y),True)
                                                T_poss.append(T_poss_poss.clone())
                                                T_poss[-1].set_pos((x+dxj,y+dyj),True)
                                            elif T_poss_poss.get_pos((x,y)) is False:
                                                T_poss[-1].set_pos((x+dxj,y+dyj),True)
                                    case (True,True):
                                        if pos_value is True:
                                            T_poss=[]
                                            break
                                        elif pos_value is None:
                                            pos_value=False
                                            ls_T_poss:list[board_class]=[]
                                            for _ in range(len(T_poss)):
                                                T_poss_poss=T_poss.pop(0)
                                                if (T_poss_poss.get_pos((x,y)) is False)or(T_poss_poss.get_pos((x,y)) is None):
                                                    T_poss.append(T_poss_poss.clone())
                                                    T_poss[-1].set_pos((x,y),False)
                                                elif T_poss_poss.get_pos((x,y)) is None:
                                                    ls_T_poss.append(T_poss_poss.clone())
                                                    ls_T_poss[-1].set_pos((x,y),False)
                                            if not(T_poss):
                                                T_poss+=ls_T_poss
                                    case (False,False):
                                        if pos_value is False:
                                            T_poss=[]
                                            break
                                        elif pos_value is None:
                                            pos_value=True
                                            ls_T_poss:list[board_class]=[]
                                            for _ in range(len(T_poss)):
                                                T_poss_poss=T_poss.pop(0)
                                                if (T_poss_poss.get_pos((x,y)) is True)or(T_poss_poss.get_pos((x,y)) is None):
                                                    T_poss.append(T_poss_poss.clone())
                                                    T_poss[-1].set_pos((x,y),True)
                                                elif T_poss_poss.get_pos((x,y)) is None:
                                                    ls_T_poss.append(T_poss_poss.clone())
                                                    ls_T_poss[-1].set_pos((x,y),True)
                                            if not(T_poss):
                                                T_poss+=ls_T_poss
                                    case (True,False)|(False,True):
                                        continue
                        case True:
                            for dxi,dyi,dxj,dyj in self.circle:
                                I=(not isinstance(board.get_pos((x+dxi,y+dyi)),clue))and(poss_poss.get_pos((x+dxi,y+dyi)))
                                J=(not isinstance(board.get_pos((x+dxj,y+dyj)),clue))and(poss_poss.get_pos((x+dxj,y+dyj)))
                                match (I,J):
                                    case (True,True):
                                        T_poss=[]
                                        break
                                    case (None,True):
                                        for _ in range(len(T_poss)):
                                            T_poss_poss=T_poss.pop(0)
                                            T_poss.append(T_poss_poss.clone())
                                            T_poss[-1].set_pos((x+dxi,y+dyi),False)
                                    case (True,None):
                                        for _ in range(len(T_poss)):
                                            T_poss_poss=T_poss.pop(0)
                                            T_poss.append(T_poss_poss.clone())
                                            T_poss[-1].set_pos((x+dxj,y+dyj),False)
                                    case (None,None):
                                        for _ in range(len(T_poss)):
                                            T_poss_poss=T_poss.pop(0)
                                            T_poss.append(T_poss_poss.clone())
                                            T_poss[-1].set_pos((x+dxi,y+dyi),False)
                                            T_poss.append(T_poss_poss.clone())
                                            T_poss[-1].set_pos((x+dxj,y+dyj),False)
                        case False:
                            for dxi,dyi,dxj,dyj in self.circle:
                                I=(not isinstance(board.get_pos((x+dxi,y+dyi)),clue))and(poss_poss.get_pos((x+dxi,y+dyi)))
                                J=(not isinstance(board.get_pos((x+dxj,y+dyj)),clue))and(poss_poss.get_pos((x+dxj,y+dyj)))
                                match (I,J):
                                    case (False,False):
                                        T_poss=[]
                                        break
                                    case (None,False):
                                        for _ in range(len(T_poss)):
                                            T_poss_poss=T_poss.pop(0)
                                            T_poss.append(T_poss_poss.clone())
                                            T_poss[-1].set_pos((x+dxi,y+dyi),True)
                                    case (False,None):
                                        for _ in range(len(T_poss)):
                                            T_poss_poss=T_poss.pop(0)
                                            T_poss.append(T_poss_poss.clone())
                                            T_poss[-1].set_pos((x+dxj,y+dyj),True)
                                    case (None,None):
                                        for _ in range(len(T_poss)):
                                            T_poss_poss=T_poss.pop(0)
                                            T_poss.append(T_poss_poss.clone())
                                            T_poss[-1].set_pos((x+dxi,y+dyi),True)
                                            T_poss.append(T_poss_poss.clone())
                                            T_poss[-1].set_pos((x+dxj,y+dyj),True)
                    poss+=T_poss
        return poss
    def easy_check(self,board:board_class):
        changed=True
        while changed:
            changed=False
            for pos,value in board():
                if value is True:
                    x,y=pos
                    for dxi,dyi,dxj,dyj in self.circle:
                        if (board.get_pos((x+dxi,y+dyi)) is True and board.get_pos((x+dxj,y+dyj)) is True):
                            return False
                elif value is None:
                    x,y=pos
                    for dxi,dyi,dxj,dyj in self.circle:
                        if ((board.get_pos((x+dxi,y+dyi)) is True and board.get_pos((x+dxj,y+dyj)) is True)or
                            (board.get_pos((x-dxi,y-dyi)) is True and board.get_pos((x-dxj,y-dyj)) is True)or
                            (board.get_pos((x+dxi,y+dyi)) is True and board.get_pos((x-dxi,y-dyi)) is True)):
                            if (board.get_pos(pos) is None)or(board.get_pos(pos) is False):
                                changed=True
                                board.set_pos(pos,False)
                            else:
                                return False
                        if (((board.get_pos((x+dxi,y+dyi)) is False or isinstance(board.get_pos((x+dxi,y+dyi)),clue))and(board.get_pos((x+dxj,y+dyj))is False or isinstance(board.get_pos((x+dxj,y+dyj)),clue)))or
                            ((board.get_pos((x-dxi,y-dyi)) is False or isinstance(board.get_pos((x-dxi,y-dyi)),clue))and(board.get_pos((x-dxj,y-dyj))is False or isinstance(board.get_pos((x-dxj,y-dyj)),clue)))or
                            ((board.get_pos((x+dxi,y+dyi)) is False or isinstance(board.get_pos((x+dxi,y+dyi)),clue))and(board.get_pos((x-dxi,y-dyi))is False or isinstance(board.get_pos((x-dxi,y-dyi)),clue)))):
                            if (board.get_pos(pos) is None)or(board.get_pos(pos) is True):
                                changed=True
                                board.set_pos(pos,True)
                            else:
                                return False
                else:
                    x,y=pos
                    for dxi,dyi,dxj,dyj in self.circle:
                        if ((board.get_pos((x+dxi,y+dyi)) is False or isinstance(board.get_pos((x+dxi,y+dyi)),clue))and(board.get_pos((x+dxj,y+dyj))is False or isinstance(board.get_pos((x+dxj,y+dyj)),clue))):
                            return False
        return True
    def r_check(self,board:board_class)->list[list]:
        changed=True
        while changed:
            changed=False
            for pos,_ in board('N'):
                x,y=pos
                for dxi,dyi,dxj,dyj in self.circle:
                    if ((board.get_pos((x+dxi,y+dyi)) is True and board.get_pos((x+dxj,y+dyj)) is True)or
                        (board.get_pos((x-dxi,y-dyi)) is True and board.get_pos((x-dxj,y-dyj)) is True)or
                        (board.get_pos((x+dxi,y+dyi)) is True and board.get_pos((x-dxi,y-dyi)) is True)):
                        changed=True
                        board.set_pos((x,y),False)
                        break
                    if (((board.get_pos((x+dxi,y+dyi)) is False or isinstance(board.get_pos((x+dxi,y+dyi)),clue))and(board.get_pos((x+dxj,y+dyj))is False or isinstance(board.get_pos((x+dxj,y+dyj)),clue)))or
                        ((board.get_pos((x-dxi,y-dyi)) is False or isinstance(board.get_pos((x-dxi,y-dyi)),clue))and(board.get_pos((x-dxj,y-dyj))is False or isinstance(board.get_pos((x-dxj,y-dyj)),clue)))or
                        ((board.get_pos((x+dxi,y+dyi)) is False or isinstance(board.get_pos((x+dxi,y+dyi)),clue))and(board.get_pos((x-dxi,y-dyi))is False or isinstance(board.get_pos((x-dxi,y-dyi)),clue)))):
                        changed=True
                        board.set_pos(pos,True)
                        break
        return board.board

class rule_2Z(rule):
    def __init__(self,model='@h'):
        self.model=model
    def check(self,board:board_class)->list[board_class]:
        if board.mines_R & 1:
            return [board.clone()]
        poss=[board.clone()]
        if self.model=='@h':
            for y in range(board.Size_H):
                W_Flag=0
                B_Flag=0
                W_Space=[]
                B_Space=[]
                for x in range(board.Size_N):
                    if board.get_pos((x,y)) is True:
                        if board.get_dye((x,y)):
                            W_Flag+=1
                        else:
                            B_Flag+=1
                    elif board.get_pos((x,y)) is None:
                        if board.get_dye((x,y)):
                            W_Space.append(x)
                        else:
                            B_Space.append(x)
                if W_Flag-B_Flag-len(B_Space)>0 or B_Flag-W_Flag-len(W_Space)>0:
                    return []
                else:
                    pem=[]
                    for i in range(len(W_Space)+1):
                        if W_Flag+i-B_Flag<0 or W_Flag+i-B_Flag>len(B_Space):
                            continue
                        pem.append((full_permu(len(W_Space),i),full_permu(len(B_Space),W_Flag+i-B_Flag)))
                for _ in range(len(poss)):
                    Z=poss.pop(0)
                    for Wpem,Bpem in pem:
                        for Wi in Wpem:
                            step_W=Z.clone()
                            for wx in W_Space:
                                if Wi & 1:
                                    step_W.set_pos((wx,y),True)
                                else:
                                    step_W.set_pos((wx,y),False)
                                Wi>>=1
                            for Bi in Bpem:
                                step_B=step_W.clone()
                                for bx in B_Space:
                                    if Bi & 1:
                                        step_B.set_pos((bx,y),True)
                                    else:
                                        step_B.set_pos((bx,y),False)
                                    Bi>>=1
                                poss.append(step_B.clone())
        if self.model=='@v':
            for x in range(board.Size_N):
                W_Flag=0
                B_Flag=0
                W_Space=[]
                B_Space=[]
                for y in range(board.Size_H):
                    if board.get_pos((x,y)) is True:
                        if board.get_dye((x,y)):
                            W_Flag+=1
                        else:
                            B_Flag+=1
                    elif board.get_pos((x,y)) is None:
                        if board.get_dye((x,y)):
                            W_Space.append(y)
                        else:
                            B_Space.append(y)
                if W_Flag-B_Flag-len(B_Space)>0 or B_Flag-W_Flag-len(W_Space)>0:
                    return []
                else:
                    pem=[]
                    for i in range(len(W_Space)+1):
                        if W_Flag+i-B_Flag<0 or W_Flag+i-B_Flag>len(B_Space):
                            continue
                        pem.append((full_permu(len(W_Space),i),full_permu(len(B_Space),W_Flag+i-B_Flag)))
                for _ in range(len(poss)):
                    Z=poss.pop(0)
                    for Wpem,Bpem in pem:
                        for Wi in Wpem:
                            step_W=Z.clone()
                            for wy in W_Space:
                                if Wi & 1:
                                    step_W.set_pos((x,wy),True)
                                else:
                                    step_W.set_pos((x,wy),False)
                                Wi>>=1
                            for Bi in Bpem:
                                step_B=step_W.clone()
                                for by in B_Space:
                                    if Bi & 1:
                                        step_B.set_pos((x,by),True)
                                    else:
                                        step_B.set_pos((x,by),False)
                                    Bi>>=1
                                poss.append(step_B.clone())
        return poss
    def easy_check(self,board:board_class)->bool:
        if board.mines_R & 1:
            return True
        if self.model=='@h':
            for y in range(board.Size_H):
                W_Flag=0
                B_Flag=0
                W_Space=[]
                B_Space=[]
                for x in range(board.Size_N):
                    if board.get_pos((x,y)) is True:
                        if board.get_dye((x,y)):
                            W_Flag+=1
                        else:
                            B_Flag+=1
                    elif board.get_pos((x,y)) is None:
                        if board.get_dye((x,y)):
                            W_Space.append(x)
                        else:
                            B_Space.append(x)
                if W_Flag-B_Flag-len(B_Space)>0 or B_Flag-W_Flag-len(W_Space)>0:
                    return False
                elif W_Flag==B_Flag+len(B_Space):
                    for i in B_Space:
                        board.set_pos((i,y),True)
                    for i in W_Space:
                        board.set_pos((i,y),False)
                elif B_Flag==W_Flag+len(W_Space):
                    for i in W_Space:
                        board.set_pos((i,y),True)
                    for i in B_Space:
                        board.set_pos((i,y),False)
        if self.model=='@v':
            for x in range(board.Size_N):
                W_Flag=0
                B_Flag=0
                W_Space=[]
                B_Space=[]
                for y in range(board.Size_H):
                    if board.get_pos((x,y)) is True:
                        if board.get_dye((x,y)):
                            W_Flag+=1
                        else:
                            B_Flag+=1
                    elif board.get_pos((x,y)) is None:
                        if board.get_dye((x,y)):
                            W_Space.append(y)
                        else:
                            B_Space.append(y)
                if W_Flag-B_Flag-len(B_Space)>0 or B_Flag-W_Flag-len(W_Space)>0:
                    return False
                elif W_Flag==B_Flag+len(B_Space):
                    for i in B_Space:
                        board.set_pos((x,i),True)
                    for i in W_Space:
                        board.set_pos((x,i),False)
                elif B_Flag==W_Flag+len(W_Space):
                    for i in W_Space:
                        board.set_pos((x,i),True)
                    for i in B_Space:
                        board.set_pos((x,i),False)
        return True
    def r_check(self,board:board_class)->list[list]:
        if board.mines_R & 1:
            return board.board
        count=0
        if self.model=='@h':
            for y in range(board.Size_H):
                W_Flag=0
                B_Flag=0
                W_Space=[]
                B_Space=[]
                for x in range(board.Size_N):
                    if board.get_pos((x,y)) is True:
                        if board.get_dye((x,y)):
                            W_Flag+=1
                        else:
                            B_Flag+=1
                    elif board.get_pos((x,y)) is None:
                        if board.get_dye((x,y)):
                            W_Space.append(x)
                        else:
                            B_Space.append(x)
                if W_Flag==B_Flag+len(B_Space):
                    for i in B_Space:
                        board.set_pos((i,y),True)
                    for i in W_Space:
                        board.set_pos((i,y),False)
                elif B_Flag==W_Flag+len(W_Space):
                    for i in W_Space:
                        board.set_pos((i,y),True)
                    for i in B_Space:
                        board.set_pos((i,y),False)
                count+=max(W_Flag,B_Flag)*2
            if count==board.mines_R:
                for y in range(board.Size_H):
                    W_Flag=0
                    B_Flag=0
                    W_Space=[]
                    B_Space=[]
                    for x in range(board.Size_N):
                        if board.get_pos((x,y)) is True:
                            if board.get_dye((x,y)):
                                W_Flag+=1
                            else:
                                B_Flag+=1
                        elif board.get_pos((x,y)) is None:
                            if board.get_dye((x,y)):
                                W_Space.append(x)
                            else:
                                B_Space.append(x)
                    if W_Flag>B_Flag:
                        for i in W_Space:
                            board.set_pos((i,y),False)
                    elif B_Flag>W_Flag:
                        for i in B_Space:
                            board.set_pos((i,y),False)
        if self.model=='@v':
            for x in range(board.Size_N):
                W_Flag=0
                B_Flag=0
                W_Space=[]
                B_Space=[]
                for y in range(board.Size_H):
                    if board.get_pos((x,y)) is True:
                        if board.get_dye((x,y)):
                            W_Flag+=1
                        else:
                            B_Flag+=1
                    elif board.get_pos((x,y)) is None:
                        if board.get_dye((x,y)):
                            W_Space.append(y)
                        else:
                            B_Space.append(y)
                if W_Flag==B_Flag+len(B_Space):
                    for i in B_Space:
                        board.set_pos((x,i),True)
                    for i in W_Space:
                        board.set_pos((x,i),False)
                elif B_Flag==W_Flag+len(W_Space):
                    for i in W_Space:
                        board.set_pos((x,i),True)
                    for i in B_Space:
                        board.set_pos((x,i),False)
                count+=max(W_Flag,B_Flag)*2
            if count==board.mines_R:
                for x in range(board.Size_N):
                    W_Flag=0
                    B_Flag=0
                    W_Space=[]
                    B_Space=[]
                    for y in range(board.Size_H):
                        if board.get_pos((x,y)) is True:
                            if board.get_dye((x,y)):
                                W_Flag+=1
                            else:
                                B_Flag+=1
                        elif board.get_pos((x,y)) is None:
                            if board.get_dye((x,y)):
                                W_Space.append(y)
                            else:
                                B_Space.append(y)
                    if W_Flag>B_Flag:
                        for i in W_Space:
                            board.set_pos((x,i),False)
                    elif B_Flag>W_Flag:
                        for i in B_Space:
                            board.set_pos((x,i),False)
        return board.board

class rule_3T(rule):
    def __init__(self):
        self.circle_old=[(1,0,2,0),(-1,1,-2,2),(0,1,0,2),(1,1,2,2)]
    def circle(self,szN,szH,pos):
        pos_circle=[]
        x,y=pos
        for dx in range(-(x>>1),1):
            for dy in range(1,(szH-y+1)>>1):
                pos_circle.append((dx,dy,dx*2,dy*2))
        for dx in range(1,(szN-x+1)>>1):
            for dy in range((szH-y+1)>>1):
                pos_circle.append((dx,dy,dx*2,dy*2))
        return pos_circle
    def check(self,board:board_class)->list[board_class]:
        poss=[board.clone()]
        for y in range(0,board.Size_H):
            for x in range(0,board.Size_N):
                for _ in range(len(poss)):
                    poss_poss=poss.pop(0)
                    if poss_poss.get_pos((x,y)) is True:
                        T_poss=[poss_poss.clone()]
                        for dxi,dyi,dxj,dyj in self.circle(board.Size_N,board.Size_H,(x,y)):
                            I=poss_poss.get_pos((x+dxi,y+dyi))
                            J=poss_poss.get_pos((x+dxj,y+dyj))
                            if I is True:
                                if J is None:
                                    for _ in range(len(T_poss)):
                                        T_test=T_poss.pop()
                                        T_poss.append(T_test.clone())
                                        T_poss[-1].set_pos((x+dxj,y+dyj),False)
                                elif J is True:
                                    return []
                            elif I is None:
                                if J is True:
                                    for _ in range(len(T_poss)):
                                        T_test=T_poss.pop()
                                        T_poss.append(T_test.clone())
                                        T_poss[-1].set_pos((x+dxi,y+dyi),False)
                                elif J is None:
                                    for _ in range(len(T_poss)):
                                        T_test=T_poss.pop()
                                        T_poss.append(T_test.clone())
                                        T_poss[-1].set_pos((x+dxj,y+dyj),False)
                                        T_poss.append(T_test.clone())
                                        T_poss[-1].set_pos((x+dxi,y+dyi),False)
                        poss+=T_poss
                    elif poss_poss.get_pos((x,y)) is None:
                        T_poss=[poss_poss.clone()]
                        for dxi,dyi,dxj,dyj in self.circle(board.Size_N,board.Size_H,(x,y)):
                            I=poss_poss.get_pos((x+dxi,y+dyi))
                            J=poss_poss.get_pos((x+dxj,y+dyj))
                            if (I is True)and(J is True):
                                poss.append(poss_poss.clone())
                                poss[-1].set_pos((x,y),False)
                                break
                            elif (I is None)and((J is True)or(J is None)):
                                if len(T_poss)==1:
                                    T_poss[-1].set_pos((x,y),False)
                                T_poss.append(poss_poss.clone())
                                T_poss[-1].set_pos((x+dxi,y+dyi),False)
                        else:
                            poss+=T_poss
                    else:
                        poss.append(poss_poss.clone())       
        return poss
    def easy_check(self,board:board_class):
        for pos,value in board('NF'):
                if value is True:
                    x,y=pos
                    for dxi,dyi,dxj,dyj in self.circle(board.Size_N,board.Size_H,pos):
                        if (board.get_pos((x+dxi,y+dyi)) is True and board.get_pos((x+dxj,y+dyj)) is True):
                            return False
                if value is None:
                    x,y=pos
                    for dxi,dyi,dxj,dyj in self.circle(board.Size_N,board.Size_H,pos):
                        if (board.get_pos((x+dxi,y+dyi)) is True and board.get_pos((x+dxj,y+dyj)) is True)or(board.get_pos((x-dxi,y-dyi)) is True and board.get_pos((x-dxj,y-dyj)) is True)or(board.get_pos((x+dxi,y+dyi)) is True and board.get_pos((x-dxi,y-dyi)) is True):
                            board.set_pos(pos,False)
        return True
    def r_check(self,board_Y:board_class)->list[list]:
        for pos,_ in board_Y('N'):
            x,y=pos
            for dxi,dyi,dxj,dyj in self.circle(board_Y.Size_N,board_Y.Size_H,(x,y)):
                if (board_Y.get_pos((x+dxi,y+dyi)) is True and board_Y.get_pos((x+dxj,y+dyj)) is True)or(board_Y.get_pos((x-dxi,y-dyi)) is True and board_Y.get_pos((x-dxj,y-dyj)) is True)or(board_Y.get_pos((x+dxi,y+dyi)) is True and board_Y.get_pos((x-dxi,y-dyi)) is True):
                    board_Y.set_pos((x,y),False)
                    break
        return board_Y.board