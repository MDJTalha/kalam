import type { MetadataRoute } from "next";

export default function sitemap(): MetadataRoute.Sitemap {
  const base = process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000";
  const pages = ["", "/pricing", "/guided-evaluation", "/contact-sales", "/trust", "/implementation", "/integrations"];
  return pages.map((path, index) => ({
    url: base + path,
    lastModified: new Date(),
    changeFrequency: index === 0 ? "weekly" : "monthly",
    priority: index === 0 ? 1 : path === "/contact-sales" ? 0.9 : 0.8,
  }));
}
