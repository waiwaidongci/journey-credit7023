import json,os,resource,subprocess,sys,tempfile,time
from pathlib import Path
from ..config import settings

BACKEND_ROOT=Path(__file__).resolve().parents[2]

def _peak_rss_mib(pid):
    try:
        with open(f"/proc/{pid}/status") as f:
            for line in f:
                if line.startswith("VmHWM"):return int(line.split()[1])/1024
    except OSError:pass
    return 0.

def run_attribution_supervised(batch,journeys,channels):
    """在独立子进程中执行归因计算，硬约束：峰值内存≤配置上限、墙钟≤配置时限。

    超出内存或时限立即终止并明确拒绝；子进程校验失败同样拒绝。任何情况下
    都不向调用方返回部分结果——要么完整结果字典，要么抛出ValueError。
    """
    time_limit=settings.ATTRIBUTION_TIME_LIMIT_S;mem_limit=settings.ATTRIBUTION_MEMORY_LIMIT_MIB
    payload={"batch":{"id":batch.id,"name":batch.name,"source":batch.source},"journeys":journeys,"channels":channels}
    work=Path(tempfile.mkdtemp(prefix="attribution-job-"));job_path=work/"job.json";out_path=work/"out.json"
    try:
        job_path.write_text(json.dumps(payload,ensure_ascii=False))
        env=dict(os.environ);env["PYTHONPATH"]=str(BACKEND_ROOT)+os.pathsep+env.get("PYTHONPATH","")
        # 稀疏LU为单线程负载；限制BLAS线程，避免线程栈挤占RLIMIT_DATA并触发OpenBLAS重试空转
        for var in ("OPENBLAS_NUM_THREADS","OMP_NUM_THREADS","MKL_NUM_THREADS","NUMEXPR_NUM_THREADS"):env[var]="1"
        def apply_memory_limit():
            limit=mem_limit*1024*1024
            resource.setrlimit(resource.RLIMIT_DATA,(limit,limit))
        proc=subprocess.Popen([sys.executable,"-m","src.services.attribution_job",str(job_path),str(out_path)],cwd=str(BACKEND_ROOT),env=env,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,preexec_fn=apply_memory_limit,text=True)
        deadline=time.monotonic()+time_limit
        while proc.poll() is None:
            if time.monotonic()>deadline:
                proc.kill();proc.wait()
                raise ValueError(f"归因计算超过{time_limit}秒时限，已明确拒绝并终止，不发布部分结果")
            if _peak_rss_mib(proc.pid)>mem_limit:
                proc.kill();proc.wait()
                raise ValueError(f"归因计算峰值内存超过{mem_limit}MiB上限，已明确拒绝并终止，不发布部分结果")
            time.sleep(0.2)
        if not out_path.exists():
            tail=(proc.stderr.read() if proc.stderr else "")[-300:].strip()
            raise ValueError("归因计算进程异常退出，已明确拒绝，不发布部分结果"+("："+tail if tail else ""))
        envelope=json.loads(out_path.read_text())
        if not envelope.get("ok"):raise ValueError(envelope.get("error") or "归因计算失败，已明确拒绝")
        return envelope["result"]
    finally:
        for path in (job_path,out_path):
            try:path.unlink()
            except OSError:pass
        try:work.rmdir()
        except OSError:pass
