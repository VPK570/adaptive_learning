import localFont from "next/font/local";
import "./globals.css";
import { Providers } from './providers';

const inter = localFont({
  src: "./fonts/inter-var-latin.woff2",
  weight: "400 700",
  variable: "--font-inter",
  display: "swap",
});

const jetbrainsMono = localFont({
  src: "./fonts/jetbrainsmono-400-latin.woff2",
  weight: "400",
  variable: "--font-jetbrains",
  display: "swap",
});

export const metadata = {
  title: "Vbook LM",
  description: "University AI Platform",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" className={`${inter.variable} ${jetbrainsMono.variable}`}>
      <body><Providers>{children}</Providers></body>
    </html>
  );
}
