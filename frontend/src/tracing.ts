// Browser side of the frontend -> backend -> LLM trace.
//
// Every API call gets a W3C `traceparent` header, so the backend's FastAPI
// span (and its triage + LLM child spans) join the same trace. The browser's
// own CLIENT span is exported as OTLP/JSON to /api/telemetry/traces, a
// same-origin relay in the backend that forwards to the collector. That keeps
// the collector off the public network and avoids CORS.
//
// Zero dependencies on purpose: the OpenTelemetry web SDK would add ~100 kB
// to a small SPA for the one span type we need.

const SERVICE_NAME = 'civicpulse-frontend';
const EXPORT_URL = '/api/telemetry/traces';
const FLUSH_DELAY_MS = 2000;
const MAX_BATCH = 50;

// Vitest runs with MODE === 'test': no exporting, so no stray network calls.
const exportEnabled = import.meta.env.MODE !== 'test';

type AttrValue = string | number | boolean;

export interface FinishedSpan {
  traceId: string;
  spanId: string;
  name: string;
  startTimeUnixNano: string;
  endTimeUnixNano: string;
  attributes: Record<string, AttrValue>;
  error: boolean;
}

const queue: FinishedSpan[] = [];
let flushTimer: ReturnType<typeof setTimeout> | null = null;

function randomHex(bytes: number): string {
  const buf = new Uint8Array(bytes);
  crypto.getRandomValues(buf);
  return Array.from(buf, (b) => b.toString(16).padStart(2, '0')).join('');
}

/** 16-byte trace id / 8-byte span id, never all-zero (invalid per W3C). */
export function newTraceId(): string {
  const id = randomHex(16);
  return /^0+$/.test(id) ? newTraceId() : id;
}

export function newSpanId(): string {
  const id = randomHex(8);
  return /^0+$/.test(id) ? newSpanId() : id;
}

/** W3C Trace Context header: version-traceid-spanid-flags (01 = sampled). */
export function buildTraceparent(traceId: string, spanId: string): string {
  return `00-${traceId}-${spanId}-01`;
}

/** Wall-clock time in nanoseconds as a decimal string (OTLP/JSON uint64). */
function nowUnixNano(): string {
  const micros = Math.round((performance.timeOrigin + performance.now()) * 1000);
  return (BigInt(micros) * 1000n).toString();
}

function toOtlpValue(v: AttrValue) {
  if (typeof v === 'boolean') return { boolValue: v };
  if (typeof v === 'number') return Number.isInteger(v) ? { intValue: String(v) } : { doubleValue: v };
  return { stringValue: v };
}

/** Wrap finished spans in an OTLP/JSON ExportTraceServiceRequest. */
export function toOtlpPayload(spans: FinishedSpan[]) {
  return {
    resourceSpans: [
      {
        resource: {
          attributes: [{ key: 'service.name', value: { stringValue: SERVICE_NAME } }],
        },
        scopeSpans: [
          {
            scope: { name: 'civicpulse-frontend/tracing' },
            spans: spans.map((s) => ({
              traceId: s.traceId,
              spanId: s.spanId,
              name: s.name,
              kind: 3, // SPAN_KIND_CLIENT
              startTimeUnixNano: s.startTimeUnixNano,
              endTimeUnixNano: s.endTimeUnixNano,
              attributes: Object.entries(s.attributes).map(([key, value]) => ({ key, value: toOtlpValue(value) })),
              status: { code: s.error ? 2 : 1 }, // ERROR : OK
            })),
          },
        ],
      },
    ],
  };
}

async function flush(): Promise<void> {
  flushTimer = null;
  if (queue.length === 0) return;
  const batch = queue.splice(0, MAX_BATCH);
  try {
    // Plain fetch (not tracedFetch): exporting must not create spans itself.
    await fetch(EXPORT_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(toOtlpPayload(batch)),
      keepalive: true,
    });
  } catch {
    // Telemetry is best-effort; never surface it to the user.
  }
  if (queue.length > 0) scheduleFlush();
}

function scheduleFlush(): void {
  if (!exportEnabled || flushTimer !== null) return;
  flushTimer = setTimeout(() => void flush(), FLUSH_DELAY_MS);
}

function record(span: FinishedSpan): void {
  if (!exportEnabled) return;
  queue.push(span);
  if (queue.length >= MAX_BATCH) void flush();
  else scheduleFlush();
}

/**
 * fetch() that starts a trace: sends `traceparent` and records a CLIENT span
 * named e.g. "POST /api/complaints" covering the whole round trip.
 */
export async function tracedFetch(url: string, init: RequestInit = {}): Promise<Response> {
  const traceId = newTraceId();
  const spanId = newSpanId();
  const method = (init.method ?? 'GET').toUpperCase();
  const path = url.split('?')[0];
  const headers = new Headers(init.headers);
  headers.set('traceparent', buildTraceparent(traceId, spanId));

  const start = nowUnixNano();
  const attributes: Record<string, AttrValue> = {
    'http.request.method': method,
    'url.path': path,
  };
  try {
    const response = await fetch(url, { ...init, headers });
    attributes['http.response.status_code'] = response.status;
    record({ traceId, spanId, name: `${method} ${path}`, startTimeUnixNano: start, endTimeUnixNano: nowUnixNano(), attributes, error: response.status >= 500 });
    return response;
  } catch (err) {
    attributes['error.type'] = err instanceof Error ? err.name : 'Error';
    record({ traceId, spanId, name: `${method} ${path}`, startTimeUnixNano: start, endTimeUnixNano: nowUnixNano(), attributes, error: true });
    throw err;
  }
}
