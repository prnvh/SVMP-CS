"use client";

import { useState } from "react";

export function PreviewLogin() {
  const [email, setEmail] = useState("prnvvh@gmail.com");

  function openPortal() {
    const normalizedEmail = email.trim() || "prnvvh@gmail.com";
    document.cookie = "svmp_preview_session=owner; path=/; max-age=604800; SameSite=Lax";
    window.localStorage.setItem("svmp_preview_email", normalizedEmail);
    window.location.assign("/dashboard");
  }

  return (
    <div className="space-y-5">
      <div className="rounded-[8px] border border-citron bg-citron/20 p-4 text-sm leading-6 text-ink/72">
        Preview mode is on. Use this built-in login to review the portal without Clerk.
      </div>

      <label className="grid gap-2">
        <span className="text-sm font-semibold">Portal email</span>
        <input
          type="email"
          className="h-12 rounded-[8px] border border-line bg-paper px-4 text-sm outline-none focus:border-pine"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
        />
      </label>

      <button
        type="button"
        className="w-full rounded-[8px] bg-ink px-4 py-3 text-sm font-semibold text-paper hover:bg-pine"
        onClick={openPortal}
      >
        Open customer portal
      </button>

      <div className="rounded-[8px] border border-line bg-paper p-4 text-sm leading-6 text-ink/64">
        Production auth is paused for now. When we are ready, setting{" "}
        <span className="font-semibold">NEXT_PUBLIC_PORTAL_AUTH_MODE=clerk</span> turns Clerk back on.
      </div>
    </div>
  );
}
