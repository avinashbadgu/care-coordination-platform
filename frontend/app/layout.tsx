import "./globals.css";
import type { Metadata } from "next";
import Link from "next/link";
import { Activity } from "lucide-react";

export const metadata: Metadata = {
  title: "Care Coordination",
  description: "AI-assisted care coordination & workflow intelligence",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen antialiased">
        <header className="border-b bg-background">
          <div className="container flex h-14 items-center justify-between">
            <Link href="/" className="flex items-center gap-2 font-semibold">
              <Activity className="h-5 w-5" />
              <span>Care Coordination</span>
            </Link>
            <nav className="text-sm text-muted-foreground">
              <Link href="/patients" className="hover:text-foreground">
                Patients
              </Link>
            </nav>
          </div>
        </header>
        <main className="container py-8">{children}</main>
      </body>
    </html>
  );
}
