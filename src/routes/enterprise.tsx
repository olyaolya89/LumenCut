import { createFileRoute } from "@tanstack/react-router";
import { EnterprisePage } from "@/components/inner-pages";

export const Route = createFileRoute("/enterprise")({ component: EnterprisePage });
