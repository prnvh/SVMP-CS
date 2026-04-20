"use client";

import { useSignIn } from "@clerk/nextjs";
import { useState, useTransition } from "react";
import { MagicLinkSignIn } from "@/components/auth/magic-link-sign-in";

function errorMessage(error: unknown) {
  if (error && typeof error === "object" && "errors" in error && Array.isArray(error.errors)) {
    const firstError = error.errors[0];
    if (firstError && typeof firstError === "object" && "longMessage" in firstError) {
      return String(firstError.longMessage);
    }
    if (firstError && typeof firstError === "object" && "message" in firstError) {
      return String(firstError.message);
    }
  }

  if (error instanceof Error && error.message) {
    return error.message;
  }

  return "Unable to start sign-in right now.";
}

export function ClerkSignInPanel() {
  const { fetchStatus, signIn } = useSignIn();
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  function continueWithGoogle() {
    setError(null);
    startTransition(async () => {
      if (!signIn) {
        setError("Authentication is still loading. Try again in a moment.");
        return;
      }

      try {
        const result = await signIn.sso({
          strategy: "oauth_google",
          redirectUrl: "/dashboard",
          redirectCallbackUrl: "/login/sso-callback",
        });
        if (result.error) {
          setError(errorMessage(result.error));
        }
      } catch (authError) {
        setError(errorMessage(authError));
      }
    });
  }

  return (
    <div className="space-y-6">
      <button
        type="button"
        className="flex w-full items-center justify-center gap-3 rounded-[8px] border border-line bg-white px-4 py-3 text-sm font-semibold hover:border-ink disabled:cursor-not-allowed disabled:opacity-60"
        onClick={continueWithGoogle}
        disabled={!signIn || fetchStatus === "fetching" || isPending}
      >
        <span className="text-base" aria-hidden="true">
          G
        </span>
        {isPending ? "Opening Google..." : "Continue with Google"}
      </button>

      {error ? (
        <div className="rounded-[8px] border border-rose/30 bg-rose/10 p-4 text-sm leading-6 text-rose">
          {error}
        </div>
      ) : null}

      <div className="flex items-center gap-3 text-xs font-semibold uppercase tracking-[0.08em] text-ink/42">
        <span className="h-px flex-1 bg-line" />
        <span>Email fallback</span>
        <span className="h-px flex-1 bg-line" />
      </div>

      <MagicLinkSignIn />
    </div>
  );
}
