"use client";

import { useMemo, useState, useTransition } from "react";
import { EmptyState } from "@/components/portal/empty-state";
import { Notice } from "@/components/portal/notice";
import { Panel } from "@/components/portal/panel";
import { StatusBadge } from "@/components/portal/status-badge";
import { useBrowserApi } from "@/services/api/browser";
import { ApiError } from "@/services/api/shared";
import type { KnowledgeBaseEntry, TestQuestionResponse } from "@/services/api/types";

function formatTimestamp(value?: string | null) {
  if (!value) {
    return "Recently updated";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function entryTags(value: string) {
  return value
    .split(",")
    .map((tag) => tag.trim())
    .filter(Boolean);
}

function errorMessage(error: unknown, fallback: string) {
  if (error instanceof ApiError && error.detail) {
    return error.detail;
  }
  if (error instanceof Error && error.message) {
    return error.message;
  }
  return fallback;
}

export function KnowledgeBaseManager({
  initialEntries,
  initialThreshold,
}: {
  initialEntries: KnowledgeBaseEntry[];
  initialThreshold: number;
}) {
  const api = useBrowserApi();
  const [entries, setEntries] = useState(initialEntries);
  const [search, setSearch] = useState("");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [formState, setFormState] = useState({
    domainId: "",
    question: "",
    answer: "",
    tags: "",
    active: true,
  });
  const [testQuestion, setTestQuestion] = useState("Do you offer free shipping?");
  const [testResult, setTestResult] = useState<TestQuestionResponse | null>(null);
  const [feedback, setFeedback] = useState<{ tone: "success" | "error"; text: string } | null>(null);
  const [isPending, startTransition] = useTransition();
  const activeEntries = entries.filter((entry) => entry.active).length;

  const filteredEntries = useMemo(() => {
    const normalized = search.trim().toLowerCase();
    if (!normalized) {
      return entries;
    }
    return entries.filter((entry) =>
      [entry.domainId, entry.question, entry.answer, ...entry.tags].some((value) =>
        value.toLowerCase().includes(normalized),
      ),
    );
  }, [entries, search]);

  function resetForm() {
    setEditingId(null);
    setFormState({
      domainId: "",
      question: "",
      answer: "",
      tags: "",
      active: true,
    });
  }

  function beginEdit(entry: KnowledgeBaseEntry) {
    setEditingId(entry.id);
    setFormState({
      domainId: entry.domainId,
      question: entry.question,
      answer: entry.answer,
      tags: entry.tags.join(", "),
      active: entry.active,
    });
  }

  function submitEntry() {
    setFeedback(null);
    startTransition(async () => {
      try {
        const payload = {
          domainId: formState.domainId.trim(),
          question: formState.question.trim(),
          answer: formState.answer.trim(),
          tags: entryTags(formState.tags),
          active: formState.active,
        };

        if (editingId) {
          const updated = await api.updateKnowledgeEntry(editingId, payload);
          setEntries((current) => current.map((entry) => (entry.id === editingId ? updated : entry)));
          setFeedback({ tone: "success", text: "Knowledge base entry updated." });
        } else {
          const created = await api.createKnowledgeEntry(payload);
          setEntries((current) => [created, ...current]);
          setFeedback({ tone: "success", text: "Knowledge base entry created." });
        }
        resetForm();
      } catch (error) {
        setFeedback({
          tone: "error",
          text: errorMessage(error, "Unable to save this knowledge base entry."),
        });
      }
    });
  }

  function deactivateEntry(id: string) {
    setFeedback(null);
    startTransition(async () => {
      try {
        const updated = await api.deleteKnowledgeEntry(id);
        setEntries((current) => current.map((entry) => (entry.id === id ? updated : entry)));
        setFeedback({ tone: "success", text: "Knowledge base entry deactivated." });
      } catch (error) {
        setFeedback({
          tone: "error",
          text: errorMessage(error, "Unable to deactivate this knowledge base entry."),
        });
      }
    });
  }

  function runTestQuestion() {
    setFeedback(null);
    startTransition(async () => {
      try {
        const result = await api.testQuestion({
          question: testQuestion,
          confidenceThreshold: initialThreshold,
        });
        setTestResult(result);
      } catch (error) {
        setFeedback({
          tone: "error",
          text: errorMessage(error, "Unable to test this customer question."),
        });
      }
    });
  }

  return (
    <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
      <Panel title="FAQ entries" eyebrow={`${activeEntries} active`}>
        <div className="mb-4 grid gap-3 sm:grid-cols-[1fr_auto]">
          <input
            aria-label="Search knowledge base"
            placeholder="Search question, answer, topic, or tag"
            className="h-11 rounded-[8px] border border-line bg-paper px-3 text-sm outline-none focus:border-pine"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
          <button
            type="button"
            className="rounded-[8px] border border-line bg-white px-4 py-3 text-sm font-semibold hover:border-ink"
            onClick={resetForm}
          >
            Add FAQ
          </button>
        </div>

        <div className="space-y-4">
          <div className="rounded-[8px] border border-line bg-paper p-4">
            <div className="grid gap-4">
              <div className="grid gap-4 md:grid-cols-2">
                <label className="grid gap-2">
                  <span className="text-sm font-semibold">Topic / domain</span>
                  <input
                    className="h-11 rounded-[8px] border border-line bg-white px-3 text-sm outline-none focus:border-pine"
                    value={formState.domainId}
                    onChange={(event) => setFormState((current) => ({ ...current, domainId: event.target.value }))}
                    placeholder="shipping"
                  />
                </label>
                <label className="grid gap-2">
                  <span className="text-sm font-semibold">Tags</span>
                  <input
                    className="h-11 rounded-[8px] border border-line bg-white px-3 text-sm outline-none focus:border-pine"
                    value={formState.tags}
                    onChange={(event) => setFormState((current) => ({ ...current, tags: event.target.value }))}
                    placeholder="shipping, checkout"
                  />
                </label>
              </div>
              <label className="grid gap-2">
                <span className="text-sm font-semibold">Question</span>
                <input
                  className="h-11 rounded-[8px] border border-line bg-white px-3 text-sm outline-none focus:border-pine"
                  value={formState.question}
                  onChange={(event) => setFormState((current) => ({ ...current, question: event.target.value }))}
                  placeholder="Do you offer free shipping?"
                />
              </label>
              <label className="grid gap-2">
                <span className="text-sm font-semibold">Answer</span>
                <textarea
                  rows={4}
                  className="rounded-[8px] border border-line bg-white p-3 text-sm outline-none focus:border-pine"
                  value={formState.answer}
                  onChange={(event) => setFormState((current) => ({ ...current, answer: event.target.value }))}
                  placeholder="Free shipping is available on eligible orders..."
                />
              </label>
              <div className="flex flex-wrap items-center justify-between gap-3">
                <label className="flex items-center gap-2 text-sm font-semibold">
                  <input
                    type="checkbox"
                    checked={formState.active}
                    onChange={(event) => setFormState((current) => ({ ...current, active: event.target.checked }))}
                  />
                  Entry is active
                </label>
                <div className="flex flex-wrap gap-2">
                  {editingId ? (
                    <button
                      type="button"
                      className="rounded-[8px] border border-line bg-white px-4 py-3 text-sm font-semibold hover:border-ink"
                      onClick={resetForm}
                    >
                      Cancel edit
                    </button>
                  ) : null}
                  <button
                    type="button"
                    className="rounded-[8px] bg-ink px-4 py-3 text-sm font-semibold text-paper hover:bg-pine disabled:cursor-not-allowed disabled:opacity-60"
                    onClick={submitEntry}
                    disabled={
                      isPending ||
                      !formState.domainId.trim() ||
                      !formState.question.trim() ||
                      !formState.answer.trim()
                    }
                  >
                    {isPending ? "Saving..." : editingId ? "Save changes" : "Create entry"}
                  </button>
                </div>
              </div>
            </div>
          </div>

          {feedback ? (
            <Notice
              title={feedback.tone === "success" ? "Saved" : "Needs attention"}
              copy={feedback.text}
              tone={feedback.tone}
            />
          ) : null}

          <div className="space-y-3">
            {filteredEntries.length ? (
              filteredEntries.map((entry) => (
                <article key={entry.id} className="rounded-[8px] border border-line p-4">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <p className="text-xs font-semibold uppercase text-pine">{entry.domainId}</p>
                      <h3 className="mt-2 text-lg font-semibold">{entry.question}</h3>
                    </div>
                    <StatusBadge tone={entry.active ? "green" : "neutral"}>
                      {entry.active ? "active" : "inactive"}
                    </StatusBadge>
                  </div>
                  <p className="mt-3 text-sm leading-6 text-ink/68">{entry.answer}</p>
                  <div className="mt-4 flex flex-wrap items-center gap-2">
                    {entry.tags.map((tag) => (
                      <span key={tag} className="rounded-[8px] bg-mist px-2.5 py-1 text-xs font-semibold text-ink/62">
                        {tag}
                      </span>
                    ))}
                    <span className="ml-auto text-xs text-ink/52">Updated {formatTimestamp(entry.updatedAt)}</span>
                  </div>
                  <div className="mt-4 flex flex-wrap gap-2">
                    <button
                      type="button"
                      className="rounded-[8px] border border-line bg-white px-3 py-2 text-sm font-semibold hover:border-ink"
                      onClick={() => beginEdit(entry)}
                    >
                      Edit
                    </button>
                    {entry.active ? (
                      <button
                        type="button"
                        className="rounded-[8px] border border-line bg-white px-3 py-2 text-sm font-semibold hover:border-ink"
                        onClick={() => deactivateEntry(entry.id)}
                      >
                        Deactivate
                      </button>
                    ) : null}
                  </div>
                </article>
              ))
            ) : (
              <EmptyState
                title="No knowledge matches this search"
                copy="Try a broader search, or add the missing answer as a new approved FAQ."
              />
            )}
          </div>
        </div>
      </Panel>

      <div className="space-y-6">
        <Panel title="Test this KB" eyebrow="Dry run">
          <label className="text-sm font-semibold" htmlFor="kb-test">
            Customer question
          </label>
          <textarea
            id="kb-test"
            rows={5}
            value={testQuestion}
            onChange={(event) => setTestQuestion(event.target.value)}
            placeholder="Ask something a customer would ask on WhatsApp"
            className="mt-3 w-full rounded-[8px] border border-line bg-paper p-3 text-sm outline-none focus:border-pine"
          />
          <button
            type="button"
            className="mt-4 rounded-[8px] bg-ink px-4 py-3 text-sm font-semibold text-paper hover:bg-pine disabled:cursor-not-allowed disabled:opacity-60"
            onClick={runTestQuestion}
            disabled={isPending || !testQuestion.trim()}
          >
            {isPending ? "Testing..." : "Test question"}
          </button>
          <div className="mt-5 rounded-[8px] border border-line bg-paper p-4">
            <p className="text-sm font-semibold">Preview result</p>
            {testResult ? (
              <div className="mt-2 space-y-2 text-sm leading-6 text-ink/66">
                <p>
                  Decision: <span className="font-semibold">{testResult.decision}</span>
                </p>
                <p>
                  Confidence:{" "}
                  <span className="font-semibold">
                    {typeof testResult.confidenceScore === "number"
                      ? testResult.confidenceScore.toFixed(2)
                      : "n/a"}
                  </span>
                </p>
                <p>{testResult.reason}</p>
                {testResult.response ? <p>{testResult.response}</p> : null}
              </div>
            ) : (
              <p className="mt-2 text-sm leading-6 text-ink/66">
                Run a dry test to see whether the current knowledge base would answer or escalate.
              </p>
            )}
          </div>
        </Panel>

        <Panel title="KB gap insights" eyebrow="Needs coverage">
          <div className="space-y-3 text-sm leading-6 text-ink/68">
            <p>Search, add, and test real tenant answers before switching auto-answering on for a topic.</p>
            <p>The backend stays authoritative for confidence thresholds and tenant scope on every test question.</p>
          </div>
        </Panel>
      </div>
    </div>
  );
}
