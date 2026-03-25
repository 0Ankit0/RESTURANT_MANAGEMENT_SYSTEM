import type { ObservabilityLogEntry, SecurityIncident } from '@/types/observability';

export function mergeObservabilityLogs(
  existing: ObservabilityLogEntry[],
  incoming: ObservabilityLogEntry[],
  limit = 200
): ObservabilityLogEntry[] {
  const byId = new Map(existing.map((entry) => [entry.id, entry]));
  for (const entry of incoming) {
    byId.set(entry.id, entry);
  }
  return Array.from(byId.values())
    .sort((left, right) => right.timestamp.localeCompare(left.timestamp))
    .slice(0, limit);
}

export function logLevelTone(level: string): string {
  switch (level.toUpperCase()) {
    case 'ERROR':
      return 'bg-red-50 text-red-700 border border-red-200';
    case 'WARNING':
      return 'bg-yellow-50 text-yellow-800 border border-yellow-200';
    default:
      return 'bg-blue-50 text-blue-700 border border-blue-200';
  }
}

export function incidentSeverityTone(severity: string): string {
  switch (severity) {
    case 'high':
      return 'bg-red-50 text-red-700 border border-red-200';
    case 'medium':
      return 'bg-yellow-50 text-yellow-800 border border-yellow-200';
    default:
      return 'bg-blue-50 text-blue-700 border border-blue-200';
  }
}

export function incidentStatusTone(status: string): string {
  switch (status) {
    case 'resolved':
      return 'bg-green-50 text-green-700 border border-green-200';
    case 'acknowledged':
      return 'bg-blue-50 text-blue-700 border border-blue-200';
    default:
      return 'bg-orange-50 text-orange-800 border border-orange-200';
  }
}

export function buildIncidentLogHref(incident: SecurityIncident): string {
  const params = new URLSearchParams();
  if (incident.related_log_id) {
    params.set('logId', incident.related_log_id);
  } else if (incident.signal_type) {
    params.set('search', incident.signal_type);
  }
  const query = params.toString();
  return query ? `/admin/logs?${query}` : '/admin/logs';
}
