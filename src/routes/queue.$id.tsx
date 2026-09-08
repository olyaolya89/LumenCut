import { createFileRoute } from "@tanstack/react-router";
import { QueuePage } from "@/components/generate-flow";

export const Route = createFileRoute("/queue/$id")({ component: Page });

function Page() {
  const { id } = Route.useParams();
  return <QueuePage id={id} />;
}
