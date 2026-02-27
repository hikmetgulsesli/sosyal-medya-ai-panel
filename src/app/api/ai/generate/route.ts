import { NextResponse } from "next/server";
import type { GeneratePostRequest, GenerateThreadRequest } from "@/types/ai.js";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:4522/api";

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { contentType, platform, topic, tone, max_length, context, num_posts } = body;

    // Get auth token from request headers
    const authHeader = request.headers.get("authorization");
    if (!authHeader) {
      return NextResponse.json(
        { error: { code: "UNAUTHORIZED", message: "Authentication required" } },
        { status: 401 }
      );
    }

    // Determine which backend endpoint to call based on content type
    let endpoint: string;
    let payload: GeneratePostRequest | GenerateThreadRequest;

    switch (contentType) {
      case "thread":
        endpoint = "/ai/generate/thread";
        payload = {
          topic,
          tone: tone || "professional",
          num_posts: num_posts || 5,
          context: context || undefined,
        };
        break;
      case "post":
      default:
        endpoint = "/ai/generate/post";
        payload = {
          topic,
          tone: tone || "professional",
          max_length: max_length || getDefaultMaxLength(platform),
          context: context || undefined,
        };
        break;
    }

    // Call the backend API
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": authHeader,
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({
        detail: "An error occurred while generating content",
      }));
      return NextResponse.json(
        { error: { code: "GENERATION_ERROR", message: errorData.detail || "Generation failed" } },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("AI generation error:", error);
    return NextResponse.json(
      { error: { code: "INTERNAL_ERROR", message: "An unexpected error occurred" } },
      { status: 500 }
    );
  }
}

function getDefaultMaxLength(platform: string): number {
  switch (platform) {
    case "twitter":
      return 280;
    case "linkedin":
      return 3000;
    case "instagram":
      return 2200;
    case "bluesky":
      return 300;
    default:
      return 280;
  }
}
