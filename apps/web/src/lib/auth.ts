import "server-only";

import { createHmac, timingSafeEqual } from "node:crypto";
import { cookies } from "next/headers";

const SESSION_COOKIE = "ndpi_session";
const SESSION_TTL_SECONDS = 60 * 60 * 12;

function requireAuthSecret() {
  const value = process.env.APP_SESSION_SECRET;
  if (!value) {
    throw new Error("APP_SESSION_SECRET is required.");
  }
  return value;
}

function getLoginPassword() {
  return process.env.APP_LOGIN_PASSWORD ?? "";
}

function sign(payload: string): string {
  return createHmac("sha256", requireAuthSecret()).update(payload).digest("hex");
}

function parseToken(token: string): { payload: string; signature: string } | null {
  const raw = Buffer.from(token, "base64url").toString("utf8");
  const lastDot = raw.lastIndexOf(".");
  if (lastDot === -1) return null;
  const payload = raw.slice(0, lastDot);
  const signature = raw.slice(lastDot + 1);
  if (!payload || !signature) return null;
  return { payload, signature };
}

function isSignatureValid(payload: string, providedSignature: string): boolean {
  const expectedSignature = sign(payload);
  const expectedBuffer = Buffer.from(expectedSignature, "utf8");
  const providedBuffer = Buffer.from(providedSignature, "utf8");
  if (expectedBuffer.length !== providedBuffer.length) return false;
  return timingSafeEqual(expectedBuffer, providedBuffer);
}

export function verifyLoginPassword(password: string): boolean {
  const expected = getLoginPassword();
  if (!expected || !password) return false;
  return password === expected;
}

export function createSessionToken(): string {
  const expiresAt = Math.floor(Date.now() / 1000) + SESSION_TTL_SECONDS;
  const payload = `ndpi:${expiresAt}`;
  const signature = sign(payload);
  return Buffer.from(`${payload}.${signature}`, "utf8").toString("base64url");
}

export async function isAuthenticated(): Promise<boolean> {
  try {
    const cookieStore = await cookies();
    const token = cookieStore.get(SESSION_COOKIE)?.value;
    if (!token) return false;

    const parsed = parseToken(token);
    if (!parsed) return false;

    if (!isSignatureValid(parsed.payload, parsed.signature)) {
      return false;
    }

    const [prefix, expiresAtRaw] = parsed.payload.split(":");
    if (prefix !== "ndpi" || !expiresAtRaw) return false;
    const expiresAt = Number(expiresAtRaw);
    if (!Number.isFinite(expiresAt)) return false;
    return expiresAt > Math.floor(Date.now() / 1000);
  } catch {
    return false;
  }
}

export const authCookieConfig = {
  name: SESSION_COOKIE,
  maxAge: SESSION_TTL_SECONDS,
  path: "/",
  httpOnly: true,
  sameSite: "lax" as const,
  secure: process.env.NODE_ENV === "production",
};
