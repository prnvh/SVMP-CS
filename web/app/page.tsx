import Link from "next/link";
import { outcomes } from "@/components/marketing/content";
import { MarketingFooter, MarketingHeader } from "@/components/marketing/marketing-shell";

export default function Home() {
  return (
    <main className="min-h-screen bg-paper text-ink">
      <MarketingHeader />

      <section className="section-pad border-b border-line">
        <div className="mx-auto max-w-7xl py-16 md:py-20 lg:py-24">
          <div className="max-w-4xl">
            <p className="text-[15px] font-semibold text-pine">
              AI support for WhatsApp-first businesses
            </p>
            <h1 className="mt-6 max-w-5xl font-serif text-5xl leading-[1.04] md:text-6xl lg:text-7xl">
              SVMP CS answers customer questions from your approved knowledge base.
            </h1>
            <p className="mt-7 max-w-3xl text-xl leading-9 text-ink/72">
              It connects to WhatsApp, understands fragmented customer messages, answers only when confidence is high, escalates the rest, and shows every decision in a private dashboard.
            </p>
          </div>

          <div className="mt-10 flex flex-col gap-3 sm:flex-row">
            <Link
              href="/about"
              className="rounded-[8px] bg-ink px-5 py-3 text-center text-[15px] font-semibold text-paper hover:bg-pine"
            >
              About the product
            </Link>
            <Link
              href="/pricing"
              className="rounded-[8px] border border-line px-5 py-3 text-center text-[15px] font-semibold hover:border-ink"
            >
              See pricing
            </Link>
          </div>

          <div className="mt-14 grid gap-px overflow-hidden rounded-[8px] border border-line bg-line lg:grid-cols-3">
            {outcomes.map(([title, copy]) => (
              <div key={title} className="bg-paper p-6">
                <p className="text-[15px] font-semibold">{title}</p>
                <p className="mt-4 text-[16px] leading-8 text-ink/68">{copy}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="section-pad border-b border-line bg-[#F4F7F2]">
        <div className="mx-auto grid max-w-7xl gap-12 py-20 lg:grid-cols-[0.85fr_1.15fr] lg:items-center lg:py-28">
          <div>
            <p className="text-[15px] font-semibold text-pine">Product surface</p>
            <h2 className="mt-5 font-serif text-5xl leading-tight md:text-6xl">
              A support system, not a loose chatbot.
            </h2>
            <p className="mt-7 text-xl leading-9 text-ink/72">
              The dashboard is where a business controls what SVMP CS knows, how it
              speaks, when it escalates, and what it did in each customer conversation.
            </p>
          </div>

          <div className="overflow-hidden rounded-[8px] border border-line bg-white">
            <img
              src="/portal-overview.png"
              alt="SVMP CS customer portal overview dashboard"
              className="block w-full"
            />
          </div>
        </div>
      </section>

      <section className="section-pad border-b border-line">
        <div className="mx-auto grid max-w-7xl gap-12 py-20 lg:grid-cols-[0.9fr_1.1fr] lg:items-center lg:py-28">
          <div>
            <p className="text-[15px] font-semibold text-pine">Why it matters</p>
            <h2 className="mt-5 font-serif text-5xl leading-tight md:text-6xl">
              Built for real support operations.
            </h2>
            <p className="mt-7 text-xl leading-9 text-ink/72">
              SVMP CS is meant for teams that need fast responses, clear escalations,
              and a governed view of what the AI is doing, without turning the whole
              homepage into a product manual.
            </p>
          </div>
          <div className="grid gap-px overflow-hidden rounded-[8px] border border-line bg-line md:grid-cols-2">
            <article className="bg-paper p-7">
              <h3 className="text-2xl font-semibold">Governed responses</h3>
              <p className="mt-5 text-[16px] leading-8 text-ink/68">
                Answers come from approved knowledge with confidence checks and
                escalation rules around them.
              </p>
            </article>
            <article className="bg-paper p-7">
              <h3 className="text-2xl font-semibold">Private portal</h3>
              <p className="mt-5 text-[16px] leading-8 text-ink/68">
                Teams get one place to manage knowledge, review sessions, watch
                metrics, and control rollout.
              </p>
            </article>
            <article className="bg-paper p-7">
              <h3 className="text-2xl font-semibold">WhatsApp first</h3>
              <p className="mt-5 text-[16px] leading-8 text-ink/68">
                The first live flow is focused on one support channel working well
                instead of trying to cover every channel at once.
              </p>
            </article>
            <article className="bg-paper p-7">
              <h3 className="text-2xl font-semibold">Operational clarity</h3>
              <p className="mt-5 text-[16px] leading-8 text-ink/68">
                Owners and support teams can inspect answers, escalations, missing
                knowledge, and system behavior.
              </p>
            </article>
          </div>
        </div>
      </section>

      <MarketingFooter />
    </main>
  );
}
