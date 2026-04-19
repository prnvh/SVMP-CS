import "server-only";

import { auth } from "@clerk/nextjs/server";

export async function getAuthSafe() {
  if (!process.env.CLERK_SECRET_KEY) {
    return { userId: null };
  }

  try {
    return await auth();
  } catch {
    return { userId: null };
  }
}
