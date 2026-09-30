import { describe, it, expect, vi, afterEach } from 'vitest';
import { buildTraceparent, newSpanId, newTraceId, toOtlpPayload, tracedFetch } from '../src/tracing';

describe('tracing', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('generates W3C-valid trace and span ids', () => {
    const traceId = newTraceId();
    const spanId = newSpanId();
    expect(traceId).toMatch(/^[0-9a-f]{32}$/);
    expect(spanId).toMatch(/^[0-9a-f]{16}$/);
    expect(traceId).not.toMatch(/^0+$/);
    expect(buildTraceparent(traceId, spanId)).toBe(`00-${traceId}-${spanId}-01`);
  });

  it('sends a traceparent header on API calls', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response('{}', { status: 200 }));
    vi.stubGlobal('fetch', fetchMock);

    await tracedFetch('/api/complaints?page=1', { method: 'POST', headers: { 'Content-Type': 'application/json' } });

    const init = fetchMock.mock.calls[0][1] as RequestInit;
    const headers = new Headers(init.headers);
    expect(headers.get('traceparent')).toMatch(/^00-[0-9a-f]{32}-[0-9a-f]{16}-01$/);
    expect(headers.get('Content-Type')).toBe('application/json');
    expect(init.method).toBe('POST');
  });

  it('builds an OTLP/JSON export request', () => {
    const payload = toOtlpPayload([
      {
        traceId: 'a'.repeat(32),
        spanId: 'b'.repeat(16),
        name: 'POST /api/complaints',
        startTimeUnixNano: '1000',
        endTimeUnixNano: '2000',
        attributes: { 'http.response.status_code': 201, 'url.path': '/api/complaints' },
        error: false,
      },
    ]);
    const resource = payload.resourceSpans[0];
    expect(resource.resource.attributes[0]).toEqual({ key: 'service.name', value: { stringValue: 'civicpulse-frontend' } });
    const span = resource.scopeSpans[0].spans[0];
    expect(span.kind).toBe(3);
    expect(span.status.code).toBe(1);
    expect(span.attributes).toContainEqual({ key: 'http.response.status_code', value: { intValue: '201' } });
  });
});
