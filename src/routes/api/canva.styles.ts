import { createFileRoute } from "@tanstack/react-router";
import { handleRestRequest } from "@/lib/studio/rest.server";

export const Route = createFileRoute("/api/canva/styles")({
  server: {
    handlers: {
      GET: async ({ request }: { request: Request }) => handleRestRequest(request),
    },
  },
});
