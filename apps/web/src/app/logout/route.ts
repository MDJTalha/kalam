import { redirect } from "next/navigation";
import { cookies } from "next/headers";

export async function GET() {
  const cookieStore = await cookies();
  const cookieHeader = cookieStore.toString();
  try {
    await fetch(`${process.env.API_ORIGIN || "http://localhost:8000"}/api/v1/auth/logout`, {
      method: "POST",
      headers: cookieHeader ? { cookie: cookieHeader } : undefined,
      cache: "no-store",
    });
  } finally {
    redirect("/login");
  }
}
