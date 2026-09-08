import { createFileRoute } from "@tanstack/react-router";
import { UsecasesPage } from "@/components/inner-pages";

export const Route = createFileRoute("/usecases")({ component: UsecasesPage });
