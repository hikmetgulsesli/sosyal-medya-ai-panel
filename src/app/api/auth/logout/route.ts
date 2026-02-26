import { NextResponse } from "next/server";

// Mock logout API
export async function POST() {
  // In a real implementation, this would invalidate the token on the backend
  return NextResponse.json({ success: true });
}
