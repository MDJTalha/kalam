import { NextRequest, NextResponse } from "next/server";

const API_ORIGIN = process.env.API_ORIGIN || "http://127.0.0.1:8000";

export async function POST(request: NextRequest) {
  try {
    const body = await request.text();
    const upstream = await fetch(`${API_ORIGIN}/api/v1/auth/forgot-password`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body,
      cache: "no-store",
    });
    if (!upstream.ok) {
      return NextResponse.json({ detail: "We couldn't process your request. Please try again." }, { status: upstream.status });
    }
    return NextResponse.json({ detail: "If the account exists, a reset link will be sent." }, { status: 202 });
  } catch {
    return NextResponse.json({ detail: "Password recovery is temporarily unavailable." }, { status: 503 });
  }
}
