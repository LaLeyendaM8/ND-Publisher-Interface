import { NextRequest } from "next/server";

const BASE_URL = process.env.PUBLISHER_API_URL ?? "http://127.0.0.1:8000";
const INTERNAL_TOKEN = process.env.PUBLISHER_API_TOKEN ?? "";

function joinPath(parts: string[]): string {
  const cleaned = parts.map((p) => encodeURIComponent(p)).join("/");
  return `${BASE_URL.replace(/\/+$/, "")}/${cleaned}`;
}

async function proxy(req: NextRequest, method: string, path: string[]) {
  const url = new URL(joinPath(path));
  req.nextUrl.searchParams.forEach((value, key) => url.searchParams.set(key, value));

  const headers = new Headers();
  const sourceContentType = req.headers.get("content-type");
  if (INTERNAL_TOKEN) {
    headers.set("X-Internal-Token", INTERNAL_TOKEN);
  }
  if (sourceContentType && !sourceContentType.includes("multipart/form-data")) {
    headers.set("Content-Type", sourceContentType);
  }

  let body: BodyInit | undefined;
  if (method !== "GET" && method !== "DELETE") {
    if (sourceContentType?.includes("multipart/form-data")) {
      body = await req.formData();
    } else {
      body = await req.text();
    }
  }

  const upstream = await fetch(url, {
    method,
    headers,
    body,
    cache: "no-store",
  });

  const respHeaders = new Headers();
  const upstreamType = upstream.headers.get("content-type");
  if (upstreamType) {
    respHeaders.set("Content-Type", upstreamType);
  }
  const data = await upstream.arrayBuffer();
  return new Response(data, { status: upstream.status, headers: respHeaders });
}

export async function GET(req: NextRequest, ctx: { params: Promise<{ path: string[] }> }) {
  const { path } = await ctx.params;
  return proxy(req, "GET", path);
}

export async function POST(req: NextRequest, ctx: { params: Promise<{ path: string[] }> }) {
  const { path } = await ctx.params;
  return proxy(req, "POST", path);
}

export async function PUT(req: NextRequest, ctx: { params: Promise<{ path: string[] }> }) {
  const { path } = await ctx.params;
  return proxy(req, "PUT", path);
}

export async function PATCH(req: NextRequest, ctx: { params: Promise<{ path: string[] }> }) {
  const { path } = await ctx.params;
  return proxy(req, "PATCH", path);
}

export async function DELETE(req: NextRequest, ctx: { params: Promise<{ path: string[] }> }) {
  const { path } = await ctx.params;
  return proxy(req, "DELETE", path);
}
