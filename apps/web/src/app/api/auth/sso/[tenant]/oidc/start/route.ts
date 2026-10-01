import { NextRequest, NextResponse } from "next/server";

const API_ORIGIN = process.env.API_ORIGIN || "http://127.0.0.1:8000";

export async function GET(request: NextRequest, context: { params: Promise<{ tenant: string }> }) {
  const { tenant } = await context.params;
  try {
    const upstream = await fetch(
      API_ORIGIN + "/api/v1/auth/sso/" + encodeURIComponent(tenant) + "/oidc/start",
      { method: "GET", headers: { Accept: "text/html", Cookie: request.headers.get("cookie") || "" }, redirect: "manual", cache: "no-store" },
    );
    const response = new NextResponse(null, { status: upstream.status });
    const location = upstream.headers.get("location");
    if (location) response.headers.set("location", location);
    for (const cookie of upstream.headers.getSetCookie?.() ?? []) response.headers.append("Set-Cookie", cookie);
    return response;
  } catch {
    return NextResponse.redirect(new URL("/login?sso=unavailable", request.url));
  }
}
