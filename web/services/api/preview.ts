import type { BrowserApi } from "./shared";
import type {
  BrandVoiceResponse,
  GovernanceLog,
  IntegrationStatus,
  KnowledgeBaseEntry,
  MeResponse,
  SessionSummary,
  TenantResponse,
} from "./types";
import type { PreviewSession } from "@/lib/preview-auth";

const now = new Date().toISOString();

const previewKnowledgeBase: KnowledgeBaseEntry[] = [];
const previewSessions: SessionSummary[] = [];
const previewGovernanceLogs: GovernanceLog[] = [];

const previewIntegrations: IntegrationStatus[] = [
  {
    tenantId: "preview",
    provider: "whatsapp",
    status: "not_connected",
    health: "unknown",
    setupWarnings: ["WhatsApp is not connected for this workspace yet."],
    updatedAt: null,
  },
];

function overviewMetrics() {
  return {
    deflectionRate: 0,
    aiResolved: 0,
    humanEscalated: 0,
    activeSessions: 0,
    activeKnowledgeEntries: 0,
    humanHoursSaved: 0,
    safetyScore: null,
  };
}

function emptySession(id: string): SessionSummary {
  return {
    id,
    provider: "whatsapp",
    status: "pending",
    dashboardStatus: "pending",
    latestMessage: null,
    question: null,
    customer: null,
    confidence: null,
    similarity: null,
    source: null,
    answer: null,
    escalationReason: null,
    transcript: [],
    messages: [],
    createdAt: null,
    updatedAt: null,
  };
}

export function createPreviewApi(session?: Pick<PreviewSession, "email" | "tenantId" | "tenantName" | "role">): BrowserApi {
  const tenantId = session?.tenantId?.trim() || "preview";
  const tenantName = session?.tenantName?.trim() || "Preview workspace";
  const role = session?.role ?? "owner";

  const me: MeResponse = {
    userId: "preview-user",
    email: session?.email ?? null,
    organizationId: tenantId,
    tenantId,
    tenantName,
    role,
    subscriptionStatus: "none",
    hasActiveSubscription: false,
    allowedActions: ["billing", "team", "integrations", "knowledge_base", "brand_voice", "sessions", "metrics"],
  };

  const tenant: TenantResponse = {
    tenantId,
    tenantName,
    websiteUrl: null,
    industry: null,
    supportEmail: null,
    domains: [],
    settings: {
      confidenceThreshold: 0.75,
      autoAnswerEnabled: false,
    },
    brandVoice: {},
    onboarding: {
      status: "pending",
      steps: {
        profile: false,
        brandVoice: false,
        knowledgeBase: false,
        whatsapp: false,
        testConversation: false,
      },
    },
    billing: {
      status: "none",
      hasActiveSubscription: false,
    },
  };

  return {
    getMe: async () => me,
    getTenant: async () => tenant,
    saveTenant: async (payload) => ({
      ...tenant,
      tenantName: typeof payload.tenantName === "string" ? payload.tenantName : tenant.tenantName,
      websiteUrl: typeof payload.websiteUrl === "string" ? payload.websiteUrl : tenant.websiteUrl,
      supportEmail: typeof payload.supportEmail === "string" ? payload.supportEmail : tenant.supportEmail,
      industry: typeof payload.industry === "string" ? payload.industry : tenant.industry,
      settings:
        payload.settings && typeof payload.settings === "object"
          ? { ...tenant.settings, ...payload.settings }
          : tenant.settings,
    }),
    getOverview: async () => ({
      tenantId,
      metrics: overviewMetrics(),
      recentActivity: previewGovernanceLogs,
      setupWarnings: [
        "Preview mode does not include live tenant metrics.",
        "Connect a real backend workspace before relying on portal values.",
      ],
      systemHealth: {
        status: "unknown",
        subscription: "none",
      },
    }),
    getMetrics: async () => ({
      tenantId,
      decisionCounts: {
        answered: 0,
        escalated: 0,
        closed: 0,
        total: 0,
      },
      deflectionRate: 0,
      humanHoursSaved: 0,
    }),
    getSessions: async () => ({
      tenantId,
      sessions: previewSessions,
    }),
    getSession: async (id) => ({
      tenantId,
      session: emptySession(id),
      governanceLogs: previewGovernanceLogs,
    }),
    getKnowledgeBase: async () => ({
      tenantId,
      entries: previewKnowledgeBase,
    }),
    createKnowledgeEntry: async (payload) => ({
      ...payload,
      id: `kb_preview_${Date.now()}`,
      createdAt: now,
      updatedAt: now,
    }),
    updateKnowledgeEntry: async (id, payload) => ({
      id,
      domainId: typeof payload.domainId === "string" ? payload.domainId : "",
      question: typeof payload.question === "string" ? payload.question : "",
      answer: typeof payload.answer === "string" ? payload.answer : "",
      tags: Array.isArray(payload.tags) ? payload.tags.filter((value): value is string => typeof value === "string") : [],
      active: typeof payload.active === "boolean" ? payload.active : true,
      createdAt: now,
      updatedAt: now,
    }),
    deleteKnowledgeEntry: async (id) => ({
      id,
      domainId: "",
      question: "",
      answer: "",
      tags: [],
      active: false,
      createdAt: now,
      updatedAt: now,
    }),
    testQuestion: async (payload) => ({
      tenantId,
      question: payload.question.trim(),
      domainId: null,
      dryRun: true,
      decision: "insufficient_data",
      response: null,
      matchedKnowledgeBaseEntry: null,
      confidenceScore: null,
      threshold: payload.confidenceThreshold ?? 0.75,
      reason: "Preview mode does not include live approved knowledge yet.",
      entriesConsidered: 0,
    }),
    getBrandVoice: async (): Promise<BrandVoiceResponse> => ({
      tenantId,
      brandVoice: tenant.brandVoice,
    }),
    saveBrandVoice: async (payload) => ({
      tenantId,
      brandVoice: {
        ...tenant.brandVoice,
        ...payload,
      },
    }),
    getGovernance: async () => ({
      tenantId,
      logs: previewGovernanceLogs,
    }),
    getIntegrations: async () => ({
      tenantId,
      integrations: previewIntegrations.map((integration) => ({ ...integration, tenantId })),
    }),
    saveWhatsAppIntegration: async (payload) => ({
      ...previewIntegrations[0],
      ...payload,
      provider: "whatsapp",
      tenantId,
      updatedAt: now,
    }),
    createCheckoutSession: async () => ({ id: "preview_checkout", url: "/settings?billing=preview" }),
    createPortalSession: async () => ({ id: "preview_portal", url: "/settings?billing=preview" }),
  };
}
