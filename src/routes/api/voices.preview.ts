import { createFileRoute } from "@tanstack/react-router";
import { handleRestRequest } from "@/lib/studio/rest.server";

export const Route = createFileRoute("/api/voices/preview")({
  server: {
    handlers: {
      POST: async ({ request }: { request: Request }) => handleRestRequest(request),
    },
  },
});
