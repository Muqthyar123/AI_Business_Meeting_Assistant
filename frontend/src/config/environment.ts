export const ENV = {
  API_BASE_URL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  ENABLE_DEMO_FALLBACK: import.meta.env.VITE_ENABLE_DEMO_FALLBACK !== 'false',
  APP_VERSION: '1.2.0',
  BUILD_DATE: '2026-10-09',
};
