import json
import scipy.sparse as sp
import networkx as nx
from tqdm import tqdm
import numpy as np

kw_max_keep_num = 5


def load_baseline():
    weight = sp.load_npz('../data/baseline.npz')
    with open('../data/id2idx.json', 'r') as f:
        id2idx = json.load(f)
    return weight, id2idx


def query_weight(id_i, id_j, weight: sp.csr_matrix, id2idx) -> float:
    idx_i, idx_j = id2idx[id_i], id2idx[id_j]
    value = None
    for _ in range(len(weight[idx_i].indices)):
        if weight[idx_i].indices[_] == idx_j:
            value = weight.data[weight.indptr[idx_i] + _]
    assert value is not None and -1e-10 < value < 1 + 1e-10
    return value


def baseline():

    with open('../data/subgraph_v11_1.json', 'r') as f:
        nodes = f.readlines()

    g = nx.DiGraph()

    print('node num: ', len(nodes))
    id2idx = {}
    all_node = []
    edge_num = 0
    for idx in tqdm(range(len(nodes))):
        cur_node = {}
        mes = json.loads(nodes[idx])
        id2idx[mes['id']] = idx
        try:
            feat_list = mes['fos']
            kw_mes = []
            for _ in feat_list:
                obj = (_['name'], _['w'])
                kw_mes.append(obj)
            # sort by weight and get top K keywords
            kw_mes.sort(key=lambda x: x[1], reverse=True)
            kw_mes = kw_mes[: min(len(kw_mes), kw_max_keep_num)]
            cur_node['kw'] = kw_mes
        except:
            cur_node['kw'] = []

        cur_node['id'] = mes['id']
        cur_node['references'] = mes['references']
        edge_num += len(cur_node['references'])
        all_node.append(cur_node)
        g.add_node(idx)

    print('add edge')
    cnt = 0
    for idx in tqdm(range(len(all_node))):
        cnt += len(all_node[idx]['references'])
        for neighbor_idx in all_node[idx]['references']:
            if neighbor_idx not in id2idx:
                print('edge out of the graph')
                continue
            neighbor_idx = id2idx[neighbor_idx]
            g.add_edge(idx, neighbor_idx)
            g.add_edge(neighbor_idx, idx)
    print('cnt estimated edge num: ', cnt * 2)

    adj = nx.adjacency_matrix(g).astype(float)
    print('nnz: ', adj.nnz)
    for i in tqdm(range(adj.shape[0])):
        feat_u = all_node[i]['kw']
        # if center node has no feature vector, then all edges have the same weight
        if len(feat_u) == 0:
            for j in range(len(adj[i].indices)):
                adj.data[adj.indptr[i] + j] = 1 / len(adj[i].indices)
        # else, compute inner product and uniform into sum = 1
        else:
            weight_list = []
            for j in range(len(adj[i].indices)):
                feat_v = all_node[adj[i].indices[j]]['kw']
                inner_product = 0
                for _u in range(len(feat_u)):
                    for _v in range(len(feat_v)):
                        # if word match
                        if feat_u[_u][0] == feat_v[_v][0]:
                            inner_product += (feat_u[_u][1] * feat_v[_v][1])
                weight_list.append(inner_product)
            # if sum too small, then treat it as uniform distribution
            if sum(weight_list) < 1e-8:
                for j in range(len(adj[i].indices)):
                    adj.data[adj.indptr[i] + j] = 1 / len(adj[i].indices)
            else:
                weight_list = (np.asarray(weight_list) / sum(weight_list)).tolist()
                for j in range(len(adj[i].indices)):
                    adj.data[adj.indptr[i] + j] = weight_list[j]
    sp.save_npz('../data/baseline.npz', adj)
    print('baseline.npz saved')
    with open('id2idx.json', 'w') as f:
        json.dump(id2idx, f)
    print('id2idx.json saved')
    return


if __name__ == '__main__':

    _, __ = load_baseline()
    while True:
        i = int(input())
        j = int(input())
        print(query_weight(i, j, _, __))

    # baseline()

