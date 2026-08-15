import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Vibe Terms",
  description: "A multilingual Vibe Coding terminology dictionary for beginners.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
