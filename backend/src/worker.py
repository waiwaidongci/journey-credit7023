import json,time,traceback
from pathlib import Path
from .config.database import Base,engine,SessionLocal
from .models import AttributionRun,BudgetScenario,JourneyBatch
from .constants.status import RunStatus
from .services.run_service import queue
from .services.journey_service import list_journeys
from .services.channel_service import list_channels
from .services.compute_supervisor import run_attribution_supervised
from .services.budget_algorithm import optimize_budget
from .services.audit_service import log
from .utils.fingerprint import fingerprint
ARTIFACTS=Path("/artifacts")
def handle_job(kind,raw_id):
    with SessionLocal() as db:
        model=AttributionRun if kind=='run' else BudgetScenario
        row=db.get(model,int(raw_id))
        if not row or row.status!=RunStatus.QUEUED:return
        row.status=RunStatus.RUNNING;db.commit()
        try:
            if kind=='run':
                batch=db.get(JourneyBatch,row.batch_id)
                row.result=run_attribution_supervised(batch,list_journeys(db,batch.id),list_channels(db))
            else:
                run=db.get(AttributionRun,row.run_id);result=optimize_budget(run.result['credits'],row.budget,row.capacity_overrides)
                result['input_hash']=fingerprint({"method":"linear-association-budget-v1","attribution":run.result,"budget":row.budget,"capacity_overrides":row.capacity_overrides})
                result['attribution_hash']=run.result['input_hash'];row.result=result
            row.status=RunStatus.COMPLETED;ARTIFACTS.joinpath(f"{kind}-{row.id}.json").write_text(json.dumps(row.result,ensure_ascii=False));log(db,"worker",kind+".completed",row.id)
        except Exception as e:row.status=RunStatus.FAILED;row.error=str(e);traceback.print_exc()
        db.commit()

def main():
    Base.metadata.create_all(engine);ARTIFACTS.mkdir(exist_ok=True)
    while True:
        ARTIFACTS.joinpath("heartbeat").write_text(str(time.time()))
        job=queue.blpop("journey:jobs",timeout=2)
        if not job:continue
        kind,raw_id=job[1].split(':');handle_job(kind,raw_id)

if __name__=="__main__":main()
