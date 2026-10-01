import { NextRequest, NextResponse } from "next/server";

const API_ORIGIN = process.env.API_ORIGIN || "http://127.0.0.1:8000";

export async function GET(request: NextRequest) {
  try {
    const target = API_ORIGIN + "/api/v1/auth/sso/oidc/callback" + request.nextUrl.search;
    const upstream = await fetch(target, {
      method: "GET",
      headers: { Accept: "text/html", Cookie: request.headers.get("cookie") || "" },
      redirect: "manual",
      cache: "no-store",
    });
    const body = upstream.status >= 400 ? await upstream.text() : null;
    const response = new NextResponse(body, {
      status: upstream.status,
      headers: body ? { "Content-Type": upstream.headers.get("content-type") || "application/json" } : undefined,
    });
    const location = upstream.headers.get("location");
    if (location) response.headers.set("location", location);
    for (const cookie of upstream.headers.getSetCookie?.() ?? []) response.headers.append("Set-Cookie", cookie);
    return response;
  } catch {
    return NextResponse.redirect(new URL("/login?sso=unavailable", request.url));
  }
}
