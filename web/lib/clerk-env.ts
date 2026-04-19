export function portalAuthMode() {
  return process.env.NEXT_PUBLIC_PORTAL_AUTH_MODE?.trim().toLowerCase() === "clerk"
    ? "clerk"
    : "preview";
}

export function isPreviewAuthMode() {
  return portalAuthMode() === "preview";
}

export function isClerkConfigured() {
  return (
    portalAuthMode() === "clerk" &&
    Boolean(
      process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY?.trim() &&
        process.env.CLERK_SECRET_KEY?.trim(),
    )
  );
}
