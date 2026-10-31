import { cookies } from "next/headers";
import { redirect } from "next/navigation";

const API_ORIGIN = process.env.API_ORIGIN || "http://127.0.0.1:8000";

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

export type ApiJsonResult<T> = {
  ok: boolean;
  status: number;
  data: T | null;
  error: string | null;
};

export async function apiJsonResult<T>(path: string, init: RequestInit = {}): Promise<ApiJsonResult<T>> {
  let response: Response;
  try {
    response = await apiFetch(path, init);
  } catch {
    return {
      ok: false,
      status: 0,
      data: null,
      error: "The API service could not be reached. Check that it is running and try again.",
    };
  }
  const body = await response.text();
  let parsed: unknown = null;
  if (body) {
    try {
      parsed = JSON.parse(body) as unknown;
    } catch {
      parsed = null;
    }
  }
  if (!response.ok) {
    const detail = parsed && typeof parsed === "object" && parsed !== null && "detail" in parsed
      ? String((parsed as { detail?: unknown }).detail ?? "")
      : body.trim();
    return { ok: false, status: response.status, data: null, error: detail || response.statusText || "Request failed" };
  }
  return { ok: true, status: response.status, data: parsed as T, error: null };
}

/**
 * Backward-compatible JSON helper for legacy/non-critical pages.
 * Critical reads should use apiJsonResult so service/API failures remain explicit.
 */
export async function apiJson<T>(path: string, init: RequestInit = {}): Promise<T | null> {
  const result = await apiJsonResult<T>(path, init);
  return result.ok ? result.data : null;
}

export async function requireUser<T = Record<string, unknown>>() {
  let response: Response;
  try {
    response = await apiFetch("/api/v1/auth/me");
  } catch {
    redirect("/service-unavailable");
  }
  if (response.status === 401) redirect("/login");
  if (response.status === 403) redirect("/access-denied");
  if (!response.ok) {
    redirect("/service-unavailable");
  }
  return response.json() as Promise<T>;
}
