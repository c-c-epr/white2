export function files(filenames: string[]) {
  return filenames.map((filename) => {
    return {
      label: filename,
      link: `codes/${filename}`,
      badge: { text: "檔案", variant: "tip" as const },
    };
  });
}
