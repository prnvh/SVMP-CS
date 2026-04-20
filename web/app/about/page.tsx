import Link from "next/link";
import { Arrow, MarketingFooter, MarketingHeader } from "@/components/marketing/marketing-shell";
import { buildStatus, flow, portalRows, safety } from "@/components/marketing/content";

export default function AboutPage() {
  return (
    <main className="min-h-screen bg-paper text-ink">
      <MarketingHeader />

      <section className="section-pad border-b border-line">
        <div className="mx-auto max-w-7xl py-16 md:py-20 lg:py-24">
          <div className="max-w-4xl">
            <p className="text-[15px] font-semibold text-pine">About SVMP CS</p>
            <h1 className="mt-6 max-w-5xl font-serif text-5xl leading-[1.04] md:text-6xl lg:text-7xl">
              A governed customer support system for WhatsApp-first businesses.
            </h1>
            <p className="mt-7 max-w-3xl text-xl leading-9 text-ink/72">
              SVMP CS is built for teams that want faster customer support without
              losing control over what the AI says, when it escalates, and how each
              answer can be reviewed later.
            </p>
            <div className="mt-10">
              <Link
                href="/pricing"
                className="inline-flex rounded-[8px] bg-ink px-5 py-3 text-[15px] font-semibold text-paper hover:bg-pine"
              >
                See pricing
              </Link>
            </div>
          </div>
        </div>
      </section>

      <section className="section-pad border-b border-line bg-[#F4F7F2]">
        <div className="mx-auto max-w-7xl py-16 md:py-20">
          <div className="grid gap-8 lg:grid-cols-[0.55fr_1.45fr]">
            <div>
              <p className="text-[15px] font-semibold text-pine">How it works</p>
              <h2 className="mt-4 font-serif text-4xl leading-tight md:text-5xl">
                The support loop, end to end.
              </h2>
            </div>
            <div className="grid gap-4 lg:grid-cols-[1fr_auto_1fr_auto_1fr_auto_1fr] lg:items-stretch">
              {flow.map((item, index) => (
                <div key={item.label} className="contents">
                  <article className="rounded-[8px] border border-line bg-paper p-5">
                    <p className="font-serif text-3xl text-berry">0{index + 1}</p>
                    <h3 className="mt-8 text-xl font-semibold">{item.label}</h3>
                    <p className="mt-4 text-[15px] leading-7 text-ink/66">{item.detail}</p>
                  </article>
                  {index < flow.length - 1 ? <Arrow /> : null}
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="section-pad border-b border-line bg-ink text-paper">
        <div className="mx-auto grid max-w-7xl gap-12 py-20 lg:grid-cols-[0.85fr_1.15fr] lg:py-28">
          <div>
            <p className="text-[15px] font-semibold text-citron">Private portal</p>
            <h2 className="mt-5 font-serif text-5xl leading-tight md:text-6xl">
              What the support team actually uses.
            </h2>
            <p className="mt-8 text-xl leading-9 text-paper/72">
              The portal is where a business monitors value, controls answers,
              updates knowledge, reviews escalations, and keeps a governed record
              of what the AI did.
            </p>
          </div>
          <div className="overflow-hidden rounded-[8px] border border-paper/18">
            {portalRows.map(([name, description]) => (
              <div
                key={name}
                className="grid gap-3 border-b border-paper/14 p-5 last:border-b-0 md:grid-cols-[11rem_1fr]"
              >
                <p className="font-semibold">{name}</p>
                <p className="leading-7 text-paper/68">{description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="section-pad border-b border-line">
        <div className="mx-auto grid max-w-7xl gap-12 py-20 lg:grid-cols-[0.7fr_1.3fr] lg:py-28">
          <div>
            <p className="text-[15px] font-semibold text-pine">Governance</p>
            <h2 className="mt-5 font-serif text-5xl leading-tight md:text-6xl">
              Built around control.
            </h2>
          </div>
          <div className="grid gap-px overflow-hidden rounded-[8px] border border-line bg-line md:grid-cols-2">
            {safety.map((item) => (
              <article key={item.title} className="bg-paper p-7">
                <h3 className="text-2xl font-semibold">{item.title}</h3>
                <p className="mt-5 text-[16px] leading-8 text-ink/68">{item.copy}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="section-pad border-b border-line bg-[#F4F7F2]">
        <div className="mx-auto grid max-w-7xl gap-12 py-20 lg:grid-cols-[0.9fr_1.1fr] lg:items-center lg:py-28">
          <div>
            <p className="text-[15px] font-semibold text-pine">Why WhatsApp first</p>
            <h2 className="mt-5 font-serif text-5xl leading-tight md:text-6xl">
              Start where customer conversations already happen.
            </h2>
            <p className="mt-7 text-xl leading-9 text-ink/72">
              SVMP CS starts with one channel and tries to make that workflow work
              well before branching out. The goal is practical support operations,
              not a bloated feature list.
            </p>
          </div>
          <div className="overflow-hidden rounded-[8px] border border-line bg-paper">
            <div className="border-b border-line p-5">
              <p className="text-[13px] text-ink/54">What changes</p>
              <h3 className="mt-1 text-2xl font-semibold">
                From repeat work to governed automation
              </h3>
            </div>
            <div className="grid gap-px bg-line md:grid-cols-2">
              <div className="bg-paper p-6">
                <p className="text-[13px] font-semibold uppercase text-berry">Before</p>
                <ul className="mt-8 space-y-5 text-[16px] leading-7 text-ink/70">
                  <li>Agents repeat the same shipping, pricing, and product answers.</li>
                  <li>WhatsApp threads are fragmented and hard to summarize.</li>
                  <li>Owners cannot easily inspect what was said or why.</li>
                  <li>Knowledge gaps stay hidden until customers complain.</li>
                </ul>
              </div>
              <div className="bg-paper p-6">
                <p className="text-[13px] font-semibold uppercase text-pine">With SVMP CS</p>
                <ul className="mt-8 space-y-5 text-[16px] leading-7 text-ink/70">
                  <li>Safe repeat questions are answered from approved KB entries.</li>
                  <li>Low-confidence questions are escalated with reasons attached.</li>
                  <li>Every decision keeps source, score, provider, and timestamp.</li>
                  <li>Metrics show deflection, hours saved, and missing knowledge.</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="section-pad">
        <div className="mx-auto grid max-w-7xl gap-10 py-14 lg:grid-cols-[0.34fr_1fr]">
          <div>
            <p className="text-[15px] font-semibold">Platform</p>
          </div>
          <div className="grid gap-px overflow-hidden rounded-[8px] border border-line bg-line md:grid-cols-3">
            {buildStatus.map(([title, copy]) => (
              <article key={title} className="bg-paper p-6">
                <h3 className="text-xl font-semibold">{title}</h3>
                <p className="mt-5 text-[15px] leading-7 text-ink/68">{copy}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <MarketingFooter />
    </main>
  );
}
