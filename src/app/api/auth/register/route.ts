import { NextResponse } from "next/server";

// Mock register API for development
export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { name, email, password, confirmPassword } = body;

    // Mock validation
    if (!name || !email || !password) {
      return NextResponse.json(
        { error: { code: "VALIDATION_ERROR", message: "All fields are required" } },
        { status: 400 }
      );
    }

    if (password !== confirmPassword) {
      return NextResponse.json(
        { error: { code: "VALIDATION_ERROR", message: "Passwords do not match" } },
        { status: 400 }
      );
    }

    // Mock successful registration
    const mockUser = {
      id: "user-" + Date.now(),
      email,
      name,
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
