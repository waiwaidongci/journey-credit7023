import random,json
from src.config.database import Base,engine,SessionLocal
from src.models import User,Channel,JourneyBatch,Journey,AttributionRun,BudgetScenario
from src.utils.security import hash_password
from src.utils.fingerprint import fingerprint
from src.services.journey_service import list_journeys
from src.services.channel_service import list_channels
from src.services.attribution_algorithm import analyze_attribution
from src.services.budget_algorithm import optimize_budget

def seed():
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        for role,name in [("admin","陈照 · 传播负责人"),("analyst","许晴 · 路径研究员"),("viewer","闻溪 · 策展阅读者")]:
            email=role+"@xunguang.demo"
            if not db.query(User).filter_by(email=email).first():db.add(User(email=email,name=name,role=role,password_hash=hash_password("Xunguang2026!")))
        definitions=[('POSTER','城市海报',12.,500.),('NEWSLETTER','策展通讯',8.,450.),('CREATOR','创作者推荐',18.,350.),('SEARCH','主动检索',22.,600.),('COMMUNITY','社群分享',6.,400.),('PARTNER','合作场馆',15.,300.)]
        for code,name,cost,cap in definitions:
            if not db.query(Channel).filter_by(code=code).first():db.add(Channel(code=code,name=name,unit_cost=cost,capacity=cap,description="模拟每触达单元成本与容量；仅供关联预算情景，不执行实际投放。"))
        db.flush();codes=[c[0] for c in definitions];rng=random.Random(89);index=0;batches=[]
        for name,n in [('巡光秋展 · 首周路径',700),('巡光秋展 · 第二周路径',400)]:
            batch=db.query(JourneyBatch).filter_by(name=name).first()
            if not batch:batch=JourneyBatch(name=name,source="xg-exhibition-paths.json",description="匿名预约触点路径，保留循环与未转化终点；移除渠道时概率流量转NULL。");db.add(batch);db.flush()
            existing=set(x[0] for x in db.query(Journey.code).filter_by(batch_id=batch.id))
            for i in range(n):
                index+=1;code=f"XG-{index:05}";path=rng.choices(codes,weights=[18,15,12,15,22,9],k=rng.randint(1,5))
                if index%9==0 and len(path)>1:path.append(path[0])
                converted=rng.random()<(.12+.1*('SEARCH' in path)+.09*('PARTNER' in path)+.07*('NEWSLETTER' in path)+.04*('COMMUNITY' in path))
                if code not in existing:db.add(Journey(code=code,batch_id=batch.id,path=path,converted=converted,note="匿名合成路径，触点顺序保留；终点根据预约观察窗口记录。"))
            db.flush();batches.append(batch)
        if not db.query(AttributionRun).filter_by(name="秋展首周 · 归因基准").first():
            batch=batches[0];result=analyze_attribution(batch,list_journeys(db,batch.id),list_channels(db))
            run=AttributionRun(name="秋展首周 · 归因基准",batch_id=batch.id,status="completed",result=result,owner="许晴 · 路径研究员");db.add(run);db.flush()
            scenario_result=optimize_budget(result['credits'],5000.,{})
            scenario_result['input_hash']=fingerprint({"method":"linear-association-budget-v1","attribution":result,"budget":5000.,"capacity_overrides":{}});scenario_result['attribution_hash']=result['input_hash']
            db.add(BudgetScenario(name="首周五千元讨论情景",run_id=run.id,budget=5000.,capacity_overrides={},status="completed",review_status="approved",result=scenario_result,owner="许晴 · 路径研究员",reviewer="陈照 · 传播负责人",review_note="批准研究情景归档；关联得分不是因果ROI，不代表真实预约预测，不自动投放。"))
        db.commit();print(json.dumps({m.__tablename__:db.query(m).count() for m in [User,Channel,JourneyBatch,Journey,AttributionRun,BudgetScenario]},ensure_ascii=False))
if __name__=="__main__":seed()
