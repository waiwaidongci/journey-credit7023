from collections import Counter
from ..config import settings
from .transition_algorithm import transition_counts_sparse,probabilities_csr
from .sparse_absorbing import removal_probabilities_sparse
from ..utils.fingerprint import fingerprint

def analyze_attribution(batch,journeys,channels):
    journeys=sorted(journeys,key=lambda j:j['code']);channels=sorted(channels,key=lambda c:c['code'])
    if len({j['code'] for j in journeys})!=len(journeys):raise ValueError("匿名路径编号重复")
    if len(channels)>settings.ATTRIBUTION_MAX_CHANNELS:raise ValueError(f"渠道数{len(channels)}超过规模上限{settings.ATTRIBUTION_MAX_CHANNELS}，明确拒绝计算")
    codes=[c['code'] for c in channels];states,counts=transition_counts_sparse(journeys,codes)
    matrix=probabilities_csr(states,counts)
    if matrix.nnz>settings.ATTRIBUTION_MAX_EDGES:raise ValueError(f"非零转移边{matrix.nnz}超过规模上限{settings.ATTRIBUTION_MAX_EDGES}，明确拒绝计算")
    base,removed=removal_probabilities_sparse(matrix,states)
    if base<=1e-12:raise ValueError("基准转化概率为零，无法定义相对移除效应")
    total_conversions=sum(j['converted'] for j in journeys)
    touches=Counter();last=Counter()
    for j in journeys:
        touches.update(j['path'])
        if j['converted'] and j['path']:last[j['path'][-1]]+=1
    credit=[]
    for c in channels:
        effect=max(0.,(base-removed[c['code']])/base)
        credit.append({**c,"removed_probability":removed[c['code']],"removal_effect":effect,"touches":touches[c['code']],"last_touch_conversions":last[c['code']]})
    total_effect=sum(c['removal_effect'] for c in credit)
    if total_effect<=1e-12:raise ValueError("所有渠道移除效应为零，不能归一归因")
    for c in credit:
        c['share']=c['removal_effect']/total_effect;c['credited_conversions']=c['share']*total_conversions
        c['association_score']=c['credited_conversions']/c['touches'] if c['touches'] else 0.
    count_map=counts.todok();edges=[]
    coo=matrix.tocoo()
    for i,j,prob in sorted(zip(coo.row,coo.col,coo.data)):
        edges.append({"source":states[i],"target":states[j],"probability":float(prob),"count":float(count_map.get((i,j),0.))})
    info={"id":batch.id,"name":batch.name,"source":batch.source}
    return {"batch":info,"journey_count":len(journeys),"conversions":total_conversions,"base_probability":base,"states":states,"transition_edges":edges,"credits":credit,"input_hash":fingerprint({"method":"absorbing-null-removal-v1","batch":info,"journeys":journeys,"channels":channels}),"removal_policy":"所有指向被移除渠道的概率流量转入NULL；被移除渠道本身转NULL，不跨接路径，其他行保持和1。","assumptions":"一阶马尔可夫、观察期路径闭合且渠道定义一致；移除效应是关联模型，不是因果增量。循环触点保留，未访问渠道转NULL且归因零。","direct_paths":sum(not j['path'] for j in journeys),"normalization":"相对移除效应除以全部渠道效应和，再分配观察到的全部转化；有直接路径时这会将直接转化也归一分配，需单独审阅。","engine":"sparse-fundamental-matrix-v1：一次稀疏LU分解求基本矩阵，解析式得到全部渠道移除概率，与逐渠道稠密重解等价（误差≤1e-9），不抽样、不截断小概率；转移明细以稀疏边存储，按来源分页读取，不传输完整方阵。","scale":{"channels":len(channels),"edges":int(matrix.nnz),"max_channels":settings.ATTRIBUTION_MAX_CHANNELS,"max_edges":settings.ATTRIBUTION_MAX_EDGES}}
