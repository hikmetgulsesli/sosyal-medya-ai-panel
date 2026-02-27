import { NextResponse } from "next/server";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:4522/api";

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { email, password } = body;

    if (!email || !password) {
      return NextResponse.json(
        { error: { code: "VALIDATION_ERROR", message: "Email and password are required" } },
        { status: 400 }
      );
    }

    // Call backend JSON login endpoint
    const backendRes = await fetch(`${API_BASE_URL}/auth/login/json`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });

    if (!backendRes.ok) {
      const err = await backendRes.json().catch(() => ({ detail: "Login failed" }));
      return NextResponse.json(
        { error: { code: "AUTH_ERROR", message: err.detail || "Invalid credentials" } },
        { status: backendRes.status }
      );
    }

    const data = await backendRes.json();

    // Fetch user profile with the new token
    const meRes = await fetch(`${API_BASE_URL}/auth/me`, {
      headers: { Authorization: `Bearer ${data.access_token}` },
    });

    let user = { id: "", email, name: "", createdAt: new Date().toISOString(), updatedAt: new Date().toISOString() };
    if (meRes.ok) {
      const profile = await meRes.json();
      user = {
        id: profile.id,
        email: profile.email,
        name: profile.full_name || profile.email,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      };
    }

    return NextResponse.json({
      user,
      tokens: {
        accessToken: data.access_token,
        refreshToken: data.refresh_token,
        expiresIn: data.expires_in,
      },
    });
  } catch {
    return NextResponse.json(
      { error: { code: "INTERNAL_ERROR", message: "An unexpected error occurred" } },
      { status: 500 }
    );
  }
}
