from urllib import request
import re
import chardet
cur=0
found=[]
dic=dict()
def dfs(u,sts):
        if(sts>10):
                return
        global found
        if u in found:
                return
        found.append(u)
        global cur
        a=request.urlopen(u)
        b=a.read()
        c=chardet.detect(b)
        b=b.decode(c['encoding'],errors='ignore')
        ans=""
        title=re.findall(r'<title[^>]*>([^_|]*)[^<]*</title>',b)
        times=re.findall(r'class="date">([^<]*)<',b)
        time=""
        if len(times)>=1:
                time=times[0]+"\r\n"
        else:
                time="\r\n"
        ans+=title[0]+"\r\n"
        text=re.findall(r'<p>([^<]*)</p>',b)
        for i in text:
            ans+=i+"\r\n"
        if len(ans)>=300 and len(u.split('/'))>5:
                global dic
                print(cur)
                cur+=1
                filename="ans/"+str(cur)+".txt"
                f=open(filename,"wb")
                an=u+"\r\n"+time+ans
                f.write(an.encode('GBK',errors='ignore'))
                f.close()
        urls=re.findall(r'<a[^h]*href="([^"]*)"',b)
        for i in urls:
                try:
                        if i.split('/')[2]!="news.sina.com.cn" :
                                continue
                        if cur<5000 :
                                dfs(i,sts+1)
                
                except:
                        continue
dfs("http://news.sina.com.cn/",0)
