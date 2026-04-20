import { PricingPageClient } from "@/components/marketing/pricing-page-client";
import { MarketingFooter, MarketingHeader } from "@/components/marketing/marketing-shell";

export default function PricingPage() {
  return (
    <main className="min-h-screen bg-paper text-ink">
      <MarketingHeader />
      <PricingPageClient />
      <MarketingFooter />
    </main>
  );
}
