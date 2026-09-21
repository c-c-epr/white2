# White²

White² 是一個以 Pico 2W 為核心的空氣品質感測學習文件站，整理空氣品質感測、物聯網、巨量資料與地理資訊系統等主題，並記錄每週的實作進度與參考資料。

文件網站：<https://white2.ccepr.dev>

## 技術

- [Astro](https://astro.build/)
- [Starlight](https://starlight.astro.build/)
- TypeScript
- Cloudflare Workers / Assets

## 專案結構

```text
.
├── public/
├── src/
│   ├── assets/
│   ├── content/
│   │   └── docs/          # 文件內容（Markdown / MDX）
│   │       ├── introduce/ # 專案介紹與材料清單
│   │       ├── reference/ # 參考資料
│   │       └── weeks/     # 每週進度
│   └── content.config.ts
├── astro.config.ts
├── wrangler.jsonc
├── package.json
└── tsconfig.json
```

Starlight 會讀取 `src/content/docs/` 下的 `.md` 與 `.mdx` 文件，並依檔案路徑產生對應頁面。圖片等素材放在 `src/assets/`；不需要經過打包處理的靜態檔案放在 `public/`。

## 開始開發

需要先安裝 [pnpm](https://pnpm.io/installation)。在專案根目錄執行：

```bash
pnpm install
pnpm dev
```

開發伺服器預設位於 <http://localhost:4321>。

## 常用指令

| 指令                  | 用途                     |
| :-------------------- | :----------------------- |
| `pnpm dev`            | 啟動本機開發伺服器       |
| `pnpm build`          | 建立正式版本至 `dist/`   |
| `pnpm preview`        | 預覽正式版本             |
| `pnpm lint`           | 執行 TypeScript 型別檢查 |
| `pnpm format`         | 使用 Prettier 格式化檔案 |
| `pnpm format:check`   | 檢查檔案格式             |
| `pnpm astro ...`      | 執行 Astro CLI 指令      |
| `pnpm generate-types` | 產生 Wrangler 型別       |

## 新增文件

1. 在 `src/content/docs/` 下建立 `.md` 或 `.mdx` 檔案。
2. 在檔案開頭加入 frontmatter，例如 `title` 與 `description`。
3. 將文件放入對應的 `introduce/`、`weeks/` 或 `reference/` 目錄，側邊欄會依 `astro.config.ts` 的設定顯示。
4. 執行 `pnpm dev` 檢查頁面，再執行 `pnpm lint` 與 `pnpm build`。

## 部署

專案使用 Cloudflare 設定檔 `wrangler.jsonc` 部署，正式網域為 `white2.ccepr.dev`。部署前請先完成建置並確認 `dist/` 內容：

```bash
pnpm build
pnpm wrangler deploy
```
