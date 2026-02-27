import { NextResponse } from "next/server";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:4522/api";

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { name, email, password, confirmPassword } = body;

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

    // Register user on backend
    const registerRes = await fetch(`${API_BASE_URL}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password, full_name: name }),
    });

    if (!registerRes.ok) {
      const err = await registerRes.json().catch(() => ({ detail: "Registration failed" }));
      return NextResponse.json(
        { error: { code: "AUTH_ERROR", message: err.detail || "Registration failed" } },
        { status: registerRes.status }
      );
    }

    const profile = await registerRes.json();

    // Auto-login after registration
    const loginRes = await fetch(`${API_BASE_URL}/auth/login/json`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });

    if (!loginRes.ok) {
      return NextResponse.json(
        { error: { code: "AUTH_ERROR", message: "Registered but auto-login failed. Please log in manually." } },
        { status: 500 }
      );
    }

    const tokens = await loginRes.json();

    return NextResponse.json({
      user: {
        id: profile.id,
        email: profile.email,
        name: profile.full_name || profile.email,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      },
      tokens: {
        accessToken: tokens.access_token,
        refreshToken: tokens.refresh_token,
        expiresIn: tokens.expires_in,
      },
    });
  } catch {
    return NextResponse.json(
      { error: { code: "INTERNAL_ERROR", message: "An unexpected error occurred" } },
      { status: 500 }
    );
  }
}
