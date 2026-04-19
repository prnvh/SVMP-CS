"use client";

import { useAuth } from "@clerk/nextjs";
import { isPreviewAuthMode } from "@/lib/clerk-env";
import { createPreviewApi } from "./preview";
import { createBrowserApi } from "./shared";

const clerkJwtTemplate = process.env.NEXT_PUBLIC_CLERK_JWT_TEMPLATE?.trim() || undefined;

export function useBrowserApi() {
  // Client components only receive preview data after the server has already
  // admitted a signed preview session. Production defaults to Clerk mode.
  if (isPreviewAuthMode()) {
    return createPreviewApi();
  }

  const { getToken } = useAuth();

  return createBrowserApi(() => getToken(clerkJwtTemplate ? { template: clerkJwtTemplate } : undefined));
}
