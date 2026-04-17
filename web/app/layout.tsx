import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SVMP | Governed AI Customer Support",
  description:
    "SVMP automates WhatsApp customer support with approved knowledge, brand voice controls, confidence thresholds, and governance logs.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
