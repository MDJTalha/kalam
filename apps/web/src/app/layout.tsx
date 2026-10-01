import type { Metadata, Viewport } from "next";
import localFont from "next/font/local";
import "./globals.css";
import "./auth-experience.css";
import "intl-tel-input/build/css/intlTelInput.css";
import { NavigationProgress } from "@/components/navigation-progress";
import { ScrollToTop } from "@/components/scroll-to-top";

const geistSans = localFont({ src: "./fonts/Geist-Latin.woff2", variable: "--font-geist-sans", weight: "100 900", display: "swap" });
const geistMono = localFont({ src: "./fonts/GeistMono-Latin.woff2", variable: "--font-geist-mono", weight: "100 900", display: "swap" });
const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000";

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: { default: "Kalam | Enterprise Workforce Capability Platform", template: "%s · Kalam" },
  description: "Kalam connects workforce expectations, capability, learning, evidence and readiness in one governed enterprise platform.",
  applicationName: "Kalam",
  keywords: ["workforce capability","enterprise learning","skills management","compliance readiness","workforce readiness","learning management","capability management"],
  openGraph: {
    type: "website",
    siteName: "Kalam",
    title: "Kalam | Enterprise Workforce Capability Platform",
    description: "Build capability, prove readiness and connect workforce development with evidence and action.",
    url: "/",
    images: [{ url: "/kalam-og.png", width: 1200, height: 630, alt: "Kalam Enterprise Workforce Capability Platform" }],
  },
  twitter: {
    card: "summary_large_image",
    title: "Kalam | Enterprise Workforce Capability Platform",
    description: "Build capability, prove readiness and connect workforce development with evidence and action.",
    images: ["/kalam-og.png"],
  },
  robots: { index: true, follow: true },
  manifest: "/manifest.webmanifest",
  icons: {
    icon: [{ url: "/favicon-16.png", sizes: "16x16", type: "image/png" }, { url: "/favicon-32.png", sizes: "32x32", type: "image/png" }],
    shortcut: "/favicon-32.png",
    apple: [{ url: "/apple-touch-icon.png", sizes: "180x180", type: "image/png" }],
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={geistSans.variable + " " + geistMono.variable}>
      <body>{children}<NavigationProgress /><ScrollToTop /></body>
    </html>
  );
}
