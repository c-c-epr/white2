import { defineConfig } from "astro/config";
import starlight from "@astrojs/starlight";

import cloudflare from "@astrojs/cloudflare";

// https://astro.build/config
export default defineConfig({
  site: "https://white2.ccepr.dev",
  output: "static",
  integrations: [
    starlight({
      title: "White²",
      disable404Route: true,
      head: [
        {
          tag: "script",
          attrs: {
            defer: true,
            src: "https://cloud.umami.is/script.js",
            "data-website-id": "5302d773-69e9-4fa8-9bfb-8113817d934c",
          },
        },
      ],
      locales: {
        root: { label: "繁體中文", lang: "zh-TW" },
      },
      social: [],
      sidebar: [
        {
          label: "介紹",
          items: ["introduce/introduce", "introduce/material"],
        },
        {
          label: "每周進度",
          items: [{ autogenerate: { directory: "weeks" } }],
        },
        {
          label: "參考資料",
          items: [{ autogenerate: { directory: "reference" } }],
        },
      ],
      editLink: {
        baseUrl: "https://github.com/c-c-epr/white2/tree/main/",
      },
    }),
  ],
  vite: {
    build: {
      rollupOptions: {
        onwarn(warning, warn) {
          if (warning.code === "MODULE_LEVEL_DIRECTIVE") return;
          warn(warning);
        },
      },
    },
  },
  session: false,
  adapter: cloudflare({
    imageService: "compile",
  }),
});
