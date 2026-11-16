import json,random
from src.config import settings
from src.config.database import Base,engine,SessionLocal
from src.models import Channel,JourneyBatch,Journey
from src.services.transition_algorithm import transition_counts_sparse,probabilities_csr

CHANNELS=2000;JOURNEYS=40000;ENTRY=2000;STEP=6;BATCH_NAME="巡光联展 · 两千渠道压力验证"

def seed():
    """按需生成两千渠道联展批次（默认不运行）：docker compose exec backend python -m scripts.seed_large

    环形邻接随机游走生成路径，非零转移边控制在规模上限内；只补缺失，不覆盖已有数据。
    """
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        for i in range(1,CHANNELS+1):
            code=f"CH{i:04}"
            if not db.query(Channel).filter_by(code=code).first():db.add(Channel(code=code,name=f"联展渠道{i:04}",unit_cost=round(4+(i*37%180)/10,1),capacity=float(200+i*13%400),description="联展两千渠道模拟成本与容量；仅供关联预算情景，不执行实际投放。"))
        db.flush()
        batch=db.query(JourneyBatch).filter_by(name=BATCH_NAME).first()
        if not batch:batch=JourneyBatch(name=BATCH_NAME,source="xg-expo-2000-channels.json",description="两千渠道联展匿名路径，保留循环与NULL终点，用于规模上限与分页验证。");db.add(batch);db.flush()
        existing=set(x[0] for x in db.query(Journey.code).filter_by(batch_id=batch.id))
        rng=random.Random(2000);journeys=[]
        for k in range(1,JOURNEYS+1):
            code=f"LG-{k:06}"
            if code in existing:continue
            cur=rng.randrange(ENTRY);path=[cur]
            for _ in range(rng.randint(1,5)):cur=(cur+1+rng.randrange(STEP))%CHANNELS;path.append(cur)
            journeys.append({"code":code,"path":[f"CH{c+1:04}" for c in path],"converted":rng.random()<.18,"note":"联展合成路径，触点顺序保留；终点根据预约观察窗口记录。"})
        states,counts=transition_counts_sparse(journeys,[f"CH{i:04}" for i in range(1,CHANNELS+1)])
        edges=probabilities_csr(states,counts).nnz
        if edges>settings.ATTRIBUTION_MAX_EDGES:raise SystemExit(f"生成非零转移边{edges}超过规模上限{settings.ATTRIBUTION_MAX_EDGES}")
        for i in range(0,len(journeys),5000):db.add_all([Journey(batch_id=batch.id,**j) for j in journeys[i:i+5000]]);db.flush()
        db.commit();print(json.dumps({"channels":CHANNELS,"journeys_added":len(journeys),"edges":edges,"max_edges":settings.ATTRIBUTION_MAX_EDGES},ensure_ascii=False))
if __name__=="__main__":seed()
