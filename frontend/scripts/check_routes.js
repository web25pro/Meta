// Simple route checker script
// Usage: node scripts/check_routes.js <baseUrl>

const baseUrl = process.argv[2] || 'http://localhost:3001';
const routes = [
  '/',
  '/auth/login',
  '/auth/register',
  '/auth/check-email',
  '/auth/password-reset',
  '/auth/password-reset-confirm',
  '/auth/resend-verification',
  '/auth/verify-email',
  '/dashboard',
  '/dashboard/community/profile',
  '/dashboard/community/referrals',
  '/dashboard/community/settings',
];

(async () => {
  console.log(`Checking ${routes.length} routes on ${baseUrl}`);
  for (const route of routes) {
    const url = new URL(route, baseUrl).toString();
    try {
      const res = await fetch(url, { method: 'GET' });
      const ct = res.headers.get('content-type') || '';
      const text = await res.text();
      console.log(`${route} -> ${res.status} ${res.statusText} (${ct}) body:${text.length} chars`);
      if (res.status >= 400) {
        console.log(`  ERROR: ${route} returned ${res.status}`);
      }
    } catch (err) {
      console.log(`${route} -> NETWORK ERROR: ${err.message}`);
    }
  }
})();
