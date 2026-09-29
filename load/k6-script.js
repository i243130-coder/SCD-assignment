// CivicPulse Performance & Load Testing Suite
// Used for HPA validation (generating concurrent traffic to observe pod scale-out)
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '1m', target: 50 }, // ramp up to 50 VUs
    { duration: '2m', target: 50 }, // hold 50 VUs
    { duration: '30s', target: 0 }, // ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'], // 95% of requests must complete below 500ms
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

export default function () {
  // POST /api/complaints
  const payload = JSON.stringify({
    description: `Load test complaint ${__VU} ${__ITER}`,
    location: "Test Location",
  });
  
  const params = {
    headers: {
      'Content-Type': 'application/json',
    },
  };

  const postRes = http.post(`${BASE_URL}/api/complaints`, payload, params);
  check(postRes, {
    'post complaint status is 201 or 200': (r) => r.status === 201 || r.status === 200,
  });

  // GET /api/complaints
  const getComplaintsRes = http.get(`${BASE_URL}/api/complaints`);
  check(getComplaintsRes, {
    'get complaints status is 200': (r) => r.status === 200,
  });

  // GET /api/stats
  const getStatsRes = http.get(`${BASE_URL}/api/stats`);
  check(getStatsRes, {
    'get stats status is 200': (r) => r.status === 200,
  });

  sleep(1);
}
