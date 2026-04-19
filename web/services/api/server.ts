import "server-only";

import { auth } from "@clerk/nextjs/server";
import { redirect } from "next/navigation";
import { isPreviewAuthMode } from "@/lib/clerk-env";
import { createPreviewApi } from "./preview";
import { createBrowserApi, type BrowserApi } from "./shared";

const clerkJwtTemplate = process.env.CLERK_JWT_TEMPLATE?.trim() || process.env.NEXT_PUBLIC_CLERK_JWT_TEMPLATE?.trim() || undefined;

async function requireServerToken() {
  const { userId, orgId, getToken } = await auth();

  if (!userId) {
    redirect("/login");
  }

  if (!orgId) {
    redirect("/login?organization=required");
  }

  const token = await getToken(clerkJwtTemplate ? { template: clerkJwtTemplate } : undefined);

  if (!token) {
    redirect("/login");
  }

  return token;
}

type ServerApi = Omit<BrowserApi, never>;

export async function getServerApi(): Promise<ServerApi> {
  if (isPreviewAuthMode()) {
    return createPreviewApi();
  }

  return createBrowserApi(requireServerToken);
}
