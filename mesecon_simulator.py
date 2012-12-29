from Tkinter import *
import os
import pickle
import tkFileDialog as tkfd
import sys
modules=sys.modules

TOPDIR=os.getcwd()
os.chdir('resources')

class GridCanvas(Canvas):
    def __init__(self,boss,width,height,csize,onclic):
        wd=(csize+1)*width-1
        he=(csize+1)*height-1
        Canvas.__init__(self,boss,bg='white',scrollregion=(0,0,wd,he))#,width=wd,height=he)
        self.width=width
        self.height=height
        self.csize=csize
        self.onclic=onclic
        self.bind("<Button-1>",self.clc)

    def dims(self,width,height):
        self.width=width
        self.height=height
        wd=(self.csize+1)*width-1
        he=(self.csize+1)*height-1
        self.configure(scrollregion=(0,0,wd,he))

    def clc(self,event):
        x,y=int(self.canvasx(event.x)),int(self.canvasy(event.y))
        self.onclic(x//(self.csize+1),y//(self.csize+1))

    def draw(self,l,d):
        self.delete(ALL)
        c=self.csize+1
        w=self.width
        h=self.height
        for i in range(len(l)):
            m=l[i]
            if i>=w:
                break
            for j in range(len(m)):
                if j>=h:
                    break
                p=m[j]
                if p!=None:
                    im=p.image(d)
                    self.create_image(i*c+1,j*c+1,image=im,anchor=NW)
        for i in range(w+1):
            self.create_line(i*c,0,i*c,h*c,fill='black')
        for j in range(h+1):
            self.create_line(0,j*c,w*c,j*c,fill='black')


def getclassname(i):
    if hasattr(i,"name"):
        return i.name
    md=i.__module__
    return str(i.__class__)[len(md)+1:]

class Mesecon_conductor(object):
    def __init__(self,connect):
        self.connect=connect
        self.t='conductor'
        self.state=0
        self.connections=[]
        self.group=None

    def get_group(self):
        return self.group


class Mesecon_thing(object):
    def __init__(self,inputs,outputs):
        self.inputs=inputs
        self.outputs=outputs
        self.connections=[[] for i in range(len(outputs))]
        self.ostates=[0]*len(outputs)
        self.istates=[0]*len(inputs)
        self.t='thing'
        self.groups_i=[None]*len(inputs)
        self.groups_o=[None]*len(outputs)

    def get_group_i(self,n):
        return self.groups_i[n]

    def get_group_o(self,n):
        return self.groups_o[n]

    def get_group_r(self,r):
        if r in self.inputs:
            return self.get_group_i(self.inputs.index(r))
        if r in self.outputs:
            return self.get_group_o(self.outputs.index(r))
        return None

    def sig_change(self,inumber,st):
        self.istates[inumber]=st
        self.update_outputs()

    def update_outputs(self):
        pass

    def set_output(self,onum,st):
        if st!=self.ostates[onum]:
            self.ostates[onum]=st
            for reg in self.connections[onum]:
                reg.chst(st)

    def on(self,onumber):
        return self.ostates[onumber]

    def register_connected(self,reg,onumber):
        self.connections[onumber].append(reg)

    def unregister_connected(self,reg,onumber):
        if reg not in self.connections[onumber]:
            return
        self.connections[onumber].remove(reg)

class Mesecons_group(object):
    def __init__(self):
        self.connected=set()
        self.inputs=set()
        self.outputs=set()
        self.psources=0

    def add_conductor(self,c):
        if c not in self.connected:
            self.connected.add(c)
            c.group=self
            return True
        return False

    def add_input(self,i,inumber):
        if (i,inumber) not in self.inputs:
            self.inputs.add((i,inumber))
            i.register_connected(self,inumber)
            i.groups_o[inumber]=self
            if i.on(inumber):
                self.psources+=1
            return True
        return False

    def remove_input(self,i,inumber):
        if (i,inumber) in self.inputs:
            self.inputs.discard((i,inumber))
            i.unregister_connected(self,inumber)
            i.groups_o[inumber]=None
            if i.on(inumber):
                self.psources-=1
                self.update_outputs(self.psources>=1)
                    
    def remove_output(self,o,onumber):
        if (o,onumber) in self.outputs:
            self.outputs.discard((o,onumber))
            o.groups_i[onumber]=None

    def add_output(self,o,onumber):
        if (o,onumber) not in self.outputs:
            self.outputs.add((o,onumber))
            o.groups_i[onumber]=self
            return True
        return False

    def update_outputs(self,st):
        for c in self.connected:
            c.state=st
        for (o,onumber) in self.outputs:
            o.sig_change(onumber,st)

    def chst(self,st):
        ost=(self.psources>=1)
        if st==1:
            self.psources+=1
        else:
            self.psources-=1
        nst=(self.psources>=1)
        if ost!=nst:
            self.update_outputs(nst)

    def has_conductor(self,c):
        return (c in self.connected)

    def has_input(self,i,inum):
        return ((i,inum) in self.inputs)

    def has_output(self,o,onum):
        return ((o,onum) in self.outputs)

    def unreg(self):
        for (i,inum) in self.inputs:
            i.unregister_connected(self,inum)

    def merge(self,other):
        if other is self:
            return
        for (i,inum) in other.inputs:
            i.unregister_connected(other,inum)
            self.add_input(i,inum)
        #self.psources+=other.psources
        self.outputs.update(other.outputs)
        for (o,onum) in other.outputs:
            o.groups_i[onum]=self
        self.connected.update(other.connected)
        for c in other.connected:
            c.group=self
        st=(self.psources>=1)
        self.update_outputs(st)

def iscinl(c,l):
    for i in l:
        if i.has_conductor(c):
            return True
    return False

def isiinl(i,inum,l):
    for k in l:
        if k.has_input(i,inum):
            return True
    return False

def isoinl(o,onum,l):
    for k in l:
        if k.has_output(o,onum):
            return True
    return False

def group_mesecons(l):
    mg=[]
    for z in enum(l):
        if z:
            if z.t=='conductor':
                z.state=0
                z.connections=[]
            elif z.t=="thing":
                z.connections=[[] for i in range(len(z.outputs))]
                z.ostates=[0]*len(z.outputs)
                z.istates=[0]*len(z.inputs)
    for x in range(len(l)):
        m=l[x]
        for y in range(len(m)):
            n=m[y]
            for z in range(len(n)):
                p=n[z]
                if p:
                    if p.t=='conductor':
                        if iscinl(p,mg):
                            continue
                        gr=Mesecons_group()
                        gr.add_conductor(p)
                        mg.append(gr)
                        group_expand(gr,l,x,y,z,p.connect,p.connections)
                    elif p.t=='thing':
                        for inum in range(len(p.outputs)):
                            i=p.outputs[inum]
                            if isiinl(p,inum,mg):
                                continue
                            gr=Mesecons_group()
                            gr.add_input(p,inum)
                            mg.append(gr)
                            group_expand(gr,l,x,y,z,[i])
                        for onum in range(len(p.inputs)):
                            o=p.inputs[onum]
                            if isoinl(p,onum,mg):
                                continue
                            gr=Mesecons_group()
                            gr.add_output(p,onum)
                            mg.append(gr)
                            group_expand(gr,l,x,y,z,[o])
    return mg

def group_expand(gr,l,x,y,z,rls,toadd=[]):
    for r in rls:
        nx,ny,nz=x+r[0],y+r[1],z+r[2]
        if nx<0 or ny<0 or nz<0:
            continue
        try:
            p=l[nx][ny][nz]
        except IndexError:
            continue
        tf=[-r[0],-r[1],-r[2]]
        if p:
            if p.t=='conductor':
                if tf in p.connect:
                    if tf not in p.connections:
                        p.connections.append(tf)
                    if r not in toadd:
                        toadd.append(r)
                    if gr.add_conductor(p):
                        group_expand(gr,l,nx,ny,nz,p.connect,p.connections)
            if p.t=='thing':
                for inum in range(len(p.outputs)):
                    i=p.outputs[inum]
                    if tf == i:
                        if r not in toadd:
                            toadd.append(r)
                        gr.add_input(p,inum)
                for onum in range(len(p.inputs)):
                    o=p.inputs[onum]
                    if tf == o:
                        if r not in toadd:
                            toadd.append(r)
                        gr.add_output(p,onum)

def actpos(l,x,y,z,rls,toadd=[]):
    for r in rls:
        nx,ny,nz=x+r[0],y+r[1],z+r[2]
        if nx<0 or ny<0 or nz<0:
            continue
        try:
            p=l[nx][ny][nz]
        except IndexError:
            continue
        tf=[-r[0],-r[1],-r[2]]
        if p:
            if p.t=='conductor':
                if tf in p.connect:
                    if tf not in p.connections:
                        p.connections.append(tf)
                    if r not in toadd:
                        toadd.append(r)
            if p.t=='thing':
                for inum in range(len(p.outputs)):
                    i=p.outputs[inum]
                    if tf == i:
                        if r not in toadd:
                            toadd.append(r)
                for onum in range(len(p.inputs)):
                    o=p.inputs[onum]
                    if tf == o:
                        if r not in toadd:
                            toadd.append(r)

def rempos(l,x,y,z,rls,toadd):
    for r in rls:
        nx,ny,nz=x+r[0],y+r[1],z+r[2]
        if nx<0 or ny<0 or nz<0:
            continue
        try:
            p=l[nx][ny][nz]
        except IndexError:
            continue
        tf=[-r[0],-r[1],-r[2]]
        if p:
            if p.t=='conductor':
                if tf in p.connections:
                    p.connections.remove(tf)
                    if r not in toadd:
                        toadd.append(r)
            elif p.t=='thing':
                if tf in p.inputs+p.outputs:
                    if r not in toadd:
                        toadd.append(r)

def rules(x):
    if x.t=='conductor':
        return x.connect
    elif x.t=='thing':
        return x.inputs+x.outputs
    else:
        return []

def enum(l):
    for i in l:
        for j in i:
            for k in j:
                yield k

def update_group(l,x,y,z,r,g,gin=[]):
    nx,ny,nz=x+r[0],y+r[1],z+r[2]
    o=l[nx][ny][nz]
    if o.t=="conductor":
        og=o.get_group()
        if og not in gin:
            g.merge(og)
            gin.append(og)
    elif o.t=='thing':
        nr=[-r[0],-r[1],-r[2]]
        og=o.get_group_r(nr)
        if og not in gin:
            g.merge(og)
            gin.append(og)

def rotate_rule(rule):
    return [rule[2], rule[1], -rule[0]]

def rotate_left(rules):
    return [rotate_rule(rule) for rule in rules]

def rotate_left_n(rules,n):
    for i in range(n):
        rules=rotate_left(rules)
    return rules

"""class Test1(Mesecon_conductor):
    def __init__(self):
        Mesecon_conductor.__init__(self,[[0,0,1],[0,0,-1],[0,1,0],[0,-1,0]])

class Test2(Mesecon_thing):
    def __init__(self):
        Mesecon_thing.__init__(self,[[[0,0,-1]]],[[[0,1,0]]])

    def update_outputs(self):
        self.set_output(0,1-self.istates[0])


tbl=[[[Test1(),Test1(),Test2()],[None,None,Test1()],[None,None,Test1()]]]
mg=group_mesecons(tbl)
mg[0].update_outputs(0)
print mg
print mg[1].psources
print tbl[0][0][2].connections
"""        
class Application:
    def __init__(self,maxc=10):
        self.tk=Tk()
        self.tk.title("Mesecons simulator")
        self.used=0
        self.btsframe=Frame(self.tk)
        self.btsframe.grid(row=0,column=0,columnspan=2,sticky=W)
        self.levlbl=Label(self.tk, text="Plane: XZ, Y-Level: 0")
        self.levlbl.grid(row=1,column=0,columnspan=2,sticky=W)
        self.can=GridCanvas(self.tk,maxc,maxc,30,self.clic)
        self.can.grid(row=2,column=0,sticky=NSEW)
        self.xsc=Scrollbar(self.tk,command=self.can.xview, orient=HORIZONTAL)
        self.xsc.grid(row=3,column=0,sticky=EW)
        self.can.configure(xscrollcommand=self.xsc.set)
        self.ysc=Scrollbar(self.tk,command=self.can.yview, orient=VERTICAL)
        self.ysc.grid(row=2,column=1,sticky=NS)
        self.can.configure(yscrollcommand=self.ysc.set)
        self.tk.grid_rowconfigure(2,weight=1)
        self.tk.grid_columnconfigure(0,weight=1)
        self.l=[[[None]*maxc for i in range(maxc)] for i in range(maxc)]
        self.maxcoords=(maxc,maxc,maxc)
        self.curplane=(1,0) #plane (x,z) at y level 0
        self.can.draw(self.l[0],0)
        self.tk.bind("<Key-0x003c>",self.levup)
        self.tk.bind("<Key-0x003e>",self.levdown)
        self.tk.bind("<r>",self.rotate)
        self.tk.bind("<Control-o>",self.open_command)
        self.tk.bind("<Control-s>",self.save_command)

    def rotate(self,evnt):
        d=(self.curplane[0]+1)%3
        l=min(self.maxcoords[d],self.curplane[1])
        self.curplane=(d,l)
        self.uplbl()
        self.draw()

    def levup(self,evnt):
        self.curplane=(self.curplane[0],min(self.maxcoords[self.curplane[0]]-1,self.curplane[1]+1))
        self.uplbl()
        self.draw()

    def levdown(self,evnt):
        self.curplane=(self.curplane[0],max(0,self.curplane[1]-1))
        self.uplbl()
        self.draw()

    def uplbl(self):
        d,l=self.curplane
        if d==0:
            t="Plane: YZ, X-Level: "
        elif d==1:
            t="Plane: XZ, Y-Level: "
        else:
            t="Plane: XY, Z-Level: "
        t+=str(l)
        self.levlbl.configure(text=t)

    def persistent_id(self,obj):
        if obj is self:
            return 'self'
        return None

    def persistent_load(self,id):
        return self

    def save(self,fname):
        f=open(fname,'w')
        p=pickle.Pickler(f)
        p.persistent_id=self.persistent_id
        p.dump(self.l)
        f.close()

    def open_(self,fname):
        f=open(fname,'r')
        p=pickle.Unpickler(f)
        p.persistent_load=self.persistent_load
        self.l=p.load()
        f.close()
        self.draw()

    def open_command(self,event=None):
        op=tkfd.Open(self.tk).show()
        if op:
            self.open_(op)

    def save_command(self,event=None):
        sa=tkfd.SaveAs(self.tk).show()
        if sa:
            self.save(sa)
        

    def mainloop(self):
        self.tk.mainloop()

    def get_real_coords(self,x,y):
        d=self.curplane[0]
        level=self.curplane[1]
        if d==0:
            return level,self.maxcoords[1]-y-1,x
        elif d==1:
            return x,level,y
        else:
            return x,self.maxcoords[1]-y-1,level

    def chpos(self,x,y,z,new):
        a=self.l[x][y][z]
        if a:
            l=[]
            rempos(self.l,x,y,z,rules(a),l)
            self.l[x][y][z]=None
            if a.t=='thing':
                for i in range(len(a.inputs)):
                    g=a.get_group_i(i)
                    g.remove_output(a,i)
                for o in range(len(a.outputs)):
                    g=a.get_group_o(o)
                    g.remove_input(a,o)
            elif a.t=="conductor":
                g=a.get_group()
                g.unreg()
                gs=[]
                for r in l:
                    nx,ny,nz=x+r[0],y+r[1],z+r[2]
                    nr=[-r[0],-r[1],-r[2]]
                    np=self.l[nx][ny][nz]
                    g=Mesecons_group()
                    gs.append(g)
                    if np.t=='conductor':
                        g.add_conductor(np)
                        group_expand(g,self.l,nx,ny,nz,np.connect)
                    elif np.t=='thing':
                        if nr in np.inputs:
                            i=np.inputs.index(nr)
                            g.add_output(np,i)
                        elif nr in np.outputs:
                            i=np.outputs.index(nr)
                            g.add_input(np,i)
                    for g in gs:
                        g.update_outputs(g.psources>=1)
            del a

        self.l[x][y][z]=new
        if new!=None:
            if new.t=="conductor":
                l=[]
                actpos(self.l,x,y,z,new.connect,l)
                g=Mesecons_group()
                g.add_conductor(new)
                new.connections=l
                gin=[]
                for r in l:
                    update_group(self.l,x,y,z,r,g,gin)
            elif new.t=="thing":
                l=[]
                actpos(self.l,x,y,z,new.inputs+new.outputs,l)
                igs=[Mesecons_group() for i in range(len(new.inputs))]
                ogs=[Mesecons_group() for i in range(len(new.outputs))]
                for i in range(len(new.inputs)):
                    igs[i].add_output(new,i)
                    g=igs[i]
                    r=new.inputs[i]
                    if r in l:
                        update_group(self.l,x,y,z,r,g)
                        if g.psources>=1:
                            new.istates[i]=1
                        else:
                            new.istates[i]=0
                for i in range(len(new.outputs)):
                    ogs[i].add_input(new,i)
                    g=ogs[i]
                    r=new.outputs[i]
                    if r in l:
                        update_group(self.l,x,y,z,r,g)
                new.update_outputs()

    def addcells(self):
        w=Toplevel(self.tk)
        self.w=w
        w.title("Add cells")
        l=[]
        t=Label(w,text="Add cells:")
        t.grid(row=0,column=0,columnspan=3,sticky=W)
        for (i,d) in enumerate(("X","Y","Z")):
            txt1=Label(w,text="%s-axis: Before:"%d)
            txt1.grid(row=2*i+1,column=0,sticky=E)
            txt2=Label(w,text="After:")
            txt2.grid(row=2*i+2,column=0,sticky=E)
            sp1=Spinbox(w,from_=0,to=1000)
            sp1.grid(row=2*i+1,column=1,columnspan=2)
            sp2=Spinbox(w,from_=0,to=1000)
            sp2.grid(row=2*i+2,column=1,columnspan=2)
            l.append((sp1,sp2))
        self.sps=l
        bt=Button(w,text='OK',command=self.addok)
        bt.grid(row=7,column=2,sticky=E)
        btc=Button(w,text='Cancel',command=w.destroy)
        btc.grid(row=7,column=0,sticky=W)
        w.bind("<Button-1>",self.addclic)

    def addclic(self,ev):
        def update_spin(x):
            v=x.get()
            s=""
            for k in v:
                if k in "0123456789":
                    s+=k
            x.delete(0,END)
            x.insert(0,s)
        for sp1,sp2 in self.sps:
            update_spin(sp1)
            update_spin(sp2)

    def addok(self):
        def toint(i):
            s=""
            for k in i:
                if k in "0123456789":
                    s+=k
            return int(s)
        l=[]
        for sp1,sp2 in self.sps:
            l.append((toint(sp1.get()),toint(sp2.get())))
        self.l=[[[None]*self.maxcoords[2]
                 for j in range(self.maxcoords[1])]
                for i in range(l[0][0])]+\
                self.l+\
                [[[None]*self.maxcoords[2]
                  for j in range(self.maxcoords[1])]
                 for i in range(l[0][1])]
        mx0=self.maxcoords[0]+l[0][0]+l[0][1]
        self.l=[[[None]*self.maxcoords[2] for j in range(l[1][0])]+
                i+
                [[None]*self.maxcoords[2] for j in range(l[1][1])]
                for i in self.l]
        mx1=self.maxcoords[1]+l[1][0]+l[1][1]
        self.l=[[[None]*l[2][0]+
                 j+[None]*l[2][1] for j in i]
                for i in self.l]
        mx2=self.maxcoords[2]+l[2][0]+l[2][1]
        self.maxcoords=mx0,mx1,mx2
        self.w.destroy()
        for i in enum(self.l):
            if hasattr(i,'update_pos'):
                i.update_pos(l[0][0],l[1][0],l[2][0])
        self.draw()

    def stats(self):
        dic={}
        for i in enum(self.l):
            if i!=None:
                name=getclassname(i)
                d=dic.get(name,0)+1
                dic[name]=d
        w=Toplevel(self.tk)
        w.title("Statistics")
        txt="\n - ".join(["%s:%s"%i for i in dic.items()])
        if txt=="":
            txt="Nothing"
        lbl=Label(w,text="Your machine uses:\n - "+txt,justify=LEFT)
        lbl.pack()
        Button(w,text="OK",command=w.destroy).pack()
        
    def set_buttons(self,*b):
        a=Button(self.btsframe,bg='white',image=ADDCELLS,command=self.addcells)
        a.pack(side=LEFT)
        a=Button(self.btsframe,bg='white',image=STATS,command=self.stats)
        a.pack(side=LEFT)
        b=[None,None,None]+list(b)
        self.bts=[]
        self.nodes=b
        for i in range(len(b)):
            if i==0:
                a=Button(self.btsframe,bg='white',image=POINTER,command=lambda i=i:self.set_used(i),relief=SUNKEN)
            elif i==2:
                a=Button(self.btsframe,bg='white',image=ERASER,command=lambda i=i:self.set_used(i))
            elif i==1:
                a=Button(self.btsframe,bg='white',image=ROTATE,command=lambda i=i:self.set_used(i))
            else:
                a=Button(self.btsframe,bg='white',image=b[i].imagedraw(),command=lambda i=i:self.set_used(i))
            self.bts.append(a)
            a.pack(side=LEFT)

    def set_used(self,i):
        self.bts[self.used].configure(relief=RAISED)
        self.used=i
        self.bts[i].configure(relief=SUNKEN)
        
    def clic(self,x,y):
        try:
            x,y,z=self.get_real_coords(x,y)
            if x>=self.maxcoords[0] or y>=self.maxcoords[1] or z>=self.maxcoords[2]:
                return
            if self.used>1:
                cl=self.nodes[self.used]
                if self.l[x][y][z] and self.l[x][y][z].t=="unremovable":
                    return
                if hasattr(self.l[x][y][z],"onremove"):
                    self.l[x][y][z].onremove()
                if cl==None:
                    self.chpos(x,y,z,None)
                else:
                    self.chpos(x,y,z,cl(self,x,y,z))
            elif self.used==0:
                p=self.l[x][y][z]
                if hasattr(p,'action'):
                        p.action()
            else:
                p=self.l[x][y][z]
                if hasattr(p,'rotate'):
                    self.chpos(x,y,z,p.rotate(self,x,y,z))
            self.draw()
        except RuntimeError:
            print "Warning : will cause stack overflow"

    def getplane(self,plane):
        level=plane[1]
        d=plane[0]
        if d==0:
            return [[j[k] for j in reversed(self.l[level])] for k in range(len(self.l[0][0]))]
        elif d==1:
            return [i[level] for i in self.l]
        else:
            return [[j[level] for j in reversed(i)] for i in self.l]

    def canreconf(self):
        d=self.curplane[0]
        if d==0:
            x,y=self.maxcoords[2],self.maxcoords[1]
        elif d==1:
            x,y=self.maxcoords[0],self.maxcoords[2]
        else:
            x,y=self.maxcoords[0],self.maxcoords[1]
        self.can.dims(x,y)

    def draw(self):
        m=self.getplane(self.curplane)
        self.canreconf()
        self.can.draw(m,self.curplane[0])        

a=Application(20)

ADDCELLS=PhotoImage(file='addcells.gif')
STATS=PhotoImage(file='stats.gif')
ERASER=PhotoImage(file='eraser.gif')
POINTER=PhotoImage(file='pointer.gif')
ROTATE=PhotoImage(file='rotate.gif')

default_rules=[[0,0,1],[0,0,-1],[1,0,0],[-1,0,0],[0,-1,1],[0,-1,-1],
               [1,-1,0],[-1,-1,0],[0,1,1],[0,1,-1],[1,1,0],[-1,1,0]]


class Normal_block(object):
    p=PhotoImage(file="normal.gif")
    t="normal"
    name="Normal block"
    def __init__(self,boss,x,y,z):
        pass

    def image(self,d):
        return self.p
    
    @classmethod
    def imagedraw(cls):
        return cls.p


class Mesecon(Mesecon_conductor):
    #p=[PhotoImage(file='moff.gif'),PhotoImage(file='mon.gif')]
    p=[[PhotoImage(file='moff'+str(i)+'.gif') for i in range(24)],
       [PhotoImage(file='mon'+str(i)+'.gif') for i in range(24)]]
    name="Mesecon"
    def __init__(self,boss,x,y,z):
        Mesecon_conductor.__init__(self,default_rules)

    def image(self,d):
        if d==1: #Y-plane
            k=-1
            if [0,0,1] in self.connections or [0,-1,1] in self.connections or [0,1,1] in self.connections:
                k+=1
            if [0,0,-1] in self.connections or [0,-1,-1] in self.connections or [0,1,-1] in self.connections:
                k+=2
            if [1,0,0] in self.connections or [1,-1,0] in self.connections or [1,1,0] in self.connections:
                k+=4
            if [-1,0,0] in self.connections or [-1,-1,0] in self.connections or [-1,1,0] in self.connections:
                k+=8
            if k==-1:
                k=14
        elif d==0:
            k=15
            if [0,1,1] in self.connections:
                k+=6
            elif [0,0,1] in self.connections or [0,-1,1] in self.connections:
                k+=3
            if [0,1,-1] in self.connections:
                k+=2
            elif [0,0,-1] in self.connections or [0,-1,-1] in self.connections:
                k+=1
        elif d==2:
            k=15
            if [1,1,0] in self.connections:
                k+=6
            elif [1,0,0] in self.connections or [1,-1,0] in self.connections:
                k+=3
            if [-1,1,0] in self.connections:
                k+=2
            elif [-1,0,0] in self.connections or [-1,-1,0] in self.connections:
                k+=1
        return self.p[self.state][k]

    @classmethod
    def imagedraw(cls):
        return cls.p[0][14]

class Switch(Mesecon_thing):
    name="Switch"
    p=[PhotoImage(file='switch_off.gif'),PhotoImage(file='switch_on.gif')]
    def __init__(self,boss,x,y,z):
        Mesecon_thing.__init__(self,[],default_rules)

    def image(self,d):
        return self.p[self.ostates[0]]

    @classmethod
    def imagedraw(cls):
        return cls.p[0]

    def action(self):
        st=1-self.ostates[0]
        for i in range(len(self.ostates)):
            self.set_output(i,st)

class RedLightStone(Mesecon_thing):
    name="Red Lightstone"
    p=[PhotoImage(file='red_lightstone_off.gif'),
       PhotoImage(file='red_lightstone_on.gif')]
    def __init__(self,boss,x,y,z):
        Mesecon_thing.__init__(self,default_rules,[])
        self.st=0

    def image(self,d):
        return self.p[self.st]

    @classmethod
    def imagedraw(cls):
        return cls.p[0]

    def update_outputs(self):
        self.st=(sum(self.istates)>=1)
            
class ClassContainer:
    pass

def rotated(t,mx):
    l=[]
    for i in range(mx):
        th=t(i)
        l.append(th)
        setattr(ClassContainer,th.__name__+str(i),th)
        setattr(modules["__main__"],"ClassContainer."+th.__name__+str(i),th)
        th.__name__="ClassContainer."+th.__name__+str(i)
    for i in range(mx):
        l[i].rotate=l[(i+1)%mx]
    return l[0]

def Inverter(i):
    rin=rotate_left_n([[0,0,1]],i)
    rout=rotate_left_n([[0,0,-1]],i)
    class _Inverter(Mesecon_thing):
        name="Inverter gate"
        p=[[PhotoImage(file='inverter_side_%s_off.gif'%((i+1)%4)),
            PhotoImage(file='inverter_%s_off.gif'%i),
            PhotoImage(file='inverter_side_%s_off.gif'%((-i+2)%4))],
           [PhotoImage(file='inverter_side_%s_on.gif'%((i+1)%4)),
            PhotoImage(file='inverter_%s_on.gif'%i),
            PhotoImage(file='inverter_side_%s_on.gif'%((-i+2)%4))]]
        def __init__(self,boss,x,y,z):
            Mesecon_thing.__init__(self,rin,rout)

        def image(self,d):
            return self.p[self.ostates[0]][d]

        @classmethod
        def imagedraw(cls):
            return cls.p[0][1]

        def update_outputs(self):
            self.set_output(0,not self.istates[0])
    return _Inverter

def Diode(i):
    rin=rotate_left_n([[0,0,1]],i)
    rout=rotate_left_n([[0,0,-1]],i)
    class _Diode(Mesecon_thing):
        name="Diode gate"
        p=[[PhotoImage(file='diode_side_%s_off.gif'%((i+1)%4)),
            PhotoImage(file='diode_%s_off.gif'%i),
            PhotoImage(file='diode_side_%s_off.gif'%((-i+2)%4))],
           [PhotoImage(file='diode_side_%s_on.gif'%((i+1)%4)),
            PhotoImage(file='diode_%s_on.gif'%i),
            PhotoImage(file='diode_side_%s_on.gif'%((-i+2)%4))]]
        def __init__(self,boss,x,y,z):
            Mesecon_thing.__init__(self,rin,rout)

        def image(self,d):
            return self.p[self.ostates[0]][d]

        @classmethod
        def imagedraw(cls):
            return cls.p[0][1]

        def update_outputs(self):
            self.set_output(0,self.istates[0])
    return _Diode

def And(i):
    rin=rotate_left_n([[1,0,0],[-1,0,0]],i)
    rout=rotate_left_n([[0,0,-1]],i)
    class _And(Mesecon_thing):
        name="And gate"
        p=[[PhotoImage(file='and_side_%s_off.gif'%((i+1)%4)),
            PhotoImage(file='and_%s_off.gif'%i),
            PhotoImage(file='and_side_%s_off.gif'%((-i+2)%4))],
           [PhotoImage(file='and_side_%s_on.gif'%((i+1)%4)),
            PhotoImage(file='and_%s_on.gif'%i),
            PhotoImage(file='and_side_%s_on.gif'%((-i+2)%4))]]
        def __init__(self,boss,x,y,z):
            Mesecon_thing.__init__(self,rin,rout)

        def image(self,d):
            return self.p[self.ostates[0]][d]

        @classmethod
        def imagedraw(cls):
            return cls.p[0][1]

        def update_outputs(self):
            self.set_output(0,self.istates[0] and self.istates[1])
    return _And

def Nand(i):
    rin=rotate_left_n([[1,0,0],[-1,0,0]],i)
    rout=rotate_left_n([[0,0,-1]],i)
    class _Nand(Mesecon_thing):
        name="Nand gate"
        p=[[PhotoImage(file='nand_side_%s_off.gif'%((i+1)%4)),
            PhotoImage(file='nand_%s_off.gif'%i),
            PhotoImage(file='nand_side_%s_off.gif'%((-i+2)%4))],
           [PhotoImage(file='nand_side_%s_on.gif'%((i+1)%4)),
            PhotoImage(file='nand_%s_on.gif'%i),
            PhotoImage(file='nand_side_%s_on.gif'%((-i+2)%4))]]
        def __init__(self,boss,x,y,z):
            Mesecon_thing.__init__(self,rin,rout)

        def image(self,d):
            return self.p[self.ostates[0]][d]

        @classmethod
        def imagedraw(cls):
            return cls.p[0][1]

        def update_outputs(self):
            self.set_output(0,not(self.istates[0] and self.istates[1]))
    return _Nand

def Xor(i):
    rin=rotate_left_n([[1,0,0],[-1,0,0]],i)
    rout=rotate_left_n([[0,0,-1]],i)
    class _Xor(Mesecon_thing):
        name="Xor gate"
        p=[[PhotoImage(file='xor_side_%s_off.gif'%((i+1)%4)),
            PhotoImage(file='xor_%s_off.gif'%i),
            PhotoImage(file='xor_side_%s_off.gif'%((-i+2)%4))],
           [PhotoImage(file='xor_side_%s_on.gif'%((i+1)%4)),
            PhotoImage(file='xor_%s_on.gif'%i),
            PhotoImage(file='xor_side_%s_on.gif'%((-i+2)%4))]]
        def __init__(self,boss,x,y,z):
            Mesecon_thing.__init__(self,rin,rout)

        def image(self,d):
            return self.p[self.ostates[0]][d]

        @classmethod
        def imagedraw(cls):
            return cls.p[0][1]

        def update_outputs(self):
            self.set_output(0,self.istates[0]^self.istates[1])
    return _Xor

def Insulated(i):
    rs=rotate_left_n([[1,0,0],[-1,0,0]],i)
    class _Insulated(Mesecon_conductor):
        name="Insulated wire"
        p=[[PhotoImage(file='insulated_side_%s_off.gif'%((i+1)%2)),
            PhotoImage(file='insulated_%s.gif'%i),
            PhotoImage(file='insulated_side_%s_off.gif'%i)],
           [PhotoImage(file='insulated_side_%s_on.gif'%((i+1)%2)),
            PhotoImage(file='insulated_%s.gif'%i),
            PhotoImage(file='insulated_side_%s_on.gif'%i)]]
        def __init__(self,boss,x,y,z):
            Mesecon_conductor.__init__(self,rs)

        def image(self,d):
            return self.p[self.state][d]

        @classmethod
        def imagedraw(cls):
            return cls.p[0][1]
    return _Insulated

def Insulated_t(i):
    rs=rotate_left_n([[1,0,0],[-1,0,0],[0,0,1]],i)
    class _Insulated_t(Mesecon_conductor):
        name="Insulated T-junction"
        p=[[PhotoImage(file='insulated_t_side_%s_off.gif'%((i+1)%4)),
            PhotoImage(file='insulated_t_%s.gif'%i),
            PhotoImage(file='insulated_t_side_%s_off.gif'%((-i+2)%4))],
           [PhotoImage(file='insulated_t_side_%s_on.gif'%((i+1)%4)),
            PhotoImage(file='insulated_t_%s.gif'%i),
            PhotoImage(file='insulated_t_side_%s_on.gif'%((-i+2)%4))]]
        def __init__(self,boss,x,y,z):
            Mesecon_conductor.__init__(self,rs)

        def image(self,d):
            return self.p[self.state][d]

        @classmethod
        def imagedraw(cls):
            return cls.p[0][1]
    return _Insulated_t

def Piston_all(rs,plst):
    class _Piston(Mesecon_thing):
        name="Piston"
        p=[[PhotoImage(file='piston_%s_off.gif'%plst[0]),
            PhotoImage(file='piston_%s_off.gif'%plst[1]),
            PhotoImage(file='piston_%s_off.gif'%plst[2])],
           [PhotoImage(file='piston_%s_on.gif'%plst[0]),
            PhotoImage(file='piston_%s_on.gif'%plst[1]),
            PhotoImage(file='piston_%s_on.gif'%plst[2])]]
        def __init__(self,boss,x,y,z):
            Mesecon_thing.__init__(self,default_rules,[])
            self.x,self.y,self.z,self.boss=x,y,z,boss
            self.st=False
            self.unpushable=False

        def update_pos(self,xadd,yadd,zadd):
            self.x+=xadd
            self.y+=yadd
            self.z+=zadd

        def image(self,d):
            return self.p[self.st][d]

        @classmethod
        def imagedraw(cls):
            return cls.p[0][1]

        def update_outputs(self):
            l=[]
            st=(sum(self.istates)>=1)
            if (st and self.st) or ((not st) and (not self.st)):
                return
            self.st=st
            if self.st:
                for i in range(1,15):
                    posx,posy,posz=self.x+rs[0]*i,self.y+rs[1]*i,self.z+rs[2]*i
                    p=self.boss.l[posx][posy][posz]
                    if p==None or (hasattr(p,"unpushable") and p.unpushable):
                        break
                    else:
                        l.append(p)
                else:
                    self.st=0
                    self.unpushable=False
                    return
                posx,posy,posz=self.x+rs[0],self.y+rs[1],self.z+rs[2]
                self.boss.chpos(posx,posy,posz,_Piston_Head())
                for i in range(len(l)):
                    posx,posy,posz=self.x+rs[0]*(i+2),self.y+rs[1]*(i+2),self.z+rs[2]*(i+2)
                    self.boss.chpos(posx,posy,posz,None)
                for i in range(len(l)):
                    p=l[i]
                    if hasattr(p,'update_pos'):
                        p.update_pos(rs[0],rs[1],rs[2])
                    posx,posy,posz=self.x+rs[0]*(i+2),self.y+rs[1]*(i+2),self.z+rs[2]*(i+2)
                    self.boss.chpos(posx,posy,posz,p)
            else:
                posx,posy,posz=self.x+rs[0],self.y+rs[1],self.z+rs[2]
                self.boss.chpos(posx,posy,posz,None)
            self.unpushable=self.st
                
        def onremove(self):
            if self.st:
                posx,posy,posz=self.x+rs[0],self.y+rs[1],self.z+rs[2]
                self.boss.chpos(posx,posy,posz,None)
        
    class _Piston_Head(object):
        name="Piston head"
        p=[PhotoImage(file='piston_head_%s.gif'%plst[0]),
            PhotoImage(file='piston_head_%s.gif'%plst[1]),
            PhotoImage(file='piston_head_%s.gif'%plst[2])]
        t="unremovable"
        unpushable=True
        def __init__(self):
            pass

        def image(self,d):
            return self.p[d]
        
    return _Piston

def Piston(i):
    plst=[[5,1,1],[3,2,4],[4,3,3],[1,0,5]][i]
    return Piston_all(rotate_left_n([[1,0,0]],i)[0],plst)

Piston_Up=Piston_all([0,1,0],[2,5,2])
Piston_Down=Piston_all([0,-1,0],[0,4,0])

def Sticky_Piston_all(rs,plst):
    class _Sticky_Piston(Mesecon_thing):
        name="Sticky piston"
        p=[[PhotoImage(file='sticky_piston_%s_off.gif'%plst[0]),
            PhotoImage(file='sticky_piston_%s_off.gif'%plst[1]),
            PhotoImage(file='sticky_piston_%s_off.gif'%plst[2])],
           [PhotoImage(file='sticky_piston_%s_on.gif'%plst[0]),
            PhotoImage(file='sticky_piston_%s_on.gif'%plst[1]),
            PhotoImage(file='sticky_piston_%s_on.gif'%plst[2])]]
        def __init__(self,boss,x,y,z):
            Mesecon_thing.__init__(self,default_rules,[])
            self.x,self.y,self.z,self.boss=x,y,z,boss
            self.st=False
            self.unpushable=False

        def update_pos(self,xadd,yadd,zadd):
            self.x+=xadd
            self.y+=yadd
            self.z+=zadd

        def image(self,d):
            return self.p[self.st][d]

        @classmethod
        def imagedraw(cls):
            return cls.p[0][1]

        def update_outputs(self):
            l=[]
            st=(sum(self.istates)>=1)
            if (st and self.st) or ((not st) and (not self.st)):
                return
            self.st=st
            if self.st:
                for i in range(1,15):
                    posx,posy,posz=self.x+rs[0]*i,self.y+rs[1]*i,self.z+rs[2]*i
                    p=self.boss.l[posx][posy][posz]
                    if p==None or (hasattr(p,"unpushable") and p.unpushable):
                        break
                    else:
                        l.append(p)
                else:
                    self.st=0
                    self.unpushable=False
                    return
                posx,posy,posz=self.x+rs[0],self.y+rs[1],self.z+rs[2]
                self.boss.chpos(posx,posy,posz,_Sticky_Piston_Head())
                for i in range(len(l)):
                    posx,posy,posz=self.x+rs[0]*(i+2),self.y+rs[1]*(i+2),self.z+rs[2]*(i+2)
                    self.boss.chpos(posx,posy,posz,None)
                for i in range(len(l)):
                    p=l[i]
                    if hasattr(p,'update_pos'):
                        p.update_pos(rs[0],rs[1],rs[2])
                    posx,posy,posz=self.x+rs[0]*(i+2),self.y+rs[1]*(i+2),self.z+rs[2]*(i+2)
                    self.boss.chpos(posx,posy,posz,p)
            else:
                posx2,posy2,posz2=self.x+2*rs[0],self.y+2*rs[1],self.z+2*rs[2]
                posx,posy,posz=self.x+rs[0],self.y+rs[1],self.z+rs[2]
                p=self.boss.l[posx2][posy2][posz2]
                if hasattr(p,'unpushable') and p.unpushable:
                    self.boss.chpos(posx,posy,posz,None)
                else:
                    if hasattr(p,'update_pos'):
                        p.update_pos(-rs[0],-rs[1],-rs[2])
                    self.boss.chpos(posx2,posy2,posz2,None)
                    self.boss.chpos(posx,posy,posz,p)
            self.unpushable=self.st
                
        def onremove(self):
            if self.st:
                posx,posy,posz=self.x+rs[0],self.y+rs[1],self.z+rs[2]
                self.boss.chpos(posx,posy,posz,None)
        
    class _Sticky_Piston_Head(object):
        name="Sticky piston head"
        p=[PhotoImage(file='sticky_piston_head_%s.gif'%plst[0]),
            PhotoImage(file='sticky_piston_head_%s.gif'%plst[1]),
            PhotoImage(file='sticky_piston_head_%s.gif'%plst[2])]
        t="unremovable"
        unpushable=True
        def __init__(self):
            pass

        def image(self,d):
            return self.p[d]
        
    return _Sticky_Piston

def Sticky_Piston(i):
    plst=[[5,1,1],[3,2,4],[4,3,3],[1,0,5]][i]
    return Sticky_Piston_all(rotate_left_n([[1,0,0]],i)[0],plst)

Sticky_Piston_Up=Sticky_Piston_all([0,1,0],[2,5,2])
Sticky_Piston_Down=Sticky_Piston_all([0,-1,0],[0,4,0])

Inverters=rotated(Inverter,4)
t=Inverters(0,0,0,0)
#print (t.__class__ is ClassContainer._Inverter0)
#print ClassContainer._Inverter0.__name__
#b=pickle.dumps(t)
#print str(b)
Diodes=rotated(Diode,4)
Ands=rotated(And,4)
Nands=rotated(Nand,4)
Xors=rotated(Xor,4)
Insulateds=rotated(Insulated,2)
Insulated_ts=rotated(Insulated_t,4)
Pistons=rotated(Piston,4)
Sticky_Pistons=rotated(Sticky_Piston,4)

a.set_buttons(Normal_block,Mesecon,Switch,Inverters,Diodes,Ands,Nands,Xors,Insulateds,
              Insulated_ts,RedLightStone,Pistons,Piston_Up,Piston_Down,Sticky_Pistons,Sticky_Piston_Up,
              Sticky_Piston_Down)
os.chdir(TOPDIR)
a.mainloop()
