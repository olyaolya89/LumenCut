import { createFileRoute } from "@tanstack/react-router";
import { handleRestRequest } from "@/lib/studio/rest.server";

export const Route = createFileRoute("/api/media/$")({
  server: {
    handlers: {
      GET: async ({ request }: { request: Request }) => handleRestRequest(request),
      POST: async ({ request }: { request: Request }) => handleRestRequest(request),
    },
  },
});
