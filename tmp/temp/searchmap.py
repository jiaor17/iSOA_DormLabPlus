import jieba
import re
import math
import time
dic={}
hasinit=False
def init():
    global dic
    global hasinit
    if hasinit:
        return
    f=open("ans/keywords.txt","rb")
    allans=f.read().decode("GBK").split('\n')
    for i in allans:
        try:
            oneans=i.split(':')
            onekey=oneans[0].split(' ')[0]
            onelist=[]
            onevalue=oneans[1].split(' ')
            for j in onevalue:
                try:
                    onelist.append(int(j))
                except:
                    continue
            dic[onekey]=onelist
        except:
            continue
    f.close()
    hasinit=True
    print(len(dic))
class sanswer:
    def __init__(self,w,t,c):
        self.website=w
        self.title=t
        self.content=c
class pagen:
    def __init__(self,h,g,n):
        self.isherf=h
        self.goto=g
        self.num=n
def allweb(page,tp,fro,too):
    fr=fro.split('-')
    fr=fr[0]+'年'+fr[1]+'月'+fr[2]+'日'
    to=too.split('-')
    to=to[0]+'年'+to[1]+'月'+to[2]+'日'
    forret={}
    mes=''
    if tp==2:
        mes="很遗憾，未找到搜索结果<br>"
    ansn=[]
    for i in range(1,5001):
        f=open("ans/"+str(i)+".txt","rb")
        p=(f.read().decode("GBK")).split('\n',2)[1][0:11]
        if fr<=p<=to:
            ansn.append(i)
        f.close()
    pn=math.ceil(len(ansn)/10)
    forret['messages']=mes+"本网站共含有 "+str(len(ansn))+" 条相关新闻，共 "+str(pn)+" 页"
    aforr=[]
    for i in ansn[10*(page-1):10*page]:
        f=open("ans/"+str(i)+".txt","rb")
        p=(f.read().decode("GBK")).split('\n',3)
        f.close()
        p1=p[2]
        p2=p[3][0:100]
        s=sanswer(str(i),p1,p[1]+' '+p2+"...")
        aforr.append(s)
    forret['answers']=aforr
    aforp=[]
    lef=max(1,page-5)
    rig=min(pn+1,page+6)
    if lef!=1:
        aforp.append(pagen(True,"searchforpage1"+"from"+fro+"to"+too,"1"))
    if lef>2:
        aforp.append(pagen(False,"","..."))
    for i in range(lef,rig):
        if i==page:
            aforp.append(pagen(False,"",str(i)))
        else:
            aforp.append(pagen(True,"searchforpage"+str(i)+"from"+fro+"to"+too,str(i)))
    if rig<pn:
        aforp.append(pagen(False,"","..."))
    if rig<=pn:
        aforp.append(pagen(True,"searchforpage"+str(pn)+"from"+fro+"to"+too,str(pn)))
    forret['pas']=aforp
    forret['que']=""
    forret['ft']=fro
    forret['tt']=too
    return forret
def searchweb(keywords,page,tp,fro="2000-01-01",too="2018-12-31"):
    if tp!=0:
        return allweb(page,tp,fro,too)
    if keywords=='':
        return allweb(page,1,fro,too)
    start=time.clock()
    fr=fro.split('-')
    fr=fr[0]+'年'+fr[1]+'月'+fr[2]+'日'
    to=too.split('-')
    to=to[0]+'年'+to[1]+'月'+to[2]+'日'
    forret={}
    global dic
    global hasinit
    if hasinit==False:
        init()
    fin=jieba.cut_for_search(keywords)
    anslist={}
    inp=set()
    for i in fin:
        inp.add(i)
        try:
            l=dic[i]
            for j in l:
                num=anslist.setdefault(j,0)
                num+=1
                anslist[j]=num
        except:
            continue
    pickup=zip(anslist.values(),anslist.keys())
    anslist=sorted(pickup)
    it=0
    while it<len(anslist):
        f=open("ans/"+str(anslist[it][1])+".txt","rb")
        p=(f.read().decode("GBK")).split('\n',2)[1][0:11]
        if p<fr or p>to:
            anslist.remove(anslist[it])
            it-=1
        it+=1
        f.close()
    pagenum=math.ceil(len(anslist)/10)
    forret['messages']="共找到 "+str(len(anslist))+" 条新闻，共 "+str(pagenum)+" 页"
    anslist=anslist[-10*(page-1)-1:-10*page-1:-1]
    if len(anslist)==0:
        seterror=1/0
    aforr=[]
    for i in anslist:
        f=open("ans/"+str(i[1])+".txt","rb")
        p=(f.read().decode("GBK")).split('\n',3)
        fs1="<font color=red>"
        fs2="</font>"
        p1=p[2]
        ans1=""
        for j in jieba.cut(p1):
            if j in inp:
                ans1+=fs1+j+fs2
            else:
                ans1+=j
        p2=p[3]
        pos=0
        hint=False
        ans2=""
        while hint!=True and pos<len(p2):
            if pos!=0:
                ans2="..."
            else:
                ans2=""
            ph=p2[pos:pos+100]
            for j in jieba.cut(ph):
                if j in inp:
                    ans2+=fs1+j+fs2
                    hint=True
                else:
                    ans2+=j
            pos+=100
        s=sanswer(str(i[1]),ans1,p[1]+' '+ans2+"...")
        if pos<=len(p2):
            aforr.append(s)
        f.close()
    forret['answers']=aforr
    aforp=[]
    lef=max(1,page-5)
    rig=min(pagenum+1,page+6)
    if lef!=1:
        aforp.append(pagen(True,"searchfor"+keywords+"page1"+"from"+fro+"to"+too,"1"))
    if lef>2:
        aforp.append(pagen(False,"","..."))
    for i in range(lef,rig):
        if i==page:
            aforp.append(pagen(False,"",str(i)))
        else:
            aforp.append(pagen(True,"searchfor"+keywords+"page"+str(i)+"from"+fro+"to"+too,str(i)))
    if rig<pagenum:
        aforp.append(pagen(False,"","..."))
    if rig<=pagenum:
        aforp.append(pagen(True,"searchfor"+keywords+"page"+str(pagenum)+"from"+fro+"to"+too,str(pagenum)))
    forret['pas']=aforp
    forret['que']=keywords
    forret['ft']=fro
    forret['tt']=too
    end=time.clock()
    forret['messages']+="，用时"+str(end-start)+"秒"
    return forret
class onelink:
    def __init__(self,u,t):
        self.url=u
        self.title=t
def searchfile(fid):
    global dic
    global hasinit
    if hasinit==False:
        init()
    links=dict()
    for i in dic:
        if fid in dic[i]:
            for j in dic[i]:
                if j==fid:
                    continue
                num=links.setdefault(j,0)
                num+=1/len(dic[i])
                links[j]=num
    pickup=zip(links.values(),links.keys())
    links=sorted(pickup)[-1:-4:-1]
    aforl=[]
    for i in links:
        f=open("ans/"+str(i[1])+".txt","rb")
        b=f.read().decode("GBK")
        f.close()
        s=b.split('\n',3)
        aforl.append(onelink(str(i[1]),s[2]))
    return aforl
