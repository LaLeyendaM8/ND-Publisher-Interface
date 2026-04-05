import "server-only";

import { cookies } from "next/headers";

export type AppRole = "admin" | "editor" | "viewer";

type SupabaseUser = {
  id: string;
  email: string | null;
  app_metadata?: Record<string, unknown>;
  user_metadata?: Record<string, unknown>;
};

type TokenResponse = {
  access_token: string;
  refresh_token: string;
  expires_in: number;
  token_type: string;
  user: SupabaseUser;
};

const AUTH_COOKIE_ACCESS = "ndpi_access_token";
const AUTH_COOKIE_REFRESH = "ndpi_refresh_token";
const AUTH_COOKIE_EXPIRES_AT = "ndpi_expires_at";

function requireSupabaseUrl() {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  if (!url) {
    throw new Error("NEXT_PUBLIC_SUPABASE_URL is required.");
  }
  return url.replace(/\/+$/, "");
}

function requireSupabaseAnonKey() {
  const key = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  if (!key) {
    throw new Error("NEXT_PUBLIC_SUPABASE_ANON_KEY is required.");
  }
  return key;
}

function authCookieBase() {
  return {
    path: "/",
    httpOnly: true,
    sameSite: "lax" as const,
    secure: process.env.NODE_ENV === "production",
  };
}

function readRole(user: SupabaseUser): AppRole {
  const fromAppMetadata = user.app_metadata?.role;
  const fromUserMetadata = user.user_metadata?.role;
  const value = typeof fromAppMetadata === "string" ? fromAppMetadata : fromUserMetadata;
  if (value === "admin" || value === "editor" || value === "viewer") {
    return value;
  }
  return "viewer";
}

async function supabaseTokenPassword(email: string, password: string): Promise<TokenResponse | null> {
  const response = await fetch(`${requireSupabaseUrl()}/auth/v1/token?grant_type=password`, {
    method: "POST",
    headers: {
      apikey: requireSupabaseAnonKey(),
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ email, password }),
    cache: "no-store",
  });
  if (!response.ok) return null;
  return (await response.json()) as TokenResponse;
}

async function supabaseTokenRefresh(refreshToken: string): Promise<TokenResponse | null> {
  const response = await fetch(`${requireSupabaseUrl()}/auth/v1/token?grant_type=refresh_token`, {
    method: "POST",
    headers: {
      apikey: requireSupabaseAnonKey(),
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ refresh_token: refreshToken }),
    cache: "no-store",
  });
  if (!response.ok) return null;
  return (await response.json()) as TokenResponse;
}

async function supabaseUser(accessToken: string): Promise<SupabaseUser | null> {
  const response = await fetch(`${requireSupabaseUrl()}/auth/v1/user`, {
    method: "GET",
    headers: {
      apikey: requireSupabaseAnonKey(),
      Authorization: `Bearer ${accessToken}`,
    },
    cache: "no-store",
  });
  if (!response.ok) return null;
  return (await response.json()) as SupabaseUser;
}

async function setSessionCookies(tokens: TokenResponse) {
  const cookieStore = await cookies();
  const expiresAt = Math.floor(Date.now() / 1000) + tokens.expires_in;
  cookieStore.set(AUTH_COOKIE_ACCESS, tokens.access_token, {
    ...authCookieBase(),
    maxAge: tokens.expires_in,
  });
  cookieStore.set(AUTH_COOKIE_REFRESH, tokens.refresh_token, {
    ...authCookieBase(),
    maxAge: 60 * 60 * 24 * 30,
  });
  cookieStore.set(AUTH_COOKIE_EXPIRES_AT, String(expiresAt), {
    ...authCookieBase(),
    maxAge: tokens.expires_in,
  });
}

export async function clearSessionCookies() {
  const cookieStore = await cookies();
  cookieStore.delete({ name: AUTH_COOKIE_ACCESS, path: "/" });
  cookieStore.delete({ name: AUTH_COOKIE_REFRESH, path: "/" });
  cookieStore.delete({ name: AUTH_COOKIE_EXPIRES_AT, path: "/" });
}

async function readCookieSession() {
  const cookieStore = await cookies();
  const accessToken = cookieStore.get(AUTH_COOKIE_ACCESS)?.value ?? "";
  const refreshToken = cookieStore.get(AUTH_COOKIE_REFRESH)?.value ?? "";
  const expiresAtRaw = cookieStore.get(AUTH_COOKIE_EXPIRES_AT)?.value ?? "";
  const expiresAt = Number(expiresAtRaw);
  return {
    accessToken,
    refreshToken,
    expiresAt: Number.isFinite(expiresAt) ? expiresAt : 0,
  };
}

async function refreshIfNeeded() {
  const session = await readCookieSession();
  if (!session.accessToken || !session.refreshToken) return session;
  const now = Math.floor(Date.now() / 1000);
  if (session.expiresAt > now + 30) return session;

  const refreshed = await supabaseTokenRefresh(session.refreshToken);
  if (!refreshed) {
    await clearSessionCookies();
    return { accessToken: "", refreshToken: "", expiresAt: 0 };
  }

  await setSessionCookies(refreshed);
  return {
    accessToken: refreshed.access_token,
    refreshToken: refreshed.refresh_token,
    expiresAt: now + refreshed.expires_in,
  };
}

export async function signInWithPasswordServer(email: string, password: string) {
  const tokens = await supabaseTokenPassword(email, password);
  if (!tokens) return null;
  await setSessionCookies(tokens);
  return {
    id: tokens.user.id,
    email: tokens.user.email,
    role: readRole(tokens.user),
  };
}

export async function getCurrentAuth() {
  const session = await refreshIfNeeded();
  if (!session.accessToken) return null;

  const user = await supabaseUser(session.accessToken);
  if (!user) {
    await clearSessionCookies();
    return null;
  }

  return {
    id: user.id,
    email: user.email,
    role: readRole(user),
    accessToken: session.accessToken,
  };
}

export async function isAuthenticated(): Promise<boolean> {
  return (await getCurrentAuth()) !== null;
}
