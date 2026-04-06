import { NextResponse } from "next/server";
import { clearSessionCookies, signInWithPasswordServer } from "@/lib/auth";

async function syncActorProvisioning(auth: { id: string; email: string | null; role: string }) {
  const baseUrl = process.env.PUBLISHER_API_URL?.replace(/\/+$/, "");
  const internalToken = process.env.PUBLISHER_API_TOKEN ?? "";
  if (!baseUrl || !internalToken) {
    throw new Error("Provisioning config missing.");
  }

  const response = await fetch(`${baseUrl}/auth/sync`, {
    method: "GET",
    headers: {
      "X-Internal-Token": internalToken,
      "X-User-Id": auth.id,
      "X-User-Email": auth.email ?? "",
      "X-User-Role": auth.role,
    },
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error("Provisioning request failed.");
  }
}

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

  try {
    await syncActorProvisioning(auth);
  } catch {
    await clearSessionCookies();
    return NextResponse.json(
      { ok: false, error: { code: "provisioning_failed", message: "Login provisioning failed." } },
      { status: 503 },
    );
  }

  return NextResponse.json({ ok: true, role: auth.role, email: auth.email });
}
