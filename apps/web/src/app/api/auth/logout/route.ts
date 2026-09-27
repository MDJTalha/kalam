import { NextRequest, NextResponse } from "next/server";

const API_ORIGIN = process.env.API_ORIGIN || "http://127.0.0.1:8000";

export async function POST(request: NextRequest) {
  try {
    const upstream = await fetch(`${API_ORIGIN}/api/v1/auth/logout`, {
      method: "POST",
      headers: { Accept: "application/json", cookie: request.headers.get("cookie") || "" },
      cache: "no-store",
    });
    const response = NextResponse.redirect(new URL("/login", request.url), 303);
    for (const cookie of upstream.headers.getSetCookie?.() ?? []) response.headers.append("Set-Cookie", cookie);
    return response;
  } catch {
    return NextResponse.redirect(new URL("/login", request.url), 303);
  }
}
