"use client";

import { useAuth } from "@clerk/nextjs";
import { createBrowserApi } from "./shared";

const clerkJwtTemplate = process.env.NEXT_PUBLIC_CLERK_JWT_TEMPLATE?.trim() || undefined;

export function useBrowserApi() {
  const { getToken } = useAuth();

  return createBrowserApi(() => getToken(clerkJwtTemplate ? { template: clerkJwtTemplate } : undefined));
}
