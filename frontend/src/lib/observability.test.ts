import { describe, expect, it } from 'vitest';

import { buildIncidentLogHref, incidentStatusTone, mergeObservabilityLogs } from './observability';

describe('observability helpers', () => {
  it('merges live logs without duplicates and keeps newest first', () => {
    const merged = mergeObservabilityLogs(
      [
        {
          id: 'a',
          timestamp: '2026-03-17T10:00:00Z',
          level: 'INFO',
          logger_name: 'api.requests',
          source: 'api',
          message: 'older',
          event_code: 'http.request.completed',
          request_id: 'req-1',
          method: 'GET',
          path: '/health',
          status_code: 200,
          duration_ms: 10,
          user_id: null,
          ip_address: '127.0.0.1',
          user_agent: 'test',
          metadata: {},
        },
      ],
      [
        {
          id: 'b',
          timestamp: '2026-03-17T10:01:00Z',
          level: 'ERROR',
          logger_name: 'api.requests',
          source: 'api',
          message: 'newer',
          event_code: 'ops.request_error',
          request_id: 'req-2',
          method: 'GET',
          path: '/broken',
          status_code: 500,
          duration_ms: 42,
          user_id: null,
          ip_address: '127.0.0.1',
          user_agent: 'test',
          metadata: {},
        },
        {
          id: 'a',
          timestamp: '2026-03-17T10:00:00Z',
          level: 'INFO',
          logger_name: 'api.requests',
          source: 'api',
          message: 'older',
          event_code: 'http.request.completed',
          request_id: 'req-1',
          method: 'GET',
          path: '/health',
          status_code: 200,
          duration_ms: 10,
          user_id: null,
          ip_address: '127.0.0.1',
          user_agent: 'test',
          metadata: {},
        },
      ]
    );

    expect(merged.map((entry) => entry.id)).toEqual(['b', 'a']);
  });

  it('builds a direct log link from an incident', () => {
    expect(
      buildIncidentLogHref({
        id: 'incident-1',
        signal_type: 'auth.failed_login_burst',
        severity: 'high',
        status: 'open',
        title: 'Failed logins',
        summary: 'Repeated failures',
        fingerprint: 'fingerprint',
        occurrence_count: 3,
        first_seen_at: '2026-03-17T09:00:00Z',
        last_seen_at: '2026-03-17T10:00:00Z',
        actor_user_id: null,
        subject_user_id: null,
        ip_address: '127.0.0.1',
        related_log_id: 'log-1',
        metadata: {},
        review_notes: '',
        reviewed_by: null,
        reviewed_at: null,
      })
    ).toBe('/admin/logs?logId=log-1');
  });

  it('returns distinct tones for incident statuses', () => {
    expect(incidentStatusTone('open')).toContain('orange');
    expect(incidentStatusTone('acknowledged')).toContain('blue');
    expect(incidentStatusTone('resolved')).toContain('green');
  });
});
