from django.shortcuts import render
from django.http import JsonResponse,FileResponse,HttpResponse
import pickle
import networkx as nx
import json
import scipy.sparse as sp
from tqdm import tqdm
import numpy as np
import math
from temp.models import *
from django.db.models import Sum
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
    with open('data/edge_query_dict.json', 'r') as f:
        edge_query_dict = json.load(f)
    with open('data/id2idx.json', 'r') as f:
        id2idx = json.load(f)
    return edge_query_dict, id2idx

def query_weight(id_i, id_j, weight: dict, id2idx: dict) -> list:
    idx_i, idx_j = id2idx[id_i], id2idx[id_j]
    key = str(idx_i) + '_' + str(idx_j)
    queried_results = weight[key]
    return queried_results

def sigmoid(x):
    return 1 / (1 + math.exp(-x))


def compute_score(cross_feature, n_citation):
    impact = sigmoid(n_citation / 10)
    score = cross_feature * impact
    return score

'''
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

def generate_database(request):
    global node_dict,citation_dict,author_dict,kw_dic,title_dic,weight_dict,id2idx
    init_data()
    auts = [Author(name = aut) for aut in tqdm(author_dict)]
    Author.objects.bulk_create(auts)
    papers = []
    refs = []
    for idx in tqdm(node_dict):
        nd = node_dict[idx]
        g = gen_graph(idx)
        paper = Paper(idx = int(idx), title = nd['title'][:200], venue = nd['venue'][:300],year = nd['year'],citation = nd['citation'],abstract = nd['abstract'],keywords = ';'.join(nd['keywords'][:5]),authors = ';'.join(nd['authors'][:3]))
        for nb in g.nodes:
            neb = g.nodes[nb]
            if neb['modularity_class'] != 'self':
                nbr = Edge(uid = int(idx),vid = int(nb),relevance = neb['relevance'],impact = neb['impact'],score = neb['score'],relation = neb['modularity_class'],title = neb['label'][:200])
                refs.append(nbr)
        papers.append(paper)
    Paper.objects.bulk_create(papers)
    Edge.objects.bulk_create(refs)
    return HttpResponse('init over!')

'''
    
def init_data():
    return
'''
    global kw_dic,title_dic
    if kw_dic == None:
        print('init start')
        with open('data/keywords.pkl','rb') as f:
            kw_dic,title_dic = pickle.load(f)
        print('init over')
'''

def get_value(id_i,id_j):
    try:
        ans = query_weight(id_i,id_j,weight_dict,id2idx)
        ans[2] = compute_score(ans[0],ans[1])
        return tuple(ans)
    except:
        ans = [0,node_dict[id_j]['citation'],0]
        ans[2] = compute_score(ans[0],ans[1])
        return tuple(ans)

def gen_graph(index):
    index = str(index)
    g = nx.DiGraph()
    node = Paper.objects.get(idx = int(index))
    neighbors = Edge.objects.filter(uid = int(index))
    root_name = node.title
    g.add_node(index,label = root_name,showValue = 1.5,relevance = 1.0, impact = node.citation, score = 1.0,modularity_class = 'self')
    nb_list = [_ for _ in neighbors if _.relation!='co-author']
    co_list = [_ for _ in neighbors if _.relation=='co-author']
    if len(nb_list)>0:
        nb_max = np.max([_.score for _ in nb_list])
    if len(co_list)>0:
        co_max = np.max([_.score for _ in co_list])
    for nd in nb_list:
        showValue,relevance,impact,score = 0.5*nd.score/nb_max+0.7,nd.relevance,nd.impact,nd.score
        g.add_node(str(nd.vid),label = nd.title,showValue = showValue,relevance = relevance, impact = impact, score = score, modularity_class = nd.relation)
        g.add_edge(str(nd.vid),index,weight = showValue)
    for nd in co_list:
        showValue,relevance,impact,score = 0.4*nd.score/co_max+0.3,nd.relevance,nd.impact,nd.score
        g.add_node(str(nd.vid),label = nd.title,showValue = showValue,relevance = relevance, impact = impact, score = score, modularity_class = nd.relation)
        g.add_edge(str(nd.vid),index,weight = showValue)
    return g

def getgexf(request,index):
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
    node = {}
    nd = Paper.objects.get(idx = int(idx))
    node['idx'] = str(nd.idx)
    node['title'] = nd.title
    node['year'] = nd.year
    node['venue'] = nd.venue
    node['abstract'] = nd.abstract
    node['keywords'] = nd.keywords.split(';')
    node['authors'] = nd.authors.split(';')
    node['citation'] = nd.citation
    return node

def get_messages(idxs:list):
    idxs = [int(idx) for idx in idxs]
    nds = Paper.objects.filter(idx__in = idxs)
    papers = []
    for nd in nds:
        node = {}
        node['idx'] = str(nd.idx)
        node['title'] = nd.title
        node['year'] = nd.year
        node['venue'] = nd.venue
        node['abstract'] = nd.abstract
        node['keywords'] = nd.keywords.split(';')
        node['authors'] = nd.authors.split(';')
        node['citation'] = nd.citation
        papers.append(node)
    return papers

def search_paper(sentence:str):
    # global title_dic,kw_dic
    # init_data()
    sentence.replace('%20',' ').replace(':',' ')
    ans_dic = {}
    sentence = sentence.strip()
    possible_kw = [sentence]
    sentence = sentence.lower()
    sentence = sentence.split(' ')
    for st in range(len(sentence)):
        for ed in range(st+1,len(sentence)+1):
            kw = ' '.join(sentence[st:ed])
            possible_kw.append(kw)
    ans = Keyword.objects.filter(keyword__in = possible_kw).values('idx').annotate(val = Sum('score')).order_by('-val')
    return [_['idx'] for _ in ans]


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
    page = int(page)
    paper_ids = search_paper(keywords)
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
    papers = get_messages(paper_ids)
    for paper in papers:
        paper['website'] = 'graph_' + paper['idx']
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
    render_dict['answers'] = papers
    return render(request,'search.html',render_dict)
    '''
    except:
        return render(request,'start.html')
   '''
