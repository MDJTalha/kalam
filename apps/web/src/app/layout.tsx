import type { Metadata, Viewport } from "next";
import localFont from "next/font/local";
import "./globals.css";
import "./auth-experience.css";

const geistSans = localFont({ src: "./fonts/Geist-Latin.woff2", variable: "--font-geist-sans", weight: "100 900", display: "swap" });
const geistMono = localFont({ src: "./fonts/GeistMono-Latin.woff2", variable: "--font-geist-mono", weight: "100 900", display: "swap" });

export const metadata: Metadata = {
  title: { default: "Kognivon | Learning Intelligence", template: "%s · Kognivon" },
  description: "Enterprise learning, compliance, skills and workforce capability platform.",
  applicationName: "Kognivon",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={geistSans.variable + " " + geistMono.variable}>
      <body>{children}</body>
    </html>
  );
}
