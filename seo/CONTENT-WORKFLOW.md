# HomesteadCalc 内容更新工作流（配合 keyword-library.csv）

> 本文件是每次定期内容更新的执行规范。词库：`seo/keyword-library.csv`（204 个长尾词，13 个分类轮转排序）。
> 节奏：**每周 2 篇**（周一、周四各 1 篇），严格按 CSV 的 id 顺序取词，不跳号、不重复。

## CSV 字段说明

| 字段 | 含义 |
|---|---|
| id | 发布顺序（严格按此顺序） |
| keyword | 目标长尾关键词（文章须紧扣它） |
| category | 主题分类（13 类轮转，保证内容多样性） |
| search_intent | informational / commercial-investigation |
| suggested_title | 建议标题（可微调，但必须含关键词核心） |
| slug | 目标文件路径（blog/xxx.html，已查重，勿改） |
| primary_link | 正文必须内链的主计算器/页面（含 CTA 按钮） |
| secondary_links | 正文须自然嵌入的其他站内链接（分号分隔） |
| status | pending → published（发布后更新） |
| publish_date / published_url | 发布后回填 |

## 单篇文章执行步骤

1. **取词**：找 id 最小且 `status=pending` 的行。
2. **写作**：
   - 复制现有博客文章（如 `blog/chicken-feed-guide.html`）的完整 HTML 骨架：header 导航（含 Printables）、footer、GA4、canonical、OG 标签、JSON-LD（Article + BreadcrumbList）。
   - `<title>` 与 `<h1>` 使用 suggested_title；meta description 120-155 字符且含关键词。
   - 正文 **1200-1800 词原创英文**，回答搜索意图：开头 2-3 句直接给答案（利于 featured snippet），随后 H2/H3 展开，至少 1 个数据表格，结尾 FAQ 3-5 问（可加 FAQPage JSON-LD）。
   - 数据须准确（饲料量、产量、温度、比例等引用 USDA/大学推广站常识数据）。
3. **内链（三个方向都要做）**：
   - **新 → 老**：正文自然嵌入 primary_link（另加一个显眼 CTA 按钮框指向该计算器）+ 全部 secondary_links。
   - **老 → 新**：挑 2-3 个相关老页面（primary_link 指向的计算器页的 Related/相关区块，或同类目旧博客文章正文/结尾）加上指向新文章的链接。
   - **索引页**：`blog/index.html` 列表最前面加新文章卡片（复用现有卡片结构）。
4. **sitemap.xml**：新增文章 URL（lastmod=当天，changefreq=monthly，priority=0.7）；被改动的老页面 lastmod 同步为当天。
5. **回填 CSV**：该行 status=published、publish_date=YYYY-MM-DD、published_url=完整 URL。
6. **验证**：文章内所有站内链接对应文件存在；HTML 标签平衡；无 "Coming Soon"/TODO/占位文本。
7. **发布**：`git add -A && git commit -m "content: <keyword> (kw #<id>)" && git push origin main`（仓库已配置 schannelCheckRevoke=false + sslBackend=schannel）。Cloudflare Pages 自动部署。

## 硬性规则

- 严格按 id 顺序，**绝不重复**已 published 的关键词/slug。
- 不修改 CSV 中未发布行的 slug（已做全站查重）。
- 文章间避免互相蚕食：每篇只主打自己那一个关键词，相近主题靠内链互指而非重复覆盖。
- `/seo/` 目录已在 robots.txt 屏蔽，勿在站内页面链接到它。
