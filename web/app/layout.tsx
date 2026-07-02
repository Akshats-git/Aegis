import type { Metadata } from "next";
import { GeistSans } from "geist/font/sans";
import { GeistMono } from "geist/font/mono";
import "./globals.css";

export const metadata: Metadata = {
  title: "Aegis — the memory that keeps your health record honest",
  description:
    "A self-correcting clinical memory that remembers what your doctors can't — and forgets what could hurt you.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${GeistSans.variable} ${GeistMono.variable}`}>
      <body className="font-sans antialiased">
        <div className="app-bg" />
        {children}
      </body>
    </html>
  );
}
