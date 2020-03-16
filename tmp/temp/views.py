from django.shortcuts import render
from django.http import JsonResponse,FileResponse
from . import searchmap
import pickle
import networkx as nx
import json
import scipy.sparse as sp
from tqdm import tqdm
import numpy as np
# Create your views here.

def opens(request):
    s=searchmap.searchweb("",1,1)
    return render(request,'search.html',s)

node_dict = None
citation_dict = None
author_dict = None
weight_dict = None
id2idx = None

def load_baseline():
    weight = sp.load_npz('data/baseline.npz')
    with open('data/id2idx.json', 'r') as f:
        id2idx = json.load(f)
    return weight.astype(np.float64), id2idx


def query_weight(id_i, id_j, weight: sp.csr_matrix, id2idx) -> float:
    try:
        idx_i, idx_j = id2idx[id_i], id2idx[id_j]
        value = None
        for _ in range(len(weight[idx_i].indices)):
            if weight[idx_i].indices[_] == idx_j:
                value = weight.data[weight.indptr[idx_i] + _]
        assert value is not None and -1e-10 < value < 1 + 1e-10
        return value
    except:
        return 0.1

def get_value(id_i,id_j):
    # return np.random.rand()
    ans = query_weight(id_i,id_j,weight_dict,id2idx)
    ans = float(ans)
    print(ans,type(ans))
    return ans

def gen_graph(index):
    index = str(index)
    g = nx.DiGraph()
    root_name = node_dict[index]['title']
    g.add_node(index,label = root_name,value = 1.0,modularity_class = 'self')
    nb_list = []
    for nd in node_dict[index]['references']:
        nb_list.append((nd,get_value(index,nd),'references'))
    for nd in citation_dict.get(index,[]):
        nb_list.append((nd,get_value(index,nd),'cited'))
    nb_list.sort(key = lambda x:x[1],reverse = True)
    nb_list = list(filter(lambda x:x[1]>0.0,nb_list))[:10]
    if len(nb_list) > 0:
        val_max = nb_list[0][1]
        for nd,val,clas in nb_list:
            g.add_node(nd,label = node_dict[nd]['title'],value = val/val_max, modularity_class = clas)
            g.add_edge(nd,index,weight = val/val_max)
    for aut in node_dict[index]['authors']:
        for nd in author_dict[aut['id']]:
            if nd not in g.nodes and len(g.nodes)<15:
                g.add_node(nd,label = node_dict[nd]['title'],value = 0.4, modularity_class = 'co-author')
                g.add_edge(nd,index,weight = 0.4)
                
    return g

def getgexf(request,index):
    global node_dict,citation_dict,author_dict,weight_dict,id2idx
    if node_dict == None:
        with open('data/processed_data_v11_1.pkl','rb') as f:
            node_dict,citation_dict,author_dict = pickle.load(f)
        weight_dict,id2idx = load_baseline()
    file_path = 'data/graphs/' + str(index) + '.gexf'
    graph = gen_graph(int(index))
    # nx.write_gexf(graph,file_path)
    graph_dict = {'nodes':[],'links':[]}
    for nd in graph.nodes:
        d = graph.nodes[nd]
        d['id'] = nd
        graph_dict['nodes'].append(d)
    for u,v in graph.edges:
        d = graph.edges[(u,v)]
        d['source'] = u
        d['target'] = v
        graph_dict['links'].append(d)
    # return FileResponse(open(file_path,'rb'))
    return JsonResponse(graph_dict)

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
