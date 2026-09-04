import type { ReactNode } from "react";

export const metadata = {
  title: "SavePoint",
  description: "Personal video game collection and backlog tracker",
};

export default function RootLayout({
  children,
}: {
  children: ReactNode;
}) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}
