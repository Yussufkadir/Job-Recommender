import type { PageLoad } from "./$types";

export const load: PageLoad = async () => {
  return {
    hero: {
      title: "Job Recommender",
      subtitle: "Find tailored roles faster.",
      cta: {
        label: "See how it works",
        href: "/learn-more"
      },
      highlights: [
        { label: "Avg. match score", value: "92%" },
        { label: "Teams onboarded", value: "120+" },
        { label: "Roles parsed daily", value: "15k" }
      ]
    }
  };
};