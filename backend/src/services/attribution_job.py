import json,sys

def main():
    """独立进程执行归因计算：python -m src.services.attribution_job job.json out.json

    父进程在此进程上施加内存与墙钟时限；任何失败只写错误信封，不产出部分结果。
    """
    job_path,out_path=sys.argv[1],sys.argv[2]
    try:
        with open(job_path) as f:job=json.load(f)
        from types import SimpleNamespace
        from .attribution_algorithm import analyze_attribution
        result=analyze_attribution(SimpleNamespace(**job['batch']),job['journeys'],job['channels'])
        envelope={"ok":True,"result":result}
    except MemoryError:
        envelope={"ok":False,"error":"归因计算内存超出上限，已明确拒绝，不发布部分结果"}
    except Exception as e:
        envelope={"ok":False,"error":str(e)}
    with open(out_path,"w") as f:json.dump(envelope,f,ensure_ascii=False)

if __name__=="__main__":main()
