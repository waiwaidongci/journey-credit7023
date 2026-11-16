import numpy as np

def absorption_probability(matrix,states):
    try:p=np.asarray(matrix,dtype=float)
    except (TypeError,ValueError,OverflowError):raise ValueError("转移矩阵必须为有限数字")
    if len(states)!=len(set(states)) or not {'START','CONVERSION','NULL'}<=set(states) or p.shape!=(len(states),len(states)):raise ValueError("状态或矩阵形状无效")
    if not np.isfinite(p).all() or (p<0).any() or not np.allclose(p.sum(axis=1),1,atol=1e-10,rtol=0):raise ValueError("转移概率须非负、有限且每行和为1")
    start=states.index('START');conv=states.index('CONVERSION');null=states.index('NULL')
    for i in [conv,null]:
        expected=np.zeros(len(states));expected[i]=1
        if not np.allclose(p[i],expected,atol=1e-12,rtol=0):raise ValueError("CONVERSION与NULL必须是吸收状态")
    reachable={start};stack=[start]
    while stack:
        i=stack.pop()
        for j in np.flatnonzero(p[i]>0):
            if int(j) not in reachable:reachable.add(int(j));stack.append(int(j))
    can_absorb={conv,null};changed=True
    while changed:
        changed=False
        for i in range(len(states)):
            if i not in can_absorb and any(p[i,j]>0 for j in can_absorb):can_absorb.add(i);changed=True
    if reachable-can_absorb:raise ValueError("START可达非吸收闭类，无法计算完整吸收概率")
    transient=sorted(reachable-{conv,null});q=p[np.ix_(transient,transient)];a=np.eye(len(transient))-q
    try:
        if np.linalg.cond(a)>1e12:raise ValueError("转移矩阵病态，吸收概率不稳定")
        values=np.linalg.solve(a,p[transient,conv])
    except np.linalg.LinAlgError:raise ValueError("转移矩阵不可解")
    probability=float(values[transient.index(start)])
    if not np.isfinite(probability) or probability< -1e-8 or probability>1+1e-8:raise ValueError("吸收概率超出有效范围")
    return min(1.,max(0.,probability))

def remove_to_null(matrix,states,channel):
    if channel not in states or channel in ['START','CONVERSION','NULL']:raise ValueError("只能移除真实渠道")
    result=np.array(matrix,dtype=float,copy=True);c=states.index(channel);null=states.index('NULL')
    for i in range(len(states)):
        if i!=c:result[i,null]+=result[i,c];result[i,c]=0
    result[c]=0;result[c,null]=1
    return result
