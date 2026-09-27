import { redirect } from "next/navigation";
import { requireUser } from "@/lib/server-api";
export default async function CatalogStudioRedirect({ params }: { params: Promise<{ id: string }> }) {
  await requireUser();
  const { id } = await params;
  redirect(`/dashboard/course-studio/${id}`);
}
