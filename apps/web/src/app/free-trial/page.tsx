import { permanentRedirect } from "next/navigation";

export default async function LegacyFreeTrialPage({ searchParams }: { searchParams: Promise<{ plan?: string }> }) {
  const params = await searchParams;
  const query = params.plan ? "?plan=" + encodeURIComponent(params.plan) : "";
  permanentRedirect("/guided-evaluation" + query);
}
