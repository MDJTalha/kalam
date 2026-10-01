export type PublicPlan = {
  id: string; code: string; name: string; tagline?: string | null; description?: string | null;
  status: string; public_visible: boolean; billing_model: string; currency: string;
  monthly_price_minor?: number | null; annual_price_minor?: number | null;
  trial_days: number; minimum_seats: number; maximum_seats?: number | null;
  features: unknown[]; limits: Record<string, unknown>; sort_order: number;
};
export type PublicOffer = {
  id: string; plan_id?: string | null; code: string; title: string; description?: string | null;
  discount_type: string; discount_value: number; starts_at?: string | null; ends_at?: string | null;
};
export type PublicClient = {
  id: string; name: string; industry?: string | null; country?: string | null;
  website?: string | null; logo_url?: string | null; testimonial?: string | null;
};
export type PublicCertification = {
  id: string; title: string; issuer: string; registration_number?: string | null;
  issued_at?: string | null; expires_at?: string | null; verification_url?: string | null;
};
export type PublicCommercialCatalog = {
  plans: PublicPlan[]; offers: PublicOffer[]; clients: PublicClient[]; certifications: PublicCertification[];
};

const API_ORIGIN = process.env.API_ORIGIN || "http://127.0.0.1:8000";

export async function getPublicCommercialCatalog(): Promise<PublicCommercialCatalog> {
  const fallback = { plans: [], offers: [], clients: [], certifications: [] };
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 2000);
  try {
    const response = await fetch(`${API_ORIGIN}/api/v1/saas/public/catalog`, {
      cache: "no-store",
      signal: controller.signal,
    });
    if (!response.ok) return fallback;
    return response.json() as Promise<PublicCommercialCatalog>;
  } catch {
    return fallback;
  } finally {
    clearTimeout(timeout);
  }
}

export function formatCommercialPrice(minor: number | null | undefined, currency: string) {
  if (minor == null) return null;
  return new Intl.NumberFormat("en-US", { style: "currency", currency, maximumFractionDigits: minor % 100 === 0 ? 0 : 2 }).format(minor / 100);
}
