import type { Metadata } from "next";
import { ClerkProvider } from "@clerk/nextjs";
import { isClerkConfigured } from "@/lib/clerk-env";
import "./globals.css";

export const metadata: Metadata = {
  title: "SVMP CS | Governed AI Customer Support",
  description:
    "SVMP CS automates WhatsApp customer support with approved knowledge, brand voice controls, confidence thresholds, and governance logs.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const content = isClerkConfigured() ? <ClerkProvider>{children}</ClerkProvider> : children;

  return (
    <html lang="en">
      <body>{content}</body>
    </html>
  );
}
