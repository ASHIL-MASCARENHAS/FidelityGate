/**
 * Backend API Client & URL Configuration
 * 
 * Centralizes resolution of the FidelityGate Python/FastAPI backend URL across
 * local development and public production deployments (Render / Vercel).
 */

export function getBackendBaseUrl(): string {
  const apiUrl =
    process.env.FIDELITYGATE_API_URL ||
    process.env.FASTAPI_URL ||
    process.env.NEXT_PUBLIC_API_URL ||
    'http://127.0.0.1:8000';

  return apiUrl.replace(/\/+$/, '');
}

/**
 * Perform a server-side fetch to the FastAPI backend with error handling and cache disabling.
 */
export async function fetchBackend(
  endpoint: string,
  options: RequestInit = {}
): Promise<Response> {
  const baseUrl = getBackendBaseUrl();
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  const url = `${baseUrl}${cleanEndpoint}`;

  return fetch(url, {
    ...options,
    headers: {
      Accept: 'application/json',
      ...(options.headers || {}),
    },
    cache: 'no-store',
  });
}

