import { createFileRoute } from "@tanstack/react-router";
import { TestimonialsPage } from "@/components/inner-pages";

export const Route = createFileRoute("/testimonials")({ component: TestimonialsPage });
