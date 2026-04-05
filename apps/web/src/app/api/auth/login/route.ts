import { NextResponse } from "next/server";
import { signInWithPasswordServer } from "@/lib/auth";

export async function POST(req: Request) {
  const body = (await req.json().catch(() => null)) as { email?: string; password?: string } | null;
  const email = body?.email ?? "";
  const password = body?.password ?? "";
  if (!email || !password) {
    return NextResponse.json(
      { ok: false, error: { code: "invalid_request", message: "Email and password are required." } },
      { status: 400 },
    );
  }

  const auth = await signInWithPasswordServer(email, password);
  if (!auth) {
    return NextResponse.json(
      { ok: false, error: { code: "invalid_credentials", message: "Login failed." } },
      { status: 401 },
    );
  }

  return NextResponse.json({ ok: true, role: auth.role, email: auth.email });
}
