import math
import numpy as np
from scipy.optimize import linprog

def optimize_budget(credits,budget,capacity_overrides=None):
    capacity_overrides=capacity_overrides or {}
    def valid(v,positive=False):return type(v) in (int,float) and abs(v)<=1e12 and math.isfinite(v) and (v>0 if positive else v>=0)
    if not valid(budget,True) or budget>1e7:raise ValueError("预算必须是(0,1e7]内有限数字")
    if not credits or len({c['code'] for c in credits})!=len(credits):raise ValueError("渠道得分为空或标识重复")
    codes=[c['code'] for c in credits]
    if set(capacity_overrides)-set(codes):raise ValueError("容量设置包含未知渠道")
    costs=[];scores=[];caps=[]
    for c in credits:
        cost,score,cap=c['unit_cost'],c['association_score'],c['capacity']
        if not valid(cost,True) or not valid(score) or not valid(cap):raise ValueError("成本须为正，得分与容量须为非负有限值")
        override=capacity_overrides.get(c['code'],cap)
        if not valid(override) or override>cap:raise ValueError("情景容量须非负且不超过渠道快照上限")
        costs.append(cost);scores.append(score);caps.append(override)
    if sum(scores)<=1e-12:raise ValueError("关联得分全零，不能生成有意义预算情景")
    solution=linprog(-np.array(scores),A_ub=[costs],b_ub=[budget],bounds=[(0,c) for c in caps],method='highs')
    if not solution.success:raise ValueError("预算约束求解失败："+solution.message)
    allocations=[max(0.,float(v)) for v in solution.x];spent=sum(x*c for x,c in zip(allocations,costs));objective=sum(x*s for x,s in zip(allocations,scores))
    if spent>budget+1e-6 or any(x>cap+1e-6 for x,cap in zip(allocations,caps)):raise ValueError("数值解违反预算或容量约束")
    rows=[{"code":c['code'],"name":c.get('name',c['code']),"allocation":x,"unit_cost":cost,"capacity":cap,"spend":x*cost,"association_score":score,"proxy_contribution":x*score,"share":c.get('share',0.)} for c,x,cost,cap,score in zip(credits,allocations,costs,caps,scores)]
    return {"allocations":rows,"budget":budget,"spent":spent,"unspent":max(0.,budget-spent),"objective":objective,"solver":"SciPy HiGHS linear program","assumptions":"目标=Σ历史归因转化/触点次数×情景触达单元；假设线性、得分不随投入改变、无渠道交互。仅为关联得分最大化，不预测真实转化或因果ROI。连续决策支持小数，未执行实际投放。"}
