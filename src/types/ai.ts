// AI Content Generation Types

export interface GeneratePostRequest {
  topic: string;
  tone?: string;
  max_length?: number;
  context?: string;
  template_id?: string;
}

export interface GenerateThreadRequest {
  topic: string;
  tone?: string;
  num_posts?: number;
  context?: string;
  template_id?: string;
}

export interface SuggestHashtagsRequest {
  content: string;
  count?: number;
}

export interface AIProviderInfo {
  provider: string;
  model: string;
  tokens_used?: number;
}

export interface GeneratePostResponse {
  content: string;
  provider: AIProviderInfo;
  char_count: number;
  estimated_read_time: string;
}

export interface ThreadPost {
  number: number;
  content: string;
  char_count: number;
}

export interface GenerateThreadResponse {
  posts: ThreadPost[];
  provider: AIProviderInfo;
  total_posts: number;
}

export interface SuggestHashtagsResponse {
  hashtags: string[];
  provider: AIProviderInfo;
}

export interface AIServiceStatus {
  primary_provider: string;
  primary_available: boolean;
  fallback_provider: string;
  fallback_available: boolean;
  status: 'ready' | 'fallback' | 'unavailable';
}

export type ContentType = 'post' | 'thread' | 'hashtags' | 'images';
export type Platform = 'twitter' | 'linkedin' | 'instagram' | 'bluesky';

export interface GenerationState {
  contentType: ContentType;
  platform: Platform;
  topic: string;
  tone: string;
  isLoading: boolean;
  error: string | null;
  result: GeneratePostResponse | GenerateThreadResponse | SuggestHashtagsResponse | null;
}
