import Link from "next/link";
import { LoginVerifyClient } from "@/components/auth/login-verify-client";
import { isClerkConfigured } from "@/lib/clerk-env";

function VerificationPanel({
  title,
  copy,
  action,
}: {
  title: string;
  copy: string;
  action?: React.ReactNode;
}) {
  return (
    <main className="flex min-h-screen items-center justify-center bg-paper p-6 text-ink md:p-10">
      <div className="w-full max-w-md rounded-[8px] border border-line bg-white p-6">
        <p className="text-sm font-semibold text-pine">Email verification</p>
        <h1 className="mt-3 text-2xl font-semibold">{title}</h1>
        <p className="mt-3 text-sm leading-6 text-ink/62">{copy}</p>
        <div className="mt-6">{action}</div>
      </div>
    </main>
  );
}

export default function LoginVerifyPage() {
  if (!isClerkConfigured()) {
    return (
      <VerificationPanel
        title="Authentication is not configured"
        copy="This deployment does not currently have Clerk configured, so email-link verification cannot complete here yet."
        action={
          <Link
            href="/login"
            className="inline-flex rounded-[8px] border border-line px-4 py-3 text-sm font-semibold hover:border-ink"
          >
            Back to login
          </Link>
        }
      />
    );
  }

  return <LoginVerifyClient />;
}
