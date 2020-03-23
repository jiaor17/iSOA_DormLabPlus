from django.shortcuts import render
from django.http import JsonResponse,FileResponse
import pickle
import networkx as nx
import json
import scipy.sparse as sp
from tqdm import tqdm
import numpy as np
# Create your views here.

def opens(request):
    return render(request,'start.html')

node_dict = None
citation_dict = None
author_dict = None
kw_dic = None
title_dic = None
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
    
def init_data():
    global node_dict,citation_dict,author_dict,kw_dic,title_dic,weight_dict,id2idx
    if node_dict == None:
        with open('data/processed_data.pkl','rb') as f:
            node_dict,citation_dict,author_dict,kw_dic,title_dic = pickle.load(f)
        weight_dict,id2idx = load_baseline()

def get_value(id_i,id_j):
    # return np.random.rand()
    ans = query_weight(id_i,id_j,weight_dict,id2idx)
    ans = float(ans)
    # ans = 1.0
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
        for nd in author_dict[aut]:
            if nd not in g.nodes and len(g.nodes)<15:
                g.add_node(nd,label = node_dict[nd]['title'],value = 0.4, modularity_class = 'co-author')
                g.add_edge(nd,index,weight = 0.4)
                
    return g

def getgexf(request,index):
    global node_dict,citation_dict,author_dict,weight_dict,id2idx
    init_data()
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

def get_message(idx:str):
    global node_dict
    init_data()
    return node_dict[idx].copy()

def search_paper(sentence:str):
    global title_dic,kw_dic
    init_data()
    sentence.replace('%20',' ').replace(':',' ')
    sentence = sentence.lower().strip()
    ans_dic = {}
    if sentence in title_dic:
        ans_dic[title_dic[sentence]] = 10.0
    sentence = sentence.split(' ')
    for st in range(len(sentence)):
        for ed in range(st+1,len(sentence)+1):
            kw = ' '.join(sentence[st:ed])
            if kw in kw_dic:
                for idx,weight in kw_dic[kw]:
                    if idx not in ans_dic:
                        ans_dic[idx] = 0
                    ans_dic[idx] += weight
    for idx in ans_dic:
        ans_dic[idx] *= node_dict[idx]['citation']
    return sorted(ans_dic.items(),key = lambda x:x[1],reverse = True)


def writegraph(request,index):
    try:
        paper_mes = get_message(index)
        paper_mes['authors'] = ','.join(paper_mes['authors'])
        paper_mes['keywords'] = ','.join(paper_mes['keywords'])
        paper_mes['showAbstract'] = (paper_mes['abstract']!='')
        paper_mes['showKeywords'] = (paper_mes['keywords']!='')
        paper_mes['gexf'] = '"'+'graphs_'+index+'"'
        return render(request,'graph.html',paper_mes)
    except:
        return render(request,'start.html')
        
class pagen:
    def __init__(self,h,g,n):
        self.isherf=h
        self.goto=g
        self.num=n
        
def search_papers(request,keywords,page):
    try:
        page = int(page)
        paper_ids = search_paper(keywords)
        paper_ids = [ans[0] for ans in paper_ids]
        pagenum = int(np.ceil(len(paper_ids)/10))
        assert(page <= pagenum)
        render_dict = {}
        render_dict['messages'] = "About "+str(len(paper_ids))+" results, "+str(pagenum)+" pages"
        aforp=[]
        lef=max(1,page-5)
        rig=min(pagenum+1,page+6)
        if lef!=1:
            aforp.append(pagen(True,"searchfor"+keywords+"page1","1"))
        if lef>2:
            aforp.append(pagen(False,"","..."))
        for i in range(lef,rig):
            if i==page:
                aforp.append(pagen(False,"",str(i)))
            else:
                aforp.append(pagen(True,"searchfor"+keywords+"page"+str(i),str(i)))
        if rig<pagenum:
            aforp.append(pagen(False,"","..."))
        if rig<=pagenum:
            aforp.append(pagen(True,"searchfor"+keywords+"page"+str(pagenum),str(pagenum)))
        render_dict['pas'] = aforp
        paper_ids = paper_ids[(page-1)*10:page*10]
        papers = []
        for idx in paper_ids:
            paper = get_message(idx)
            paper['website'] = 'graph_' + idx
            venue = paper['venue'].split(' ')
            if len(venue)>3:
                venue = venue[:3] + ['...']
            paper['venue'] = ' '.join(venue)
            abstract = paper['abstract'].split(' ')
            if len(abstract)>30:
                abstract = abstract[:30] + ['...']
            paper['abstract'] = ' '.join(abstract)
            if paper['venue'] == '':
                paper['other_message'] = ','.join(paper['authors'][:4])+' '+str(paper['year'])
            else:
                paper['other_message'] = ','.join(paper['authors'][:3])+' -'+paper['venue']+','+str(paper['year'])
            papers.append(paper)
        render_dict['answers'] = papers
        return render(request,'search.html',render_dict)
    except:
        return render(request,'start.html')
