import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Kalam — Enterprise Workforce Capability Platform",
    short_name: "Kalam",
    description:
      "Enterprise workforce capability platform connecting people, learning, skills, evidence, compliance, capability and readiness.",
    start_url: "/",
    display: "standalone",
    background_color: "#ffffff",
    theme_color: "#08243D",
    lang: "en",
  };
}
