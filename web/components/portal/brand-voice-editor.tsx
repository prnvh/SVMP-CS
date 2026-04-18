"use client";

import { useState, useTransition } from "react";
import { Notice } from "@/components/portal/notice";
import { Panel } from "@/components/portal/panel";
import { useBrowserApi } from "@/services/api/browser";
import { ApiError } from "@/services/api/shared";
import type { BrandVoiceResponse } from "@/services/api/types";

function errorMessage(error: unknown, fallback: string) {
  if (error instanceof ApiError && error.detail) {
    return error.detail;
  }
  if (error instanceof Error && error.message) {
    return error.message;
  }
  return fallback;
}

function linesToList(value: string) {
  return value
    .split("\n")
    .map((item) => item.trim())
    .filter(Boolean);
}

function listToLines(value?: string[]) {
  return value?.join("\n") ?? "";
}

export function BrandVoiceEditor({
  initialBrandVoice,
}: {
  initialBrandVoice: BrandVoiceResponse["brandVoice"];
}) {
  const api = useBrowserApi();
  const [isPending, startTransition] = useTransition();
  const [feedback, setFeedback] = useState<{ tone: "success" | "error"; text: string } | null>(null);
  const [tone, setTone] = useState(initialBrandVoice.tone ?? "");
  const [useWords, setUseWords] = useState(listToLines(initialBrandVoice.use));
  const [avoidWords, setAvoidWords] = useState(listToLines(initialBrandVoice.avoid));
  const [escalationStyle, setEscalationStyle] = useState(initialBrandVoice.escalationStyle ?? "");
  const [exampleReplies, setExampleReplies] = useState(
    initialBrandVoice.exampleReplies?.length
      ? initialBrandVoice.exampleReplies
      : [
          "I can help with that. If the exact order details matter, I will connect you with the team.",
          "Here is the approved answer based on your current knowledge base.",
          "I do not want to guess, so I am escalating this to support.",
        ],
  );

  function saveBrandVoice() {
    setFeedback(null);
    startTransition(async () => {
      try {
        const response = await api.saveBrandVoice({
          tone,
          use: linesToList(useWords),
          avoid: linesToList(avoidWords),
          escalationStyle,
          exampleReplies,
        });
        setFeedback({ tone: "success", text: "Brand voice saved." });
        setTone(response.brandVoice.tone ?? "");
        setUseWords(listToLines(response.brandVoice.use));
        setAvoidWords(listToLines(response.brandVoice.avoid));
        setEscalationStyle(response.brandVoice.escalationStyle ?? "");
        setExampleReplies(response.brandVoice.exampleReplies ?? exampleReplies);
      } catch (error) {
        setFeedback({
          tone: "error",
          text: errorMessage(error, "Unable to save brand voice settings."),
        });
      }
    });
  }

  return (
    <div className="grid gap-6 xl:grid-cols-[1fr_0.9fr]">
      <Panel title="Voice rules" eyebrow="Editable settings">
        <div className="grid gap-5">
          <label className="grid gap-2">
            <span className="text-sm font-semibold">Tone description</span>
            <textarea
              rows={4}
              value={tone}
              onChange={(event) => setTone(event.target.value)}
              className="rounded-[8px] border border-line bg-paper p-3 text-sm outline-none focus:border-pine"
            />
          </label>
          <div className="grid gap-4 md:grid-cols-2">
            <label className="grid gap-2">
              <span className="text-sm font-semibold">Use these words</span>
              <textarea
                rows={5}
                value={useWords}
                onChange={(event) => setUseWords(event.target.value)}
                className="rounded-[8px] border border-line bg-paper p-3 text-sm outline-none focus:border-pine"
              />
            </label>
            <label className="grid gap-2">
              <span className="text-sm font-semibold">Avoid these words</span>
              <textarea
                rows={5}
                value={avoidWords}
                onChange={(event) => setAvoidWords(event.target.value)}
                className="rounded-[8px] border border-line bg-paper p-3 text-sm outline-none focus:border-pine"
              />
            </label>
          </div>
          <label className="grid gap-2">
            <span className="text-sm font-semibold">Escalation style</span>
            <textarea
              rows={3}
              value={escalationStyle}
              onChange={(event) => setEscalationStyle(event.target.value)}
              className="rounded-[8px] border border-line bg-paper p-3 text-sm outline-none focus:border-pine"
            />
          </label>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <p className="text-sm leading-6 text-ink/62">
              Save updates here before they influence any customer-facing reply.
            </p>
            <button
              type="button"
              className="rounded-[8px] bg-ink px-4 py-3 text-sm font-semibold text-paper hover:bg-pine disabled:cursor-not-allowed disabled:opacity-60"
              onClick={saveBrandVoice}
              disabled={isPending}
            >
              {isPending ? "Saving..." : "Save voice"}
            </button>
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

      <div className="space-y-6">
        <Panel title="Example replies" eyebrow="Approved tone">
          <div className="space-y-3">
            {exampleReplies.map((example) => (
              <div key={example} className="rounded-[8px] border border-line bg-paper p-4 text-sm leading-6 text-ink/72">
                {example}
              </div>
            ))}
          </div>
        </Panel>

        <Panel title="Preview" eyebrow="Escalation style">
          <div className="rounded-[8px] border border-line bg-paper p-4">
            <p className="text-sm font-semibold">Current escalation guidance</p>
            <p className="mt-2 text-sm leading-6 text-ink/68">
              {escalationStyle || "Add an escalation style so low-confidence cases stay consistent."}
            </p>
          </div>
        </Panel>
      </div>
    </div>
  );
}
