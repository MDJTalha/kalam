import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Forgot password",
  robots: { index: false, follow: false, nocache: true },
};

export default function ForgotPasswordLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return children;
}
