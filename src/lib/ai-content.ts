/** AI Content Generation API Client */

import type { 
  GenerateContentRequest, 
  GenerateContentResponse,
  GeneratedContent 
} from '@/types/ai-content.js';

const API_BASE = '/api/ai';

export class AIContentError extends Error {
  constructor(
    message: string, 
    public code: string, 
    public statusCode: number = 500
  ) {
    super(message);
    this.name = 'AIContentError';
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ 
      error: { message: 'An unexpected error occurred' } 
    }));
    throw new AIContentError(
      error.error?.message || `HTTP ${response.status}`,
      error.error?.code || 'UNKNOWN_ERROR',
      response.status
    );
  }
  return response.json() as Promise<T>;
}

/**
 * Generate AI-powered content
 */
export async function generateContent(
  request: GenerateContentRequest
): Promise<GeneratedContent> {
  const response = await fetch(`${API_BASE}/generate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  const data = await handleResponse<GenerateContentResponse>(response);
  return data.data;
}

/**
 * Generate content with token (authenticated)
 */
export async function generateContentWithAuth(
  request: GenerateContentRequest,
  token: string
): Promise<GeneratedContent> {
  const response = await fetch(`${API_BASE}/generate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify(request),
  });

  const data = await handleResponse<GenerateContentResponse>(response);
  return data.data;
}

/**
 * Save generated content to scheduler
 */
export async function saveToScheduler(
  contentId: string,
  scheduledAt?: string,
  token?: string
): Promise<{ success: boolean; scheduleId: string }> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}/schedule`, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      contentId,
      scheduledAt: scheduledAt || new Date(Date.now() + 3600000).toISOString(), // Default to 1 hour from now
    }),
  });

  return handleResponse<{ success: boolean; scheduleId: string }>(response);
}
