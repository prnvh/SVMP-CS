import Link from "next/link";
import { SsoCallbackClient } from "@/components/auth/sso-callback-client";
import { isClerkConfigured } from "@/lib/clerk-env";

export const dynamic = "force-dynamic";

export default function SsoCallbackPage() {
  if (!isClerkConfigured()) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-paper p-6 text-ink md:p-10">
        <div className="w-full max-w-md rounded-[8px] border border-line bg-white p-6">
          <p className="text-sm font-semibold text-pine">Google sign-in</p>
          <h1 className="mt-3 text-2xl font-semibold">Authentication is not configured</h1>
          <p className="mt-3 text-sm leading-6 text-ink/62">
            This deployment does not currently have Clerk configured, so Google sign-in cannot complete here yet.
          </p>
          <Link
            href="/login"
            className="mt-6 inline-flex rounded-[8px] border border-line px-4 py-3 text-sm font-semibold hover:border-ink"
          >
            Back to login
          </Link>
        </div>
      </main>
    );
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-paper p-6 text-ink md:p-10">
      <div className="w-full max-w-md rounded-[8px] border border-line bg-white p-6">
        <p className="text-sm font-semibold text-pine">Google sign-in</p>
        <h1 className="mt-3 text-2xl font-semibold">Finishing sign-in</h1>
        <p className="mt-3 text-sm leading-6 text-ink/62">
          SVMP CS is finishing your Google login and opening the portal.
        </p>
        <div className="mt-6">
          <SsoCallbackClient />
        </div>
      </div>
    </main>
  );
}
