export const navItems = [
  { label: "Home", href: "/" },
  { label: "About", href: "/about" },
  { label: "Pricing", href: "/pricing" },
] as const;

export const flow = [
  {
    label: "Customer asks on WhatsApp",
    detail: "Messages can arrive as fragments, follow-ups, or repeated questions.",
  },
  {
    label: "SVMP CS checks approved knowledge",
    detail: "It uses the tenant's FAQ, policies, domains, and brand voice.",
  },
  {
    label: "Answer or escalate",
    detail: "High-confidence answers go out. Unclear cases go to a human.",
  },
  {
    label: "Everything is logged",
    detail: "The portal shows the answer, source, score, reason, and status.",
  },
] as const;

export const outcomes = [
  ["For customers", "Fast answers on WhatsApp, without waiting for a human on simple questions."],
  ["For support teams", "Fewer repetitive replies, clearer escalations, and a record of what happened."],
  ["For owners", "A dashboard for savings, safety, knowledge gaps, and AI behavior."],
] as const;

export const portalRows = [
  ["Overview", "Deflection rate, human hours saved, resolution time, safety score"],
  ["Sessions", "Customer question, SVMP CS answer, confidence, source, escalation reason"],
  ["Knowledge base", "Approved FAQs, active state, topic filters, test questions"],
  ["Brand voice", "Tone, words to use, words to avoid, escalation style"],
  ["Governance", "Low-confidence answers, blocked responses, audit trail"],
] as const;

export const safety = [
  {
    title: "Approved knowledge only",
    copy: "SVMP CS answers from the knowledge base and settings the business controls.",
  },
  {
    title: "Confidence threshold",
    copy: "If the score is too low, SVMP CS does not force an answer.",
  },
  {
    title: "Human escalation",
    copy: "Unclear questions are routed for follow-up instead of being guessed at.",
  },
  {
    title: "Audit trail",
    copy: "Every outcome keeps the question, answer, source, score, and reason together.",
  },
] as const;

export const buildStatus = [
  ["Backend", "FastAPI runtime handling authenticated dashboard APIs and WhatsApp intake."],
  ["Data layer", "Tenant, session, knowledge, and governance records stay isolated per organization."],
  ["Portal", "Paid client workspace for setup, operations, billing, and oversight."],
] as const;

export const pricingTiers = [
  {
    name: "Starter rollout",
    label: "For early teams",
    description:
      "A guided setup for teams that want governed WhatsApp support live with approved knowledge and a controlled dashboard rollout.",
    bullets: [
      "WhatsApp-first support setup",
      "Knowledge base onboarding",
      "Brand voice and escalation rules",
      "Shared launch support",
    ],
  },
  {
    name: "Operational plan",
    label: "For active support teams",
    description:
      "A deeper setup for teams that want workflow control, governance visibility, and regular iteration once the support system is live.",
    bullets: [
      "Portal access for your team",
      "Governance and sessions review",
      "Knowledge updates and testing",
      "Billing and rollout coordination",
    ],
  },
  {
    name: "Custom deployment",
    label: "For larger needs",
    description:
      "For teams that need custom rollout planning, more operational support, or a broader deployment path after the initial WhatsApp workflow.",
    bullets: [
      "Custom onboarding path",
      "Dedicated implementation planning",
      "Deeper workflow review",
      "Expansion discussions",
    ],
  },
] as const;
