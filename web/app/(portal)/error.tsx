"use client";

export default function PortalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="rounded-[8px] border border-berry/20 bg-white p-6">
      <p className="text-sm font-semibold text-berry">Portal error</p>
      <h1 className="mt-3 text-2xl font-semibold">The portal could not load this view.</h1>
      <p className="mt-3 max-w-2xl text-sm leading-6 text-ink/66">
        {error.message || "A request failed while loading portal data. Try again, or return to settings if billing or access changed."}
      </p>
      <button
        type="button"
        onClick={() => reset()}
        className="mt-6 rounded-[8px] bg-ink px-4 py-3 text-sm font-semibold text-paper hover:bg-pine"
      >
        Try again
      </button>
    </div>
  );
}
