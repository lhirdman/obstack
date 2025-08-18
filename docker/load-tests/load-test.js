// ObservaStack Load Test Suite
// Tests frontend and API performance under various load conditions

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('error_rate');
const responseTime = new Trend('response_time');
const requestCount = new Counter('request_count');

// Test configuration
export const options = {
  stages: [
    { duration: '2m', target: 10 }, // Ramp up to 10 users
    { duration: '5m', target: 10 }, // Stay at 10 users
    { duration: '2m', target: 20 }, // Ramp up to 20 users
    { duration: '5m', target: 20 }, // Stay at 20 users
    { duration: '2m', target: 0 },  // Ramp down to 0 users
  ],
  thresholds: {
    http_req_duration: ['p(95)<1000'], // 95% of requests must complete below 1s
    error_rate: ['rate<0.05'],         // Error rate must be below 5%
    http_req_failed: ['rate<0.05'],    // Failed requests must be below 5%
  },
};

// Environment variables
const FRONTEND_URL = __ENV.TARGET_URL || 'http://frontend-test:3000';
const API_URL = __ENV.API_URL || 'http://bff-test:8000';

// Test data
const testUsers = [
  { username: 'test-user-1', password: 'password123' },
  { username: 'test-user-2', password: 'password123' },
  { username: 'test-user-3', password: 'password123' },
];

const searchQueries = [
  'error rate',
  'cpu usage',
  'memory consumption',
  'response time',
  'database connection',
  'authentication failed',
  'service unavailable',
  'timeout',
];

// Helper function to authenticate and get token
function authenticate() {
  const loginPayload = {
    username: testUsers[Math.floor(Math.random() * testUsers.length)].username,
    password: 'password123',
  };

  const loginResponse = http.post(`${API_URL}/api/auth/login`, JSON.stringify(loginPayload), {
    headers: { 'Content-Type': 'application/json' },
  });

  if (loginResponse.status === 200) {
    const tokens = JSON.parse(loginResponse.body);
    return tokens.access_token;
  }
  
  return null;
}

// Test scenarios
export default function () {
  const token = authenticate();
  
  if (!token) {
    errorRate.add(1);
    return;
  }

  const headers = {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json',
  };

  // Test 1: Frontend health check
  const frontendHealthResponse = http.get(`${FRONTEND_URL}/health`);
  check(frontendHealthResponse, {
    'frontend health check status is 200': (r) => r.status === 200,
  });
  errorRate.add(frontendHealthResponse.status !== 200);
  responseTime.add(frontendHealthResponse.timings.duration);
  requestCount.add(1);

  sleep(1);

  // Test 2: API health check
  const apiHealthResponse = http.get(`${API_URL}/health`);
  check(apiHealthResponse, {
    'API health check status is 200': (r) => r.status === 200,
  });
  errorRate.add(apiHealthResponse.status !== 200);
  responseTime.add(apiHealthResponse.timings.duration);
  requestCount.add(1);

  sleep(1);

  // Test 3: User profile endpoint
  const profileResponse = http.get(`${API_URL}/api/auth/me`, { headers });
  check(profileResponse, {
    'user profile status is 200': (r) => r.status === 200,
    'user profile has required fields': (r) => {
      const profile = JSON.parse(r.body);
      return profile.id && profile.username && profile.tenant_id;
    },
  });
  errorRate.add(profileResponse.status !== 200);
  responseTime.add(profileResponse.timings.duration);
  requestCount.add(1);

  sleep(1);

  // Test 4: Search API
  const searchQuery = {
    freeText: searchQueries[Math.floor(Math.random() * searchQueries.length)],
    type: 'unified',
    timeRange: {
      start: new Date(Date.now() - 3600000).toISOString(), // 1 hour ago
      end: new Date().toISOString(),
    },
    limit: 50,
  };

  const searchResponse = http.post(`${API_URL}/api/search`, JSON.stringify(searchQuery), { headers });
  check(searchResponse, {
    'search status is 200': (r) => r.status === 200,
    'search returns results': (r) => {
      if (r.status === 200) {
        const results = JSON.parse(r.body);
        return results.items !== undefined;
      }
      return false;
    },
  });
  errorRate.add(searchResponse.status !== 200);
  responseTime.add(searchResponse.timings.duration);
  requestCount.add(1);

  sleep(2);

  // Test 5: Alerts endpoint
  const alertsResponse = http.get(`${API_URL}/api/alerts`, { headers });
  check(alertsResponse, {
    'alerts status is 200': (r) => r.status === 200,
    'alerts returns array': (r) => {
      if (r.status === 200) {
        const alerts = JSON.parse(r.body);
        return Array.isArray(alerts.alerts);
      }
      return false;
    },
  });
  errorRate.add(alertsResponse.status !== 200);
  responseTime.add(alertsResponse.timings.duration);
  requestCount.add(1);

  sleep(1);

  // Test 6: Frontend static assets (simulate user browsing)
  const staticAssetResponse = http.get(`${FRONTEND_URL}/`);
  check(staticAssetResponse, {
    'frontend loads successfully': (r) => r.status === 200,
    'frontend contains app div': (r) => r.body.includes('id="root"'),
  });
  errorRate.add(staticAssetResponse.status !== 200);
  responseTime.add(staticAssetResponse.timings.duration);
  requestCount.add(1);

  sleep(Math.random() * 3 + 1); // Random sleep between 1-4 seconds
}

// Setup function (runs once per VU)
export function setup() {
  console.log('Starting load test...');
  console.log(`Frontend URL: ${FRONTEND_URL}`);
  console.log(`API URL: ${API_URL}`);
  
  // Verify services are accessible
  const frontendCheck = http.get(`${FRONTEND_URL}/health`);
  const apiCheck = http.get(`${API_URL}/health`);
  
  if (frontendCheck.status !== 200) {
    console.error(`Frontend not accessible: ${frontendCheck.status}`);
  }
  
  if (apiCheck.status !== 200) {
    console.error(`API not accessible: ${apiCheck.status}`);
  }
  
  return {
    frontendHealthy: frontendCheck.status === 200,
    apiHealthy: apiCheck.status === 200,
  };
}

// Teardown function (runs once after all VUs finish)
export function teardown(data) {
  console.log('Load test completed');
  console.log(`Frontend was healthy: ${data.frontendHealthy}`);
  console.log(`API was healthy: ${data.apiHealthy}`);
}