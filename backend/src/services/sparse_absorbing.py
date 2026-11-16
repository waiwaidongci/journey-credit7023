import numpy as np
from scipy.sparse import eye
from scipy.sparse.linalg import splu

COND_LIMIT=1e12

def _validate(p,states):
    """与absorbing_algorithm.absorption_probability相同的输入校验，稀疏实现。"""
    if len(states)!=len(set(states)) or not {'START','CONVERSION','NULL'}<=set(states) or p.shape!=(len(states),len(states)):raise ValueError("状态或矩阵形状无效")
    if not np.isfinite(p.data).all() or (p.data<0).any() or not np.allclose(np.asarray(p.sum(axis=1)).ravel(),1,atol=1e-10,rtol=0):raise ValueError("转移概率须非负、有限且每行和为1")
    conv=states.index('CONVERSION');null=states.index('NULL')
    for i in (conv,null):
        s,e=p.indptr[i],p.indptr[i+1]
        if e-s!=1 or p.indices[s]!=i or abs(p.data[s]-1)>1e-12:raise ValueError("CONVERSION与NULL必须是吸收状态")

def _reachable(p,sources):
    """沿data>0的有向边从sources可达的状态集合（bytearray）。"""
    seen=bytearray(p.shape[0]);stack=[]
    for s in sources:
        if not seen[s]:seen[s]=1;stack.append(s)
    indptr,indices,data=p.indptr,p.indices,p.data
    while stack:
        i=stack.pop()
        for k in range(indptr[i],indptr[i+1]):
            j=indices[k]
            if data[k]>0 and not seen[j]:seen[j]=1;stack.append(j)
    return seen

class _Solution:
    __slots__=("states","transient","pos","start","u","fundamental","base")

def _solve(p,states):
    """校验并求解(I-Q)u=r，返回暂态上下文；不可达闭类排除在求解外，可达非吸收闭类明确失败。"""
    _validate(p,states)
    n=len(states);start=states.index('START');conv=states.index('CONVERSION');null=states.index('NULL')
    reach=_reachable(p,[start]);absorb=_reachable(p.tocsr().T.tocsr(),[conv,null])
    if any(reach[i] and not absorb[i] for i in range(n)):raise ValueError("START可达非吸收闭类，无法计算完整吸收概率")
    transient=sorted(i for i in range(n) if reach[i] and i not in (conv,null))
    pos={s:k for k,s in enumerate(transient)};m=len(transient)
    q=p[transient][:,transient];a=(eye(m,format='csr')-q).tocsc()
    try:lu=splu(a)
    except MemoryError:raise
    except RuntimeError as e:
        if 'MALLOC' in str(e) or 'memory' in str(e).lower():raise ValueError("归因计算内存不足（分解分配失败），已明确拒绝，不发布部分结果")
        raise ValueError("转移矩阵不可解")
    try:fundamental=lu.solve(np.eye(m))
    except MemoryError:raise
    except Exception as e:
        if 'MALLOC' in str(e) or 'memory' in str(e).lower():raise ValueError("归因计算内存不足（求解分配失败），已明确拒绝，不发布部分结果")
        raise ValueError("转移矩阵不可解")
    if not np.isfinite(fundamental).all():raise ValueError("转移矩阵不可解")
    norm_a=np.asarray(abs(a).sum(axis=0)).ravel().max(initial=0.)
    norm_n=np.abs(fundamental).sum(axis=0).max(initial=0.)
    if norm_a*norm_n>COND_LIMIT:raise ValueError("转移矩阵病态，吸收概率不稳定")
    r=np.asarray(p.getcol(conv).todense()).ravel()[transient]
    u=lu.solve(r)
    sol=_Solution();sol.states=states;sol.transient=transient;sol.pos=pos;sol.start=pos[start]
    sol.u=u;sol.fundamental=fundamental
    raw=float(u[sol.start])
    if not np.isfinite(raw) or raw<-1e-8 or raw>1+1e-8:raise ValueError("吸收概率超出有效范围")
    sol.base=min(1.,max(0.,raw))
    return sol

def absorption_probability_sparse(p,states):
    """与稠密absorption_probability同语义：START到CONVERSION的吸收概率。"""
    return _solve(p.tocsr(),states).base

def removal_probabilities_sparse(p,states):
    """一次LU分解得到全部渠道的转NULL移除概率。

    数学依据：删除渠道c（入c流量转NULL、c行转NULL）后，对其余暂态状态有
    u' = u - u_c · N[:,c] / N[c,c]，其中N=(I-Q)^-1为基本矩阵。
    与逐渠道重建矩阵再求解完全等价，不抽样、不截断小概率。
    不可达渠道的移除不改变START结果，与原算法一致返回基准概率。
    """
    sol=_solve(p.tocsr(),states)
    removed={}
    n_mat=sol.fundamental;s=sol.start;index={code:i for i,code in enumerate(states)}
    for code in states:
        if code in ('START','CONVERSION','NULL'):continue
        i=index[code]
        if i not in sol.pos:removed[code]=sol.base;continue
        k=sol.pos[i]
        raw=float(sol.u[s]-sol.u[k]*n_mat[s,k]/n_mat[k,k])
        if not np.isfinite(raw) or raw<-1e-8 or raw>1+1e-8:raise ValueError("吸收概率超出有效范围")
        removed[code]=min(1.,max(0.,raw))
    return sol.base,removed
