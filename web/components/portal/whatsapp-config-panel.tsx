"use client";

import { useMemo, useState, useTransition } from "react";
import { EmptyState } from "@/components/portal/empty-state";
import { Notice } from "@/components/portal/notice";
import { Panel } from "@/components/portal/panel";
import { StatusBadge, statusTone } from "@/components/portal/status-badge";
import { useBrowserApi } from "@/services/api/browser";
import { ApiError } from "@/services/api/shared";
import type { IntegrationStatus } from "@/services/api/types";

function errorMessage(error: unknown, fallback: string) {
  if (error instanceof ApiError && error.detail) {
    return error.detail;
  }
  if (error instanceof Error && error.message) {
    return error.message;
  }
  return fallback;
}

export function WhatsAppConfigPanel({
  initialIntegrations,
}: {
  initialIntegrations: IntegrationStatus[];
}) {
  const api = useBrowserApi();
  const [integrations, setIntegrations] = useState(initialIntegrations);
  const [isPending, startTransition] = useTransition();
  const [feedback, setFeedback] = useState<{ tone: "success" | "error"; text: string } | null>(null);

  const whatsapp = useMemo(
    () =>
      integrations.find((integration) => integration.provider === "whatsapp") ?? {
        provider: "whatsapp",
        status: "not_connected",
        health: "unknown",
        setupWarnings: ["WhatsApp status has not been configured."],
      },
    [integrations],
  );

  const future = integrations.filter((integration) => integration.provider !== "whatsapp");
  const [status, setStatus] = useState(whatsapp.status);
  const [health, setHealth] = useState(whatsapp.health ?? "unknown");
  const [setupWarnings, setSetupWarnings] = useState((whatsapp.setupWarnings ?? []).join("\n"));

  function saveWhatsApp() {
    setFeedback(null);
    startTransition(async () => {
      try {
        const updated = await api.saveWhatsAppIntegration({
          status,
          health,
          setupWarnings: setupWarnings
            .split("\n")
            .map((item) => item.trim())
            .filter(Boolean),
        });
        setIntegrations((current) => {
          const remaining = current.filter((integration) => integration.provider !== "whatsapp");
          return [updated, ...remaining];
        });
        setFeedback({ tone: "success", text: "WhatsApp integration status saved." });
      } catch (error) {
        setFeedback({
          tone: "error",
          text: errorMessage(error, "Unable to save WhatsApp integration status."),
        });
      }
    });
  }

  return (
    <div className="grid gap-6 xl:grid-cols-[1fr_0.9fr]">
      <Panel
        title="WhatsApp"
        eyebrow="Live channel"
        action={
          <button
            type="button"
            className="rounded-[8px] bg-ink px-4 py-3 text-sm font-semibold text-paper hover:bg-pine disabled:cursor-not-allowed disabled:opacity-60"
            onClick={saveWhatsApp}
            disabled={isPending}
          >
            {isPending ? "Saving..." : "Configure WhatsApp"}
          </button>
        }
      >
        <div className="space-y-5">
          <div className="flex flex-wrap items-start justify-between gap-3 rounded-[8px] border border-line bg-paper p-5">
            <div>
              <p className="text-lg font-semibold">WhatsApp</p>
              <p className="mt-2 text-sm leading-6 text-ink/64">
                Update the visible status and health checks for the live channel without exposing provider secrets.
              </p>
            </div>
            <StatusBadge tone={statusTone(whatsapp.status)}>{whatsapp.status}</StatusBadge>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <label className="grid gap-2">
              <span className="text-sm font-semibold">Status</span>
              <select
                className="h-11 rounded-[8px] border border-line bg-white px-3 text-sm outline-none focus:border-pine"
                value={status}
                onChange={(event) => setStatus(event.target.value)}
              >
                <option value="connected">connected</option>
                <option value="healthy">healthy</option>
                <option value="warning">warning</option>
                <option value="not_connected">not_connected</option>
              </select>
            </label>
            <label className="grid gap-2">
              <span className="text-sm font-semibold">Health</span>
              <select
                className="h-11 rounded-[8px] border border-line bg-white px-3 text-sm outline-none focus:border-pine"
                value={health}
                onChange={(event) => setHealth(event.target.value)}
              >
                <option value="healthy">healthy</option>
                <option value="warning">warning</option>
                <option value="unknown">unknown</option>
              </select>
            </label>
          </div>

          <label className="grid gap-2">
            <span className="text-sm font-semibold">Setup warnings</span>
            <textarea
              rows={4}
              className="rounded-[8px] border border-line bg-white p-3 text-sm outline-none focus:border-pine"
              value={setupWarnings}
              onChange={(event) => setSetupWarnings(event.target.value)}
              placeholder="One warning per line"
            />
          </label>

          <div className="rounded-[8px] border border-line p-4">
            <p className="text-sm font-semibold">Webhook endpoint</p>
            <p className="mt-2 break-all rounded-[8px] bg-mist px-3 py-2 text-sm text-ink/70">
              https://api.svmpsystems.com/webhook
            </p>
            <p className="mt-3 text-sm leading-6 text-ink/62">
              Provider events are verified, deduplicated, and written before tenant workflows run.
            </p>
          </div>

          {feedback ? (
            <Notice
              title={feedback.tone === "success" ? "Saved" : "Needs attention"}
              copy={feedback.text}
              tone={feedback.tone}
            />
          ) : null}
        </div>
      </Panel>

      <Panel title="Additional channels" eyebrow="Planned integrations">
        {future.length ? (
          <div className="space-y-3">
            {future.map((integration) => (
              <article key={integration.provider} className="rounded-[8px] border border-line p-4">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <h3 className="font-semibold">{integration.provider}</h3>
                  <StatusBadge tone={statusTone(integration.status)}>
                    {integration.status.replace("_", " ")}
                  </StatusBadge>
                </div>
                <p className="mt-3 text-sm leading-6 text-ink/64">
                  {integration.provider} is tracked for this tenant, but WhatsApp remains the current live support channel.
                </p>
              </article>
            ))}
          </div>
        ) : (
          <EmptyState
            title="No additional channels are configured"
            copy="WhatsApp is the active support channel today. Future providers can appear here as they are added for this tenant."
          />
        )}
      </Panel>
    </div>
  );
}
