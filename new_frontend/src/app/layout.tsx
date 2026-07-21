import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { Providers } from './providers';

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  weight: ["400", "500", "600", "700"],
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-jetbrains",
  weight: ["400"],
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
