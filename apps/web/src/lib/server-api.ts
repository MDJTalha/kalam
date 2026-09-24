import { cookies } from "next/headers";
import { redirect } from "next/navigation";

const API_ORIGIN = process.env.API_ORIGIN || "http://localhost:8000";

export async function apiFetch(path: string, init: RequestInit = {}) {
  const cookieStore = await cookies();
  const cookieHeader = cookieStore.toString();
  const headers = new Headers(init.headers);
  if (cookieHeader) headers.set("cookie", cookieHeader);
  headers.set("Accept", "application/json");

  return fetch(`${API_ORIGIN}${path}`, {
    ...init,
    headers,
    cache: "no-store",
  });
}

export async function apiJson<T>(path: string, init: RequestInit = {}): Promise<T | null> {
  const response = await apiFetch(path, init);
  if (!response.ok) return null;
  return response.json() as Promise<T>;
}

export async function requireUser<T = Record<string, unknown>>() {
  const user = await apiJson<T>("/api/v1/auth/me");
  if (!user) redirect("/login");
  return user;
}
