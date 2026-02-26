/** AI Content Generation Types */

export type Platform = 'twitter' | 'linkedin' | 'instagram' | 'bluesky';
export type Tone = 'professional' | 'friendly' | 'funny' | 'casual' | 'formal';
export type ContentType = 'post' | 'thread' | 'hashtags';

export interface GenerateContentRequest {
  topic: string;
  tone: Tone;
  platform: Platform;
  contentType: ContentType;
  maxLength?: number;
  context?: string;
}

export interface GeneratedContent {
  id: string;
  content: string;
  platform: Platform;
  tone: Tone;
  contentType: ContentType;
  hashtags?: string[];
  createdAt: string;
}

export interface GenerateContentResponse {
  data: GeneratedContent;
}

export interface ContentFormData {
  topic: string;
  tone: Tone;
  platform: Platform;
  contentType: ContentType;
}

export const PLATFORM_OPTIONS: { value: Platform; label: string; icon: string }[] = [
  { value: 'twitter', label: 'Twitter/X', icon: 'Twitter' },
  { value: 'linkedin', label: 'LinkedIn', icon: 'Linkedin' },
  { value: 'instagram', label: 'Instagram', icon: 'Instagram' },
  { value: 'bluesky', label: 'Bluesky', icon: 'Cloud' },
];

export const TONE_OPTIONS: { value: Tone; label: string; description: string }[] = [
  { value: 'professional', label: 'Professional', description: 'Formal and business-oriented' },
  { value: 'friendly', label: 'Friendly', description: 'Warm and approachable' },
  { value: 'funny', label: 'Funny', description: 'Humorous and entertaining' },
  { value: 'casual', label: 'Casual', description: 'Relaxed and conversational' },
  { value: 'formal', label: 'Formal', description: 'Serious and authoritative' },
];

export const CONTENT_TYPE_OPTIONS: { value: ContentType; label: string; description: string }[] = [
  { value: 'post', label: 'Single Post', description: 'One standalone post' },
  { value: 'thread', label: 'Thread', description: 'Multiple connected posts' },
  { value: 'hashtags', label: 'Hashtags', description: 'Relevant hashtag suggestions' },
];
