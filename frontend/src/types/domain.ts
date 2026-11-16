export interface User{name:string;email:string;role:string}
export interface Batch{id:number;name:string;source:string;description:string;journey_count:number;conversions:number}
export interface Journey{id:number;code:string;batch_id:number;path:string[];converted:boolean;note:string}
export interface Channel{id:number;code:string;name:string;unit_cost:number;capacity:number;description:string}
export interface Credit extends Channel{share:number;credited_conversions:number;removal_effect:number;removed_probability:number;touches:number;last_touch_conversions:number;association_score:number}
export interface TransitionEdge{source:string;target:string;probability:number;count:number}
export interface AttributionResult{batch:Batch;journey_count:number;conversions:number;base_probability:number;states:string[];transition_counts?:number[][];transition_matrix?:number[][];transition_edges?:TransitionEdge[];credits:Credit[];input_hash:string;removal_policy:string;assumptions:string;normalization:string;direct_paths:number;engine?:string;scale?:{channels:number;edges:number;max_channels:number;max_edges:number}}
export interface TransitionRow{source:string;edges:{target:string;probability:number;count:number}[]}
export interface TransitionPage{run_id:number;page:number;per_page:number;pages:number;total_sources:number;total_edges:number;rows:TransitionRow[]}
export interface Run{id:number;name:string;batch_id:number;status:string;result:AttributionResult;error:string;owner:string;created_at:string}
export interface Allocation{code:string;name:string;allocation:number;unit_cost:number;capacity:number;spend:number;association_score:number;proxy_contribution:number;share:number}
export interface Scenario{id:number;name:string;run_id:number;budget:number;capacity_overrides:Record<string,number>;status:string;review_status:string;result:{allocations:Allocation[];budget:number;spent:number;unspent:number;objective:number;solver:string;assumptions:string;input_hash:string;attribution_hash:string};error:string;owner:string;reviewer:string;review_note:string;created_at:string}
export interface Audit{id:number;actor:string;action:string;target:string;created_at:string}
