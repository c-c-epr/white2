import { readdirSync } from "node:fs";
import { fileURLToPath } from "node:url";

const weeksDirectory = fileURLToPath(
  new URL("../content/docs/weeks", import.meta.url),
);
const weekSlugs = readdirSync(weeksDirectory)
  .filter((fileName) => /^week\d+\.(?:md|mdx)$/.test(fileName))
  .map((fileName) => fileName.replace(/\.(?:md|mdx)$/, ""))
  .sort((first, second) =>
    first.localeCompare(second, "en", { numeric: true }),
  );

if (weekSlugs.length === 0) {
  throw new Error("No weekly documents found in src/content/docs/weeks.");
}

const latestWeekSlug = weekSlugs.at(-1)!;

export const latestWeekPath = `/weeks/${latestWeekSlug}`;

export const weeklyRedirects = Object.fromEntries(
  weekSlugs.flatMap((slug) => {
    const match = /^week0+(\d+)$/.exec(slug);
    if (!match) return [];

    const unpaddedSlug = `week${Number(match[1])}`;
    return unpaddedSlug === slug
      ? []
      : [[`/weeks/${unpaddedSlug}`, `/weeks/${slug}`]];
  }),
);

export const weekSidebarItems = weekSlugs.map((slug) =>
  slug === latestWeekSlug
    ? { slug: `weeks/${slug}`, badge: "最新" }
    : `weeks/${slug}`,
);
