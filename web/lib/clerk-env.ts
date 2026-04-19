export type PortalAuthMode = "clerk" | "preview";

export function portalAuthMode() {
  return process.env.NEXT_PUBLIC_PORTAL_AUTH_MODE?.trim().toLowerCase() === "preview"
    ? "preview"
    : "clerk";
}

export function isPreviewAuthMode() {
  return portalAuthMode() === "preview";
}

export function isUnsafePreviewAuthEnabled() {
  return (
    isPreviewAuthMode() &&
    process.env.PORTAL_ALLOW_UNSAFE_PREVIEW_AUTH?.trim().toLowerCase() === "true"
  );
}

export function hasClerkKeys() {
  return Boolean(
    process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY?.trim() &&
      process.env.CLERK_SECRET_KEY?.trim(),
  );
}

export function isClerkConfigured() {
  return portalAuthMode() === "clerk" && hasClerkKeys();
}

export function authConfigurationIssue() {
  if (isUnsafePreviewAuthEnabled() || isClerkConfigured()) {
    return null;
  }

  if (isPreviewAuthMode()) {
    return "Preview auth is disabled until PORTAL_ALLOW_UNSAFE_PREVIEW_AUTH=true is set. Use this only for local or temporary review environments.";
  }

  return "Clerk is the production auth mode, but the Clerk publishable or secret key is missing.";
}
