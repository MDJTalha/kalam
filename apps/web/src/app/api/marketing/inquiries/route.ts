import { NextRequest, NextResponse } from "next/server";
const API_ORIGIN = process.env.API_ORIGIN || "http://127.0.0.1:8000";
const unavailable = () => NextResponse.json({ detail: "Demo requests are currently unavailable." }, { status: 503 });

export async function POST(request: NextRequest) {
  if (process.env.MARKETING_INBOX_ENABLED !== "true" || !process.env.MARKETING_REVIEW_TENANT_SLUG) return unavailable();
  const origin = request.headers.get("origin");
  if (!origin || origin !== request.nextUrl.origin) {
    return NextResponse.json({ detail: "Invalid request origin." }, { status: 403 });
  }
  if (!request.headers.get("content-type")?.startsWith("application/json")) {
    return NextResponse.json({ detail: "Expected JSON." }, { status: 415 });
  }
  const body = await request.text();
  if (body.length > 4000) return NextResponse.json({ detail: "Request is too large." }, { status: 413 });
  try {
    const upstream = await fetch(`${API_ORIGIN}/api/v1/marketing/inquiries`, {
      method: "POST", headers: { "content-type": "application/json" }, body, cache: "no-store",
    });
    const response = await upstream.json();
    return NextResponse.json(response, { status: upstream.status, headers: { "cache-control": "no-store" } });
  } catch {
    return unavailable();
  }
}
