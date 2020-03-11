from django.shortcuts import render
from django.http import JsonResponse,FileResponse
from . import searchmap
import pickle
import networkx as nx
# Create your views here.

def opens(request):
    s=searchmap.searchweb("",1,1)
    return render(request,'search.html',s)

node_dict = None
author_dict = None

def gen_graph(index):
    g = nx.DiGraph()
    root_name = node_dict[index]['title']
    g.add_node(index,label = root_name,modularity_class = 'self')
    for nd in node_dict[index]['references']:
        if len(g.nodes)<5:
            g.add_node(nd,label = node_dict[nd]['title'],modularity_class = 'references')
            g.add_edge(nd,index)
    for nd in node_dict[index]['cited']:
        if len(g.nodes)<10:
            g.add_node(nd,label = node_dict[nd]['title'],modularity_class = 'cited')
            g.add_edge(index,nd)
    for aut in node_dict[index]['authers']:
        for nd in author_dict[aut]:
            if nd not in g.nodes and len(g.nodes)<15:
                g.add_node(nd,label = node_dict[nd]['title'],modularity_class = 'co-author')
                g.add_edge(index,nd)
    return g

def getgexf(request,index):
    try:
        global node_dict,author_dict
        if node_dict == None:
            node_dict = pickle.load(open('data/citationv1.pkl','rb'))
        if author_dict == None:
            author_dict = pickle.load(open('data/citationv1_author.pkl','rb'))
        file_path = 'data/graphs/' + str(index) + '.gexf'
        try:
            return FileResponse(open(file_path,'rb'))
        except:
            graph = gen_graph(int(index))
            nx.write_gexf(graph,file_path)
            return FileResponse(open(file_path,'rb'))
    except:
        return render(request,'start.html')

def writegraph(request,index):
    try:
        dic = {'gexf':'"'+'graphs_'+index+'"'}
        return render(request,'graph.html',dic)
    except:
        return render(request,'start.html')

def showgraph(request):
    try:
        return FileResponse(open('webss/test.gexf','rb'))
    except:
        return render(request,'start.html')

def writeweb(request,offset):
    try:
        a=int(offset)
        f=open("ans/"+offset+".txt","rb")
        b=f.read().decode("GBK")
        f.close()
        s=b.split('\n',3)
        dic=dict()
        dic['website']=s[0]
        dic['time']=s[1]
        dic['title']=s[2]
        dic['content']='<br>'.join(s[3].split('\n'))
        dic['links']=searchmap.searchfile(int(offset))
        return render(request,'file.html',dic)
    except:
        return render(request,'start.html')

def searchfor(request,offset0,offset1,f,t):
    try:
        s=searchmap.searchweb(offset0,int(offset1),0,f,t)
        return render(request,'search.html',s)
    except:
        try:
            s=searchmap.searchweb("",1,2)
            return render(request,'search.html',s)
        except:
            return render(request,'start.html')
