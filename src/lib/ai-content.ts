/** AI Content Generation API Client */

import type { 
  GenerateContentRequest, 
  GeneratedContent,
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
      error.error?.message || error.detail || `HTTP ${response.status}`,
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
  request: GenerateContentRequest,
  token?: string
): Promise<GeneratedContent> {
  // Determine the correct endpoint based on content type
  let endpoint: string;
  let body: Record<string, unknown>;
  
  if (request.contentType === 'hashtags') {
    endpoint = `${API_BASE}/suggest/hashtags`;
    body = {
      content: request.topic,
      count: 10,
    };
  } else if (request.contentType === 'thread') {
    endpoint = `${API_BASE}/generate/thread`;
    body = {
      topic: request.topic,
      tone: request.tone,
      num_posts: 5,
      context: request.maxLength ? `Max length: ${request.maxLength} characters` : undefined,
    };
  } else {
    endpoint = `${API_BASE}/generate/post`;
    body = {
      topic: request.topic,
      tone: request.tone,
      max_length: request.maxLength || 280,
      context: request.context,
    };
  }

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(endpoint, {
    method: 'POST',
    headers,
    body: JSON.stringify(body),
  });

  const data = await handleResponse<{
    content?: string;
    posts?: Array<{ number: number; content: string; char_count: number }>;
    hashtags?: string[];
    provider: { provider: string; model: string; tokens_used?: number };
    char_count?: number;
    total_posts?: number;
  }>(response);

  // Transform the response to match our GeneratedContent interface
  let finalContent: string;
  let finalHashtags: string[] | undefined;

  if (request.contentType === 'hashtags' && data.hashtags) {
    finalContent = data.hashtags.join(' ');
    finalHashtags = data.hashtags.map(h => h.replace(/^#/, ''));
  } else if (request.contentType === 'thread' && data.posts) {
    finalContent = data.posts.map((post, idx) => `${idx + 1}/${data.posts?.length}\n${post.content}`).join('\n\n');
  } else {
    finalContent = data.content || '';
  }

  return {
    id: Date.now().toString(),
    content: finalContent,
    platform: request.platform,
    tone: request.tone,
    contentType: request.contentType,
    hashtags: finalHashtags,
    createdAt: new Date().toISOString(),
  };
}

/**
 * Generate content with authentication
 */
export async function generateContentWithAuth(
  request: GenerateContentRequest,
  token: string
): Promise<GeneratedContent> {
  return generateContent(request, token);
}

/**
 * Save generated content to scheduler
 * Stores in localStorage for now (will be replaced with API call)
 */
export async function saveToScheduler(
  contentId: string,
  content: string,
  platform: string,
  scheduledAt?: string,
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  _token?: string
): Promise<{ success: boolean; scheduleId: string }> {
  // For now, store in localStorage as a mock scheduler
  const scheduledPosts = JSON.parse(
    localStorage.getItem("sma_scheduled_posts") || "[]"
  );

  const newPost = {
    id: contentId,
    content,
    platform,
    scheduledFor: scheduledAt || new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
    status: "draft",
    createdAt: new Date().toISOString(),
  };

  scheduledPosts.push(newPost);
  localStorage.setItem("sma_scheduled_posts", JSON.stringify(scheduledPosts));

  return { success: true, scheduleId: contentId };
}
