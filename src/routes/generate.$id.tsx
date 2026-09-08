import { createFileRoute } from "@tanstack/react-router";
import { GenerateFlow } from "@/components/generate-flow";

export const Route = createFileRoute("/generate/$id")({ component: Page });

function Page() {
  const { id } = Route.useParams();
  return <GenerateFlow id={id} />;
}
