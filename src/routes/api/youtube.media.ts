import { createFileRoute } from "@tanstack/react-router";
import { handleYoutubeMedia } from "@/lib/studio/youtube-media.server";

export const Route = createFileRoute("/api/youtube/media")({
  server: {
    handlers: {
      GET: async ({ request }: { request: Request }) => handleYoutubeMedia(request),
    },
  },
});
