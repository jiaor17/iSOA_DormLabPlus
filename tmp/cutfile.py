import jieba
import re
import jieba.analyse
dic=dict()
wordtype=('n','ns','nt','nz','nr','nrf','nrfg','v','i','vn')
hint=['\u3000','\t']
for i in range(1,5001):
    f=open("ans/"+str(i)+".txt","rb")
    b=f.read().decode('GBK').split('\n',3)
    ans=[]
    ans.append(b[2])
    c=b[3].split('\n')
    ans.append(c[0])
    if len(c)>1:
        for j in range(1,len(c)):
            if len(c[j])==0 or len(c[j-1])==0:
                break;
            if c[j-1][0] in hint and c[j][0] not in hint:
                break
            else:
                ans.append(c[j])
    ans='\n'.join(ans)
    fin=jieba.analyse.textrank(ans,20,False,wordtype)
    for j in fin:
        k=dic.setdefault(j,[])
        k.append(i)
        dic[j]=k
    tim=b[1]
    if tim=='\r':
        wt=re.search(r'\d\d\d\d-\d\d-\d\d',b[0])
        if wt!=None:
            fm=wt.group()
            tim=fm[0:4]+'年'+fm[5:7]+'月'+fm[8:10]+'日'+'\r'
    forall=b[0]+'\n'+tim+'\n'+ans
    f.close()
    f=open("ans/"+str(i)+".txt","wb")
    f.write(forall.encode('GBK',errors='ignore'))
    f.close()
    print(i)
f=open("ans/keywords.txt","wb")
ans=""
for i in dic.keys():
        ans+=i+' : '
        for j in dic[i]:
                ans+=str(j)+' '
        ans+='\r\n'
f.write(ans.encode('GBK'))
f.close()
