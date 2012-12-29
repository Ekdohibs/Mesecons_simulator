import sys
sys_modules = sys.modules

import types
from types import ClassType


def modify_for_nested_pickle(cls, name_prefix, module):
    mod_name = module.__name__
    for (name, v) in cls.__dict__.iteritems():
        if isinstance(v, (type, ClassType)):
            if v.__name__ == name and v.__module__ == mod_name and getattr(module, name, None) is not v:
                # OK, probably this is a nested class.
                dotted_name = name_prefix + '.' + name
                v.__name__ = dotted_name
                setattr(module, dotted_name, v)
                modify_for_nested_pickle(v, dotted_name, module)

def nested_pickle(cls):
    modify_for_nested_pickle(cls, cls.__name__, sys_modules[cls.__module__])
    return cls


class A:
    pass

def rotate_left_n(l,i):
    return l

class Mesecon_thing(object):
    pass

def Inverter(i):
    rin=rotate_left_n([[0,0,1]],i)
    rout=rotate_left_n([[0,0,-1]],i)
    class _Inverter(Mesecon_thing):
        name="Inverter gate"
        #p=[[PhotoImage(file='inverter_side_%s_off.gif'%((i+1)%4)),
        #    PhotoImage(file='inverter_%s_off.gif'%i),
        #    PhotoImage(file='inverter_side_%s_off.gif'%((-i+2)%4))],
        #   [PhotoImage(file='inverter_side_%s_on.gif'%((i+1)%4)),
        #    PhotoImage(file='inverter_%s_on.gif'%i),
        #    PhotoImage(file='inverter_side_%s_on.gif'%((-i+2)%4))]]
        def __init__(self,boss,x,y,z):
            #Mesecon_thing.__init__(self,rin,rout)
            pass

        def image(self,d):
            return self.p[self.ostates[0]][d]

        @classmethod
        def imagedraw(cls):
            return cls.p[0][1]

        def update_outputs(self):
            self.set_output(0,not self.istates[0])
    return _Inverter

def t(i):
    l=[0,1,2,5][i]
    class B:
        z=i
    return B

def test(cl):
    l=[]
    for i in range(4):
        C=cl(i)
        l.append(C)
        setattr(A,C.__name__+str(i),C)
        C.__name__='A.'+C.__name__+str(i)
    return l[0]

c=test(Inverter)
print dir(c)
#print c.__reduce_ex__.__doc__

#print A.__name__
#print A.B0.__name__
import pickle
z=c(0,0,0,0)
y=pickle.dumps(z)
print str(y)
