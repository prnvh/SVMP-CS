"use client";

import { useClerk, useSignIn } from "@clerk/nextjs";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

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

export function LoginVerifyClient() {
  const router = useRouter();
  const { setActive } = useClerk();
  const { signIn, fetchStatus } = useSignIn();
  const [isActivating, setIsActivating] = useState(false);

  const verification = signIn?.emailLink.verification;

  useEffect(() => {
    if (!verification?.createdSessionId || verification.status !== "verified" || isActivating) {
      return;
    }

    let cancelled = false;
    setIsActivating(true);

    void setActive?.({ session: verification.createdSessionId }).then(() => {
      if (!cancelled) {
        router.replace("/dashboard");
      }
    });

    return () => {
      cancelled = true;
    };
  }, [isActivating, router, setActive, verification]);

  if (!signIn && fetchStatus === "fetching") {
    return (
      <VerificationPanel
        title="Verifying your link"
        copy="Hold on while SVMP CS confirms this sign-in link and prepares your session."
      />
    );
  }

  if (!verification) {
    return (
      <VerificationPanel
        title="Open the link from your email"
        copy="This page completes a magic-link sign-in after you open the verification link that was sent to your inbox."
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

  if (verification.status === "expired") {
    return (
      <VerificationPanel
        title="This sign-in link expired"
        copy="Email links are time-limited for safety. Request a fresh one from the login screen."
        action={
          <Link
            href="/login"
            className="inline-flex rounded-[8px] bg-ink px-4 py-3 text-sm font-semibold text-paper hover:bg-pine"
          >
            Request a new link
          </Link>
        }
      />
    );
  }

  if (verification.status === "failed") {
    return (
      <VerificationPanel
        title="The sign-in link could not be verified"
        copy="The verification step failed before a portal session could be created. Request a new link and try again."
        action={
          <Link
            href="/login"
            className="inline-flex rounded-[8px] bg-ink px-4 py-3 text-sm font-semibold text-paper hover:bg-pine"
          >
            Back to login
          </Link>
        }
      />
    );
  }

  if (verification.status === "client_mismatch") {
    return (
      <VerificationPanel
        title="Open the link in the same browser"
        copy="This Clerk instance requires the email link to be completed on the same device and browser where the sign-in started."
        action={
          <Link
            href="/login"
            className="inline-flex rounded-[8px] bg-ink px-4 py-3 text-sm font-semibold text-paper hover:bg-pine"
          >
            Return to login
          </Link>
        }
      />
    );
  }

  return (
    <VerificationPanel
      title="Signing you in"
      copy="Your email link was verified. SVMP CS is activating the portal session now."
    />
  );
}
