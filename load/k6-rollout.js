// Zero-downtime rollout test (bonus). Holds a steady request rate through the
// Ingress while `kubectl rollout restart` replaces every pod, and FAILS if
// even one request fails: http_req_failed must be exactly 0.
//
// Go through the Ingress (k3d load balancer on :8080), not a port-forward:
// a port-forward pins one pod, and that pod is exactly what a rollout kills.
//
//   k6 run -e BASE_URL=http://localhost:8080 load/k6-rollout.js
// or let ops/zero-downtime-demo.ps1 drive it together with the rollout.
import http from 'k6/http';
import { check } from 'k6';

export const options = {
  scenarios: {
    steady: {
      executor: 'constant-arrival-rate',
      rate: Number(__ENV.RATE || 20), // iterations per second (3 requests each)
      timeUnit: '1s',
      duration: __ENV.DURATION || '2m',
      preAllocatedVUs: 20,
      maxVUs: 100,
    },
  },
  thresholds: {
    http_req_failed: ['rate==0'], // the zero-downtime claim, enforced
    checks: ['rate==1'],
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8080';
// The Ingress routes on host civicpulse.local; sending the Host header avoids
// editing the hosts file.
const params = { headers: { Host: __ENV.HOST_HEADER || 'civicpulse.local' } };

export default function () {
  const list = http.get(`${BASE_URL}/api/complaints?page=1&page_size=5`, params);
  check(list, { 'GET /api/complaints is 200': (r) => r.status === 200 });

  const ready = http.get(`${BASE_URL}/ready`, params);
  check(ready, { 'GET /ready is 200': (r) => r.status === 200 });

  const ui = http.get(`${BASE_URL}/`, params);
  check(ui, { 'GET / (frontend) is 200': (r) => r.status === 200 });
}
