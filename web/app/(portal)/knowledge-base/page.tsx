import { KnowledgeBaseManager } from "@/components/portal/knowledge-base-manager";
import { PageHeader } from "@/components/portal/page-header";
import { getServerApi } from "@/services/api/server";
import { ApiError } from "@/services/api/shared";
import { redirect } from "next/navigation";

export default async function KnowledgeBasePage() {
  const api = await getServerApi();

  try {
    const [{ entries }, tenant] = await Promise.all([api.getKnowledgeBase(), api.getTenant()]);
    const threshold =
      typeof tenant.settings.confidenceThreshold === "number" ? tenant.settings.confidenceThreshold : 0.75;

    return (
      <>
        <PageHeader
          eyebrow="Knowledge base"
          title="The approved source SVMP CS is allowed to answer from."
          copy="Add, update, deactivate, and test FAQ entries before they influence customer replies."
        />
        <KnowledgeBaseManager initialEntries={entries} initialThreshold={threshold} />
      </>
    );
  } catch (error) {
    if (error instanceof ApiError && error.status === 402) {
      redirect("/settings?billing=required");
    }
    throw error;
  }
}
