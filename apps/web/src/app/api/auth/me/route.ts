import { NextResponse } from "next/server";
import { getCurrentAuth } from "@/lib/auth";

export async function GET() {
  const auth = await getCurrentAuth();
  if (!auth) {
    return NextResponse.json({ ok: false }, { status: 401 });
  }
  return NextResponse.json({
    ok: true,
    user: {
      id: auth.id,
      email: auth.email,
      role: auth.role,
    },
  });
}
