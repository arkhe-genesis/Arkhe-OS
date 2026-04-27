import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Arkhe OS v19 - Collective Consciousness',
  description: 'Federated Ethics & Quantum AR Dashboard',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="antialiased overflow-x-hidden">{children}</body>
    </html>
  );
}
