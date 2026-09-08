import { createFileRoute } from "@tanstack/react-router";
import { GuidePage } from "@/components/inner-pages";

export const Route = createFileRoute("/guide")({ component: GuidePage });
