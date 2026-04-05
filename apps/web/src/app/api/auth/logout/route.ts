import { NextResponse } from "next/server";
import { clearSessionCookies, getCurrentAuth } from "@/lib/auth";

export async function POST() {
  const auth = await getCurrentAuth();
  if (auth?.accessToken) {
    await fetch(`${process.env.NEXT_PUBLIC_SUPABASE_URL?.replace(/\/+$/, "")}/auth/v1/logout`, {
      method: "POST",
      headers: {
        apikey: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? "",
        Authorization: `Bearer ${auth.accessToken}`,
      },
      cache: "no-store",
    }).catch(() => null);
  }
  await clearSessionCookies();
  return NextResponse.json({ ok: true });
}
