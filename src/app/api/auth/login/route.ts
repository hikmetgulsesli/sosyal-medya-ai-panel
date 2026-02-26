import { NextResponse } from "next/server";

// Mock auth API for development
// In production, this would proxy to the FastAPI backend

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { email, password } = body;

    // Mock validation
    if (!email || !password) {
      return NextResponse.json(
        { error: { code: "VALIDATION_ERROR", message: "Email and password are required" } },
        { status: 400 }
      );
    }

    // Mock successful login
    const mockUser = {
      id: "user-001",
      email,
      name: "Demo User",
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };

    const mockTokens = {
      accessToken: "mock-access-token-" + Date.now(),
      refreshToken: "mock-refresh-token-" + Date.now(),
      expiresIn: 86400,
    };

    return NextResponse.json({
      user: mockUser,
      tokens: mockTokens,
    });
  } catch {
    return NextResponse.json(
      { error: { code: "INTERNAL_ERROR", message: "An unexpected error occurred" } },
      { status: 500 }
    );
  }
}
