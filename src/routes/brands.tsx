import { createFileRoute } from "@tanstack/react-router";
import { BrandsIndex } from "@/components/brand-editor";

export const Route = createFileRoute("/brands")({ component: BrandsIndex });
