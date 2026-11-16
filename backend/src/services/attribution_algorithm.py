from .transition_algorithm import transition_matrix
from .absorbing_algorithm import absorption_probability,remove_to_null
from ..utils.fingerprint import fingerprint

def analyze_attribution(batch,journeys,channels):
    journeys=sorted(journeys,key=lambda j:j['code']);channels=sorted(channels,key=lambda c:c['code'])
    if len({j['code'] for j in journeys})!=len(journeys):raise ValueError("匿名路径编号重复")
    codes=[c['code'] for c in channels];states,counts,matrix=transition_matrix(journeys,codes)
    base=absorption_probability(matrix,states)
    if base<=1e-12:raise ValueError("基准转化概率为零，无法定义相对移除效应")
    total_conversions=sum(j['converted'] for j in journeys);credit=[]
    for c in channels:
        removed=absorption_probability(remove_to_null(matrix,states,c['code']),states)
        effect=max(0.,(base-removed)/base)
        touches=sum(j['path'].count(c['code']) for j in journeys)
        last=sum(j['converted'] and bool(j['path']) and j['path'][-1]==c['code'] for j in journeys)
        credit.append({**c,"removed_probability":removed,"removal_effect":effect,"touches":touches,"last_touch_conversions":last})
    total_effect=sum(c['removal_effect'] for c in credit)
    if total_effect<=1e-12:raise ValueError("所有渠道移除效应为零，不能归一归因")
    for c in credit:
        c['share']=c['removal_effect']/total_effect;c['credited_conversions']=c['share']*total_conversions
        c['association_score']=c['credited_conversions']/c['touches'] if c['touches'] else 0.
    info={"id":batch.id,"name":batch.name,"source":batch.source}
    return {"batch":info,"journey_count":len(journeys),"conversions":total_conversions,"base_probability":base,"states":states,"transition_counts":counts.tolist(),"transition_matrix":matrix.tolist(),"credits":credit,"input_hash":fingerprint({"method":"absorbing-null-removal-v1","batch":info,"journeys":journeys,"channels":channels}),"removal_policy":"所有指向被移除渠道的概率流量转入NULL；被移除渠道本身转NULL，不跨接路径，其他行保持和1。","assumptions":"一阶马尔可夫、观察期路径闭合且渠道定义一致；移除效应是关联模型，不是因果增量。循环触点保留，未访问渠道转NULL且归因零。","direct_paths":sum(not j['path'] for j in journeys),"normalization":"相对移除效应除以全部渠道效应和，再分配观察到的全部转化；有直接路径时这会将直接转化也归一分配，需单独审阅。"}
