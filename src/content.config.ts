import { defineCollection } from "astro:content";
import { glob } from "astro/loaders";
import { docsLoader } from "@astrojs/starlight/loaders";
import { docsSchema, i18nSchema } from "@astrojs/starlight/schema";

export const collections = {
  docs: defineCollection({ loader: docsLoader(), schema: docsSchema() }),
  i18n: defineCollection({
    loader: glob({
      pattern: "**/*.{json,yaml,yml}",
      base: "./src/content/i18n",
    }),
    schema: i18nSchema(),
  }),
};
