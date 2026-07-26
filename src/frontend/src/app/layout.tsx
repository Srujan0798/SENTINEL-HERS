import type { Metadata } from "next";
import { AuthProvider } from "@/lib/auth";
import { WakingOverlay } from "@/components/WakingOverlay";
import { Toaster } from "@/components/ui/toast";
import "./globals.css";

export const metadata: Metadata = {
  title: "SENTINEL — AI-Native Engineering Operations",
  description:
    "Mission console for production incidents: logs, deploys, AI diagnosis, tasks, and team chat in one war room.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full dark">
      <body className="min-h-full flex flex-col antialiased">
        <AuthProvider><WakingOverlay>{children}</WakingOverlay></AuthProvider>
        <Toaster />
      </body>
    </html>
  );
}
