import { NextRequest, NextResponse } from "next/server";
import { isAdminAuthorized, unauthorized } from "./lib/admin-auth";

export async function middleware(request: NextRequest) {
  if (!(await isAdminAuthorized(request.headers.get("authorization")))) return unauthorized();
  return NextResponse.next();
}

export const config = { matcher: ["/", "/api/private/:path*"] };
