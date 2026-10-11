import { ApiResponse } from '@/types/api';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export class ApiClientError extends Error {
  public code: string;
  public details?: unknown;
  public statusCode?: number;

  constructor(message: string, code: string = 'CLIENT_ERROR', statusCode?: number, details?: unknown) {
    super(message);
    this.name = 'ApiClientError';
    this.code = code;
    this.statusCode = statusCode;
    this.details = details;
  }
}

interface RequestOptions extends RequestInit {
  timeoutMs?: number;
}

export async function request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const { timeoutMs = 8000, ...customConfig } = options;

  const url = `${API_BASE_URL.replace(/\/$/, '')}/${endpoint.replace(/^\//, '')}`;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  let authToken: string | null = null;
  try {
    authToken = sessionStorage.getItem('reconpilot_auth_token');
  } catch {
    // SessionStorage may be restricted in some environments
  }

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    Accept: 'application/json',
    ...(authToken ? { Authorization: `Bearer ${authToken}` } : {}),
    ...((customConfig.headers as Record<string, string>) || {}),
  };

  try {
    const response = await fetch(url, {
      ...customConfig,
      headers,
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    const json: ApiResponse<T> = await response.json().catch(() => ({
      success: false,
      error: {
        code: 'INVALID_JSON_RESPONSE',
        message: `Backend returned non-JSON response with HTTP ${response.status}`,
      },
    }));

    if (!response.ok || !json.success) {
      throw new ApiClientError(
        json.error?.message || `Request failed with HTTP status ${response.status}`,
        json.error?.code || `HTTP_${response.status}`,
        response.status,
        json.error?.details
      );
    }

    if (json.data === undefined) {
      throw new ApiClientError('Response payload is missing data object.', 'EMPTY_DATA_RESPONSE');
    }

    return json.data;
  } catch (err: unknown) {
    clearTimeout(timeoutId);

    if (err instanceof ApiClientError) {
      throw err;
    }

    if (err instanceof DOMException && err.name === 'AbortError') {
      throw new ApiClientError(
        `Request to ${endpoint} timed out after ${timeoutMs}ms.`,
        'REQUEST_TIMEOUT'
      );
    }

    const message = err instanceof Error ? err.message : 'Unknown network failure';
    throw new ApiClientError(
      `Network error connecting to API: ${message}`,
      'NETWORK_FAILURE'
    );
  }
}
