import numpy as np

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
