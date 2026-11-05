import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Kalam — Enterprise Workforce Capability Platform",
    short_name: "Kalam",
    description:
      "Enterprise workforce capability platform connecting people, learning, skills, evidence, compliance, capability and readiness.",
    start_url: "/",
    display: "standalone",
    background_color: "#F4F8FC",
    theme_color: "#08243D",
    lang: "en",
    icons: [
      { src: "/kalam-app-192.png", sizes: "192x192", type: "image/png", purpose: "any" },
      { src: "/kalam-app-512.png", sizes: "512x512", type: "image/png", purpose: "maskable" },
    ],
  };
}
