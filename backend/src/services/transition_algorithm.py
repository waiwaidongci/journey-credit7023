import numpy as np
from scipy.sparse import coo_matrix,csr_matrix

def transition_matrix(journeys,channel_codes):
    if not journeys:raise ValueError("路径批次为空")
    if not channel_codes or len(set(channel_codes))!=len(channel_codes) or set(channel_codes)&{'START','CONVERSION','NULL'}:raise ValueError("渠道标识重复、为空或占用保留状态")
    states=['START']+sorted(channel_codes)+['CONVERSION','NULL'];index={s:i for i,s in enumerate(states)}
    counts=np.zeros((len(states),len(states)),dtype=float)
    for j in journeys:
        path=j['path']
        if not isinstance(path,list) or len(path)>50 or any(type(c) is not str or c not in channel_codes for c in path):raise ValueError("路径包含未知渠道或长度超过50")
        if type(j['converted']) is not bool:raise ValueError("转化终点必须为布尔标记")
        sequence=['START']+path+['CONVERSION' if j['converted'] else 'NULL']
        for a,b in zip(sequence,sequence[1:]):counts[index[a],index[b]]+=1
    probabilities=np.zeros_like(counts)
    for i,state in enumerate(states):
        if state in ['CONVERSION','NULL']:probabilities[i,i]=1
        elif counts[i].sum()>0:probabilities[i]=counts[i]/counts[i].sum()
        else:probabilities[i,index['NULL']]=1
    return states,counts,probabilities

def _validate(journeys,channel_codes):
    if not journeys:raise ValueError("路径批次为空")
    if not channel_codes or len(set(channel_codes))!=len(channel_codes) or set(channel_codes)&{'START','CONVERSION','NULL'}:raise ValueError("渠道标识重复、为空或占用保留状态")
    known=set(channel_codes)
    for j in journeys:
        path=j['path']
        if not isinstance(path,list) or len(path)>50 or any(type(c) is not str or c not in known for c in path):raise ValueError("路径包含未知渠道或长度超过50")
        if type(j['converted']) is not bool:raise ValueError("转化终点必须为布尔标记")

def transition_counts_sparse(journeys,channel_codes):
    """与transition_matrix相同的校验与计数口径，但以COO稀疏三元组返回，不实例化完整方阵。"""
    _validate(journeys,channel_codes)
    states=['START']+sorted(channel_codes)+['CONVERSION','NULL'];index={s:i for i,s in enumerate(states)}
    conv=index['CONVERSION'];rows=[];cols=[]
    for j in journeys:
        sequence=[index[c] for c in j['path']]
        sequence.append(conv if j['converted'] else index['NULL']);sequence.insert(0,0)
        rows.extend(sequence[:-1]);cols.extend(sequence[1:])
    ones=np.ones(len(rows),dtype=float)
    counts=coo_matrix((ones,(np.asarray(rows),np.asarray(cols))),shape=(len(states),len(states))).tocsr()
    return states,counts

def probabilities_csr(states,counts):
    """计数CSR行归一：吸收终点自环为1，无出边行转NULL；与稠密口径逐元素一致。"""
    n=len(states);conv=states.index('CONVERSION');null=states.index('NULL')
    rowsum=np.asarray(counts.sum(axis=1)).ravel();observed=counts.tocoo()
    data=observed.data/rowsum[observed.row]
    extra_r=[conv,null];extra_c=[conv,null]
    for i in range(n):
        if rowsum[i]==0 and i not in (conv,null):extra_r.append(i);extra_c.append(null)
    probabilities=coo_matrix((np.concatenate([data,np.ones(len(extra_r))]),(np.concatenate([observed.row,extra_r]),np.concatenate([observed.col,extra_c]))),shape=(n,n)).tocsr()
    return probabilities
