import { createFileRoute } from "@tanstack/react-router";
import { handleRestRequest } from "@/lib/studio/rest.server";

export const Route = createFileRoute("/api/projects/$")({
  server: {
    handlers: {
      GET: async ({ request }: { request: Request }) => handleRestRequest(request),
      POST: async ({ request }: { request: Request }) => handleRestRequest(request),
      PUT: async ({ request }: { request: Request }) => handleRestRequest(request),
      PATCH: async ({ request }: { request: Request }) => handleRestRequest(request),
      DELETE: async ({ request }: { request: Request }) => handleRestRequest(request),
    },
  },
});
