"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const items = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/projects", label: "Projekte" },
  { href: "/tools", label: "Tools" },
  { href: "/files", label: "Dateien" },
  { href: "/glossaries", label: "Glossare" },
  { href: "/settings", label: "Einstellungen" },
];

export function AppNav() {
  const pathname = usePathname();
  return (
    <nav className="space-y-1">
      {items.map((item) => {
        const active = pathname.startsWith(item.href);
        return (
          <Link key={item.href} href={item.href} className={`nd-nav-link ${active ? "is-active" : ""}`}>
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
