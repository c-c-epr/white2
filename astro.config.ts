import { defineConfig } from "astro/config";
import starlight from "@astrojs/starlight";

import cloudflare from "@astrojs/cloudflare";
import {
  latestWeekPath,
  weekSidebarItems,
  weeklyRedirects,
} from "./src/config/weeks";

import starlightRosePine from "starlight-theme-rose-pine";

// https://astro.build/config
export default defineConfig({
  site: "https://white2.ccepr.dev",
  output: "static",
  redirects: {
    ...weeklyRedirects,
    latest: {
      status: 307,
      destination: latestWeekPath,
    },
  },
  integrations: [
    starlight({
      plugins: [
        starlightRosePine({
          light: { flavor: "dawn", accent: "rose" },
          dark: { flavor: "moon", accent: "rose" },
        }),
      ],
      title: "White²",
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
          items: weekSidebarItems,
        },
        {
          label: "參考資料",
          items: [{ autogenerate: { directory: "reference" } }],
        },
      ],
      pagination: false,
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
