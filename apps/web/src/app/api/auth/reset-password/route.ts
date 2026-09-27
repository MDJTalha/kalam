import { NextRequest, NextResponse } from "next/server";

const API_ORIGIN = process.env.API_ORIGIN || "http://127.0.0.1:8000";

export async function POST(request: NextRequest) {
  try {
    const body = await request.text();
    const upstream = await fetch(`${API_ORIGIN}/api/v1/auth/reset-password`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body,
      cache: "no-store",
    });
    if (!upstream.ok) {
      const message = upstream.status === 400 ? "This reset link is invalid or has expired. Request a new link." : "We couldn't reset your password. Please try again.";
      return NextResponse.json({ detail: message }, { status: upstream.status });
    }
    const response = NextResponse.json({ detail: "Password updated." });
    for (const cookie of upstream.headers.getSetCookie?.() ?? []) response.headers.append("Set-Cookie", cookie);
    return response;
  } catch {
    return NextResponse.json({ detail: "Password recovery is temporarily unavailable." }, { status: 503 });
  }
}
