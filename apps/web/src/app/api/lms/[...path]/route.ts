import { NextRequest, NextResponse } from "next/server";

const API_ORIGIN = process.env.API_ORIGIN || "http://127.0.0.1:8000";

async function proxy(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  const target = `${API_ORIGIN}/api/v1/${path.join("/")}${request.nextUrl.search}`;
  const headers = new Headers(request.headers);
  headers.delete("host");
  headers.delete("content-length");
  const response = await fetch(target, {
    method: request.method,
    headers,
    body: request.method === "GET" || request.method === "HEAD" ? undefined : await request.arrayBuffer(),
    cache: "no-store",
  });
  const body = await response.arrayBuffer();
  const result = new NextResponse(body, { status: response.status });
  const contentType = response.headers.get("content-type");
  if (contentType) result.headers.set("content-type", contentType);
  const contentDisposition = response.headers.get("content-disposition");
  if (contentDisposition) result.headers.set("content-disposition", contentDisposition);
  const requestId = response.headers.get("x-request-id");
  if (requestId) result.headers.set("x-request-id", requestId);
  const setCookies = response.headers.getSetCookie?.() ?? [];
  for (const cookie of setCookies) result.headers.append("Set-Cookie", cookie);
  return result;
}

export const GET = proxy;
export const POST = proxy;
export const PUT = proxy;
export const PATCH = proxy;
export const DELETE = proxy;
export const OPTIONS = proxy;
