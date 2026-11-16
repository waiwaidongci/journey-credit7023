import {FormEvent,useEffect,useState} from 'react';import {getRunTransitions} from '../api/runs';import {TransitionPage} from '../types/domain';import {DataTable} from './common/DataTable';import {Notice} from './common/Notice';import {number} from '../utils/format';
const PER_PAGE=25;
export function TransitionBrowser({runId}:{runId:number}){
  const [page,setPage]=useState(1),[source,setSource]=useState(''),[input,setInput]=useState(''),[data,setData]=useState<TransitionPage|null>(null),[error,setError]=useState('');
  useEffect(()=>{let live=true;setError('');getRunTransitions(runId,page,PER_PAGE,source||undefined).then(d=>{if(live)setData(d)}).catch(e=>{if(live)setError(e.message)});return()=>{live=false}},[runId,page,source]);
  function jump(e:FormEvent){e.preventDefault();if(input.trim()){setPage(1);setSource(input.trim())}}
  return <div className="transition-browser">
    <Notice message={error}/>
    <div className="transition-controls">
      <span>共 {data?.total_sources??'…'} 个来源状态 / {data?.total_edges??'…'} 条非零转移边{!source&&data&&` · 第 ${data.page}/${data.pages} 页`}</span>
      {!source&&<span className="pager"><button className="outline" disabled={!data||page<=1} onClick={()=>setPage(p=>p-1)}>上一页</button><button className="outline" disabled={!data||page>=data.pages} onClick={()=>setPage(p=>p+1)}>下一页</button></span>}
      <form onSubmit={jump}><input aria-label="来源状态" value={input} onChange={e=>setInput(e.target.value)} placeholder="按来源状态查看，如 CH0001"/><button className="outline" type="submit">查看来源</button>{source&&<button type="button" className="text-link" onClick={()=>{setSource('');setInput('')}}>返回分页</button>}</form>
    </div>
    {source&&<p className="caption">仅展示来源 {source} 的出边明细。</p>}
    {data?.rows.map(row=><section className="transition-source" key={row.source}><h3 className="mono">FROM {row.source}<span>{row.edges.length} 条出边</span></h3><DataTable head={['TO','转移概率','观察计数']}>{row.edges.map(e=><tr key={e.target}><td className="mono">{e.target}</td><td className={e.probability>0?'matrix-nonzero':''}>{number(e.probability,6)}</td><td>{number(e.count,0)}</td></tr>)}</DataTable></section>)}
    {data&&!data.rows.length&&<p className="empty">该页无来源状态。</p>}
  </div>;
}
