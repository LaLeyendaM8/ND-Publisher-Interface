import { cookies } from "next/headers";
import { NextResponse } from "next/server";
import { authCookieConfig, createSessionToken, verifyLoginPassword } from "@/lib/auth";

export async function POST(req: Request) {
  const body = (await req.json().catch(() => null)) as { password?: string } | null;
  const password = body?.password ?? "";

  if (!verifyLoginPassword(password)) {
    return NextResponse.json(
      { ok: false, error: { code: "invalid_credentials", message: "Login failed." } },
      { status: 401 },
    );
  }

  const token = createSessionToken();
  const cookieStore = await cookies();
  cookieStore.set(authCookieConfig.name, token, authCookieConfig);

  return NextResponse.json({ ok: true });
}
