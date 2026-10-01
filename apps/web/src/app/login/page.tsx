import { LoginClient } from "./login-client";

export default async function LoginPage({ searchParams }: { searchParams: Promise<{ org?: string; sso?: string }> }) {
  const params = await searchParams;
  const initialOrganization = (params.org || "").trim().toLowerCase();
  const initialSsoError = params.sso === "failed" ? "Enterprise SSO could not complete. Try again or use your approved sign-in method." : "";
  return <LoginClient initialOrganization={initialOrganization} initialSsoError={initialSsoError} />;
}
