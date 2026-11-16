import {request} from './client';import {Batch} from '../types/domain';export const getBatches=()=>request<Batch[]>('/batches');
