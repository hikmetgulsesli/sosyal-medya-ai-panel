import type { AnalyticsOverview } from '@/types/analytics';

export interface AnalyticsApiError {
  message: string;
  code?: string;
}

export async function fetchAnalyticsOverview(
  token: string,
  days: number = 30
): Promise<AnalyticsOverview> {
  const response = await fetch(
    `/api/analytics/overview?days=${days}`,
    {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    }
  );

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw {
      message: errorData.message || errorData.error?.message || `HTTP error! status: ${response.status}`,
      code: errorData.code || 'UNKNOWN_ERROR',
    } as AnalyticsApiError;
  }

  return response.json();
}
