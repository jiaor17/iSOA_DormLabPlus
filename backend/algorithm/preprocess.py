import json
import networkx as nx
from tqdm import tqdm
import numpy as np
import scipy.sparse as sp
import pickle


kw_max_keep_num = 5
feats_size = 200
class_num = 8
train_p = 0.7
val_p = 0.2
test_p = 0.1


def preprocess():

    with open('../data/subgraph_v11_1.json', 'r') as f:
        nodes = f.readlines()

    g = nx.DiGraph()

    print('node num: ', len(nodes))
    id2idx = {}
    all_node = []
    all_kw = {}
    cnt_bad_nodes = 0
    edge_num = 0
    all_class = {}
    for idx in tqdm(range(len(nodes))):
        cur_node = {}
        mes = json.loads(nodes[idx])
        id2idx[mes['id']] = idx
        bad_node = False
        try:
            feat_list = mes['fos']
            kw_mes = []
            for _ in feat_list:
                obj = (_['name'], _['w'])
                kw_mes.append(obj)
            # sort by weight and get top K keywords
            kw_mes.sort(key=lambda x: x[1], reverse=True)
            kw_mes = kw_mes[: min(len(kw_mes), kw_max_keep_num)]
            for _ in kw_mes:
                _ = _[0]
                if _ not in all_kw:
                    all_kw[_] = 1
                else:
                    all_kw[_] += 1
            cur_node['kw'] = [_[0] for _ in kw_mes]
        except:
            cur_node['kw'] = []
            bad_node = True

        try:
            label = mes['venue']
            # conference with id
            assert len(label) > 1
            label = label['raw']
            cur_node['label'] = label
            if label in all_class:
                all_class[label] += 1
            else:
                all_class[label] = 1

        except:
            bad_node = True
            cur_node['label'] = None

        # we currently overlook weight here
        if bad_node:
            cnt_bad_nodes += 1
        cur_node['id'] = mes['id']
        cur_node['references'] = mes['references']
        edge_num += len(cur_node['references'])
        all_node.append(cur_node)
    print('edge num:         ', edge_num)
    print('class num:        ', len(all_class))
    print('all keywords num: ', len(all_kw))
    print('bad nodes num:    ', cnt_bad_nodes)
    print('bad nodes percent:', round(cnt_bad_nodes / len(nodes) * 100, 3), '%')
    print('average keyword mentioned num:', (len(nodes) - cnt_bad_nodes) * kw_max_keep_num / len(all_kw))
    cnttt = 0
    for _ in all_kw:
        if all_kw[_] < 10:
            cnttt += 1
    print('kw percent < 10:  ', cnttt / len(all_kw) * 100, '%')
    print('start generating graph nodes', '***' * 10)
    # filter out bad nodes, so we need to construct a dict to record the idxes of the filtered-out nodes
    convert_back = {}
    convert = {}
    cnt = 0
    feats = []
    class_map = {}
    for idx in tqdm(range(len(all_node))):
        # filter out bad nodes
        if len(all_node[idx]['kw']) == 0 or all_node[idx]['label'] is None:
            continue
        convert_back[cnt] = idx
        convert[idx] = cnt
        g.add_node(cnt)
        feats.append(np.zeros(shape=[feats_size]))
        class_map[str(cnt)] = np.random.randint(class_num)
        cnt += 1
    feats = np.asarray(feats)
    print('feats shape: ', feats.shape)
    print('len classmap:', len(class_map))
    print('start generating graph edges', '***' * 10)
    cnt_edge = 0
    cnt_node = 0
    for idx in tqdm(range(len(all_node))):
        if idx in convert:
            cnt_node += 1
            for neighbor_idx in all_node[idx]['references']:
                if neighbor_idx not in id2idx:
                    continue
                neighbor_idx = id2idx[neighbor_idx]
                if neighbor_idx in convert:
                    # undirected graph
                    g.add_edge(convert[idx], convert[neighbor_idx])
                    g.add_edge(convert[neighbor_idx], convert[idx])
                    cnt_edge += 1
    print('final node num: ', len(g.nodes()))
    print('final edge num: ', len(g.edges()))
    print('start saving dataset')
    sp.save_npz('../data/adj_full.npz', nx.adjacency_matrix(g))
    print('adj_full.npz saved')
    sp.save_npz('../data/adj_train.npz', nx.adjacency_matrix(g))
    print('adj_train.npz saved')
    np.save('../data/feats.npy', feats)
    print('feats.npy saved')
    with open('../data/class_map.json', 'w') as f:
        json.dump(class_map, f)
    print('class_map.json saved')
    # role
    role = {'tr': [], 'va': [], 'te': []}
    rand_idx = np.random.permutation(feats.shape[0]).tolist()
    role['tr'] = rand_idx[:int(feats.shape[0] * train_p)]
    role['va'] = rand_idx[int(feats.shape[0] * train_p): int(feats.shape[0] * (train_p + val_p))]
    role['te'] = rand_idx[int(feats.shape[0] * (train_p + val_p)):]
    with open('../data/role.json', 'w') as f:
        json.dump(role, f)
    print('role.json saved')
    pickle.dump(convert, open('../data/idx_convert.pkl', 'wb'))
    print('idx_convert.pkl saved')
    print('finished')
    return


if __name__ == '__main__':
    preprocess()


