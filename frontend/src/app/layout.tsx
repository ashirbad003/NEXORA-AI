import type { Metadata } from "next";
import "@/styles/globals.css";
import { AuthProvider } from "@/lib/authContext";
import { Navbar } from "@/components/layout/Navbar";
import { Footer } from "@/components/layout/Footer";

export const metadata: Metadata = {
  title: "NEXORA AI - Intelligence That Moves You Forward",
  description: "Next-generation AI Career, Learning, Coding & Placement Ecosystem",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-obsidian min-h-screen text-text-primary antialiased selection:bg-cyber selection:text-obsidian flex flex-col">
        <AuthProvider>
          <Navbar />
          <div className="flex-1">{children}</div>
          <Footer />
        </AuthProvider>
      </body>
    </html>
  );
}
