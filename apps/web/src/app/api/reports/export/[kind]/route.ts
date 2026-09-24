import { cookies } from "next/headers";
import { NextResponse } from "next/server";

const API_ORIGIN = process.env.API_ORIGIN || "http://localhost:8000";

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ kind: string }> },
) {
  const { kind } = await params;
  if (kind !== "people" && kind !== "enrollments") {
    return NextResponse.json({ detail: "Unknown report" }, { status: 404 });
  }

  const cookieHeader = (await cookies()).toString();
  const response = await fetch(
    API_ORIGIN + "/api/v1/reports/export/" + kind,
    {
      headers: cookieHeader ? { cookie: cookieHeader } : undefined,
      cache: "no-store",
    },
  );

  const body = await response.text();
  return new NextResponse(body, {
    status: response.status,
    headers: {
      "Content-Type": response.headers.get("content-type") || "text/csv; charset=utf-8",
      "Content-Disposition": response.headers.get("content-disposition") || 'attachment; filename="report.csv"',
    },
  });
}
