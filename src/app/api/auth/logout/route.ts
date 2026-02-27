import { NextResponse } from "next/server";

export async function POST() {
  // JWT-based auth: tokens are stateless, client-side cleanup handles logout.
  // If the backend adds token blacklisting in the future, proxy here.
  return NextResponse.json({ success: true });
}
