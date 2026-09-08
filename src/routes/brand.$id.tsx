import { createFileRoute } from "@tanstack/react-router";
import { BrandEditor } from "@/components/brand-editor";

export const Route = createFileRoute("/brand/$id")({ component: BrandPage });

function BrandPage() {
  const { id } = Route.useParams();
  return <BrandEditor id={id} />;
}
