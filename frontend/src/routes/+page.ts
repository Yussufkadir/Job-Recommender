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
    }
  };
};