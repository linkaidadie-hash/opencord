/** Server-side cookie helpers for auth token (JWT) */
import { cookies } from 'next/headers';

const COOKIE_NAME = 'opencord_token';

export function setAuthCookie(token: string) {
  cookies().set(COOKIE_NAME, token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax',
    path: '/',
    maxAge: 60 * 60 * 24 * 7, // 7 days
  });
}

export function getAuthToken(): string | undefined {
  return cookies().get(COOKIE_NAME)?.value;
}

export function clearAuthCookie() {
  cookies().delete(COOKIE_NAME);
}
