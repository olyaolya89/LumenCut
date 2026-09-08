import { createFileRoute } from "@tanstack/react-router";
import { StudioEditor } from "@/components/studio-editor";

export const Route = createFileRoute("/studio/$id")({ component: Page });

function Page() {
  const { id } = Route.useParams();
  return <StudioEditor key={id} id={id} />;
}
