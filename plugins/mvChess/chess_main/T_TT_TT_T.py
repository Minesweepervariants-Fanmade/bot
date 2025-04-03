L_true=lambda a:lambda b:a
L_false=lambda a:lambda b:b

L_not=lambda x:x(L_false)(L_true)
L_and=lambda x:lambda y:x(y)(L_false)
L_or=lambda x:lambda y:x(L_true)(y)
L_xor=lambda x:lambda y:x(L_not(y))(y)

L_succ=lambda n:lambda f:lambda x:f(n(f)(x))
L_add=lambda m:lambda n:m(L_succ)(n)
L_mul=lambda m:lambda n:m(n(L_succ))(L_false)
L_pow=lambda m:lambda n:n(m)

Lnum=lambda num:((num>0)and(L_succ(Lnum(num-1))))or((num==0)and(L_false))
Lnum_to_num=lambda lnum:lnum(lambda x:x+1)(0)
print(Lnum_to_num(L_pow(Lnum(2))(Lnum(3))))