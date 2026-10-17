import { NextResponse } from 'next/server';

export function middleware() {
  const response = NextResponse.next();
  response.headers.set('x-m21-middleware', 'seen');
  return response;
}
export const config = { matcher: ['/dashboard/:path*'] };
