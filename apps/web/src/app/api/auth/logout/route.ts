import { cookies } from "next/headers";
import { NextResponse } from "next/server";
import { authCookieConfig } from "@/lib/auth";

export async function POST() {
  const cookieStore = await cookies();
  cookieStore.delete({
    name: authCookieConfig.name,
    path: authCookieConfig.path,
  });
  return NextResponse.json({ ok: true });
}
