import { request } from './api-client';
import { AuditEventItem, PaginatedResponse } from '@/types/api';

export const auditService = {
  listEvents: async (
    page = 1,
    pageSize = 20,
    search?: string,
    eventType?: string,
    actorType?: string
  ): Promise<PaginatedResponse<AuditEventItem>> => {
    let url = `audit/events?page=${page}&page_size=${pageSize}`;
    if (search) url += `&search=${encodeURIComponent(search)}`;
    if (eventType) url += `&event_type=${encodeURIComponent(eventType)}`;
    if (actorType) url += `&actor_type=${encodeURIComponent(actorType)}`;
    return request<PaginatedResponse<AuditEventItem>>(url);
  },
};
