import {request} from './client';import {Channel} from '../types/domain';export const getChannels=()=>request<Channel[]>('/channels');
