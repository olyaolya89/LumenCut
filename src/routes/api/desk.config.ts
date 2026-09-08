import { createFileRoute } from "@tanstack/react-router";
import { handlePipelineRequest } from "@/lib/studio/pipeline.server";

export const Route = createFileRoute("/api/desk/config")({
  server: {
    handlers: {
      GET: async ({ request }: { request: Request }) => handlePipelineRequest(request),
      PUT: async ({ request }: { request: Request }) => handlePipelineRequest(request),
      POST: async ({ request }: { request: Request }) => handlePipelineRequest(request),
    },
  },
});
