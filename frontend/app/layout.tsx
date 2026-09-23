import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Video Review Lab",
  description: "A first pass creative review for short video ads",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
