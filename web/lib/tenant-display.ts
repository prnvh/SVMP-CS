import type { MeResponse, TenantResponse } from "@/services/api/types";

const DEMO_TENANT_IDS = new Set(["stay"]);
const DEMO_TENANT_NAMES = new Set(["stay parfums", "stay perfumes"]);
const DEMO_DOMAINS = new Set(["stayparfums.com", "www.stayparfums.com"]);

function normalize(value?: string | null) {
  return value?.trim().toLowerCase() ?? "";
}

export function isDemoTenantValue(value?: string | null) {
  const normalized = normalize(value);
  return DEMO_TENANT_IDS.has(normalized) || DEMO_TENANT_NAMES.has(normalized);
}

export function sanitizeTenantName(value?: string | null) {
  if (!value || isDemoTenantValue(value)) {
    return null;
  }
  return value;
}

export function sanitizeWebsiteUrl(value?: string | null) {
  if (!value) {
    return null;
  }

  try {
    const host = new URL(value).hostname.toLowerCase();
    if (DEMO_DOMAINS.has(host)) {
      return null;
    }
  } catch {
    return value;
  }

  return value;
}

export function sanitizeSupportEmail(value?: string | null) {
  if (!value) {
    return null;
  }

  const [, domain] = value.split("@");
  if (domain && DEMO_DOMAINS.has(domain.toLowerCase())) {
    return null;
  }

  return value;
}

export function tenantDisplayName(me: MeResponse, tenant: TenantResponse) {
  return (
    sanitizeTenantName(tenant.tenantName) ??
    sanitizeTenantName(me.tenantName) ??
    (isDemoTenantValue(me.tenantId) ? null : me.tenantId)
  );
}
