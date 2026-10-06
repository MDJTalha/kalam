import { NextRequest, NextResponse } from "next/server";

const API_ORIGIN = process.env.API_ORIGIN || "http://127.0.0.1:8000";

export async function POST(request: NextRequest) {
  try {
    const body = await request.text();
    const upstream = await fetch(`${API_ORIGIN}/api/v1/auth/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body,
      cache: "no-store",
    });

    const responseBody = await upstream.text();
    const response = new NextResponse(responseBody, {
      status: upstream.status,
      headers: {
        "Content-Type": upstream.headers.get("content-type") || "application/json",
      },
    });

    const setCookies = upstream.headers.getSetCookie?.() ?? [];
    const forwardedProto = request.headers.get("x-forwarded-proto")?.split(",")[0]?.trim().toLowerCase();
    const host = request.headers.get("host")?.split(",")[0]?.trim().toLowerCase() || "";
    const isLocalHttp = /^127\.0\.0\.1(?::\d+)?$/.test(host) || /^localhost(?::\d+)?$/.test(host);
    const isHttps = forwardedProto === "https" || request.nextUrl.protocol === "https:";
    for (const cookie of setCookies) {
      // Production keeps Secure cookies. Only a browser-facing local HTTP host gets
      // Secure stripped; HTTPS and all non-local hosts retain the production cookie.
      const normalizedCookie = isLocalHttp && !isHttps
        ? cookie.replace(/;\s*Secure(?=;|$)/gi, "")
        : cookie;
      response.headers.append("Set-Cookie", normalizedCookie);
    }

    return response;
  } catch {
    return NextResponse.json(
      { detail: "Learning service is unavailable." },
      { status: 503 },
    );
  }
}
