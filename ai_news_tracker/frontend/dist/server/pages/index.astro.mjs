/* empty css                                    */
import { c as createComponent, m as maybeRenderHead, r as renderTemplate, a as createAstro, b as addAttribute, e as renderComponent, d as renderHead } from '../chunks/astro/server_B231dkDe.mjs';
import 'kleur/colors';
import { $ as $$Header } from '../chunks/Header_CEVC7i23.mjs';
import 'clsx';
/* empty css                                 */
export { renderers } from '../renderers.mjs';

const $$Sidebar = createComponent(($$result, $$props, $$slots) => {
  return renderTemplate`${maybeRenderHead()}<aside class="sidebar" data-astro-cid-ssfzsv2f> <nav class="nav" data-astro-cid-ssfzsv2f> <a href="/" class="nav-item active" data-astro-cid-ssfzsv2f> <span class="icon" data-astro-cid-ssfzsv2f>📰</span> <span data-astro-cid-ssfzsv2f>资讯列表</span> </a> <a href="/generate" class="nav-item" data-astro-cid-ssfzsv2f> <span class="icon" data-astro-cid-ssfzsv2f>✍️</span> <span data-astro-cid-ssfzsv2f>内容生成</span> </a> <a href="/published" class="nav-item" data-astro-cid-ssfzsv2f> <span class="icon" data-astro-cid-ssfzsv2f>📊</span> <span data-astro-cid-ssfzsv2f>已发布</span> </a> </nav> <div class="stats" data-astro-cid-ssfzsv2f> <h3 data-astro-cid-ssfzsv2f>📊 统计信息</h3> <div class="stat-item" data-astro-cid-ssfzsv2f> <span class="stat-label" data-astro-cid-ssfzsv2f>总资讯</span> <span class="stat-value" id="totalNews" data-astro-cid-ssfzsv2f>-</span> </div> <div class="stat-item" data-astro-cid-ssfzsv2f> <span class="stat-label" data-astro-cid-ssfzsv2f>今日新增</span> <span class="stat-value" id="todayNews" data-astro-cid-ssfzsv2f>-</span> </div> </div> <div class="about" data-astro-cid-ssfzsv2f> <h3 data-astro-cid-ssfzsv2f>ℹ️ 关于</h3> <p data-astro-cid-ssfzsv2f>AI News Tracker 是一个基于 MediaCrawler 和 newsnow 设计理念的 AI 资讯追踪平台。</p> <ul data-astro-cid-ssfzsv2f> <li data-astro-cid-ssfzsv2f>✅ 多源资讯聚合</li> <li data-astro-cid-ssfzsv2f>✅ AI 智能分类</li> <li data-astro-cid-ssfzsv2f>✅ 小红书内容生成</li> <li data-astro-cid-ssfzsv2f>✅ 用户偏好学习</li> </ul> </div> </aside>  `;
}, "/Users/lillianliao/notion_rag/ai_news_tracker/frontend/src/components/Sidebar.astro", void 0);

var __freeze$1 = Object.freeze;
var __defProp$1 = Object.defineProperty;
var __template$1 = (cooked, raw) => __freeze$1(__defProp$1(cooked, "raw", { value: __freeze$1(cooked.slice()) }));
var _a$1;
const $$Astro$1 = createAstro();
const $$NewsCard = createComponent(($$result, $$props, $$slots) => {
  const Astro2 = $$result.createAstro($$Astro$1, $$props, $$slots);
  Astro2.self = $$NewsCard;
  const { news } = Astro2.props;
  const publishTime = news.publish_time ? new Date(news.publish_time).toLocaleString("zh-CN", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit"
  }) : "-";
  function getCategoryName(category) {
    const names = {
      "product": "\u4EA7\u54C1",
      "model": "\u6A21\u578B",
      "investment": "\u878D\u8D44",
      "view": "\u89C2\u70B9",
      "research": "\u7814\u7A76",
      "application": "\u5E94\u7528"
    };
    return names[category] || "\u8D44\u8BAF";
  }
  function getImportanceStars(importance) {
    const level = importance || 3;
    return "\u2B50".repeat(level);
  }
  function getImportanceLabel(importance) {
    const level = importance || 3;
    const labels = {
      1: "\u4E00\u822C",
      2: "\u5173\u6CE8",
      3: "\u91CD\u8981",
      4: "\u91CD\u8981",
      5: "\u5FC5\u8BFB"
    };
    return labels[level] || "\u91CD\u8981";
  }
  return renderTemplate(_a$1 || (_a$1 = __template$1(["", '<article class="news-card"', ' data-astro-cid-ibl2wg7k> <!-- \u5361\u7247\u5934\u90E8 --> <div class="card-header" data-astro-cid-ibl2wg7k> <div class="source-info" data-astro-cid-ibl2wg7k> <span class="source-name" data-astro-cid-ibl2wg7k>', '</span> <span class="publish-time" data-astro-cid-ibl2wg7k>', "</span> </div> <span", " data-astro-cid-ibl2wg7k> ", ' </span> </div> <!-- \u6807\u9898 --> <h2 class="news-title" data-astro-cid-ibl2wg7k> <a', ' target="_blank" rel="noopener noreferrer" data-astro-cid-ibl2wg7k> ', ' </a> </h2> <!-- \u6458\u8981 --> <p class="news-summary" data-astro-cid-ibl2wg7k> ', ' </p> <!-- \u5361\u7247\u5E95\u90E8 --> <div class="card-footer" data-astro-cid-ibl2wg7k> <div class="meta" data-astro-cid-ibl2wg7k> <!-- \u2728 \u663E\u793A\u91CD\u8981\u6027\u8BC4\u5206 --> ', ' </div> <button class="generate-btn"', ' data-astro-cid-ibl2wg7k>\n\u270D\uFE0F \u751F\u6210\u6587\u6848\n</button> </div> <!-- \u751F\u6210\u7ED3\u679C\u533A\u57DF\uFF08\u9ED8\u8BA4\u9690\u85CF\uFF09 --> <div class="generated-result"', ' style="display: none;" data-astro-cid-ibl2wg7k> <div class="result-header" data-astro-cid-ibl2wg7k> <h4 data-astro-cid-ibl2wg7k>\u2728 \u751F\u6210\u7684\u5C0F\u7EA2\u4E66\u6587\u6848</h4> <button class="copy-btn"', ' data-astro-cid-ibl2wg7k>\n\u{1F4CB} \u590D\u5236\n</button> </div> <div class="result-content"', ' data-astro-cid-ibl2wg7k></div> </div> <!-- \u9690\u85CF\u7684\u6570\u636E\uFF08\u7528\u4E8E JS \u8BFB\u53D6\uFF09 --> <script type="application/json" data-news-data>\n    {JSON.stringify(news)}\n  <\/script> </article>  '])), maybeRenderHead(), addAttribute(news.news_id, "data-news-id"), news.source, publishTime, addAttribute(`category category-${news.ai_category || news.category || "view"}`, "class"), getCategoryName(news.ai_category || news.category), addAttribute(news.url || "#", "href"), news.title, news.summary || "\u6682\u65E0\u6458\u8981", news.ai_importance && renderTemplate`<span${addAttribute(`importance-badge importance-${news.ai_importance}`, "class")}${addAttribute(`\u91CD\u8981\u6027\uFF1A${getImportanceLabel(news.ai_importance)}`, "title")} data-astro-cid-ibl2wg7k> ${getImportanceStars(news.ai_importance)} </span>`, addAttribute(news.news_id, "data-news-id"), addAttribute(`result-${news.news_id}`, "id"), addAttribute(`result-content-${news.news_id}`, "data-target"), addAttribute(`result-content-${news.news_id}`, "id"));
}, "/Users/lillianliao/notion_rag/ai_news_tracker/frontend/src/components/NewsCard.astro", void 0);

const $$Astro = createAstro();
const $$NewsGrid = createComponent(($$result, $$props, $$slots) => {
  const Astro2 = $$result.createAstro($$Astro, $$props, $$slots);
  Astro2.self = $$NewsGrid;
  const { news } = Astro2.props;
  return renderTemplate`${maybeRenderHead()}<div class="news-grid" id="newsGrid" data-astro-cid-dtuulsrz> ${news.map((item) => renderTemplate`${renderComponent($$result, "NewsCard", $$NewsCard, { "news": item, "data-astro-cid-dtuulsrz": true })}`)} </div>  `;
}, "/Users/lillianliao/notion_rag/ai_news_tracker/frontend/src/components/NewsGrid.astro", void 0);

const $$RefreshButton = createComponent(async ($$result, $$props, $$slots) => {
  return renderTemplate`${maybeRenderHead()}<div class="refresh-container" data-astro-cid-odqmvp65> <button class="refresh-btn" id="refreshBtn" data-astro-cid-odqmvp65> <span class="icon" data-astro-cid-odqmvp65>🔄</span> <span class="text" data-astro-cid-odqmvp65>刷新资讯</span> </button> <span class="last-update" id="lastUpdate" data-astro-cid-odqmvp65>最后更新: -</span> </div>  `;
}, "/Users/lillianliao/notion_rag/ai_news_tracker/frontend/src/components/RefreshButton.astro", void 0);

var __freeze = Object.freeze;
var __defProp = Object.defineProperty;
var __template = (cooked, raw) => __freeze(__defProp(cooked, "raw", { value: __freeze(raw || cooked.slice()) }));
var _a;
const $$Index = createComponent(async ($$result, $$props, $$slots) => {
  let allNews = [];
  try {
    const response = await fetch("http://localhost:8000/api/news?limit=50");
    allNews = await response.json();
  } catch (error) {
    console.error("\u83B7\u53D6\u8D44\u8BAF\u5931\u8D25:", error);
  }
  const categories = ["\u5168\u90E8", "\u4EA7\u54C1", "\u6A21\u578B", "\u878D\u8D44", "\u89C2\u70B9"];
  return renderTemplate(_a || (_a = __template(['<html lang="zh-CN"> <head><meta charset="UTF-8"><meta name="viewport" content="width=device-width"><meta name="description" content="AI News Tracker - \u4F18\u96C5\u7684AI\u8D44\u8BAF\u9605\u8BFB\u5E73\u53F0"><title>AI News Tracker - AI\u8D44\u8BAF\u8FFD\u8E2A\u4E0E\u5185\u5BB9\u751F\u6210</title><link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>', '</head> <body> <div class="container"> <!-- \u4FA7\u8FB9\u680F --> ', ' <!-- \u4E3B\u5185\u5BB9\u533A --> <main class="main-content"> <!-- \u5934\u90E8 --> ', ' <!-- \u64CD\u4F5C\u680F --> <div class="action-bar"> <div class="categories"> ', " </div> ", " </div> <!-- \u8D44\u8BAF\u7F51\u683C --> ", " <!-- \u52A0\u8F7D\u66F4\u591A --> <div class=\"load-more\"> <button id=\"loadMoreBtn\">\u52A0\u8F7D\u66F4\u591A</button> </div> </main> </div> <script>\n      // \u2728 AI\u5206\u7C7B\u6620\u5C04\uFF08\u5C06\u524D\u7AEF\u6807\u7B7E\u6620\u5C04\u5230AI\u5206\u7C7B\uFF09\n      const AI_CATEGORY_MAP = {\n        '\u5168\u90E8': null,\n        '\u4EA7\u54C1': 'product',\n        '\u6A21\u578B': 'model',\n        '\u878D\u8D44': 'investment',\n        '\u89C2\u70B9': 'view'\n      };\n\n      // \u52A0\u8F7D\u7EDF\u8BA1\u4FE1\u606F\u5E76\u66F4\u65B0\u5206\u7C7B\u6309\u94AE\n      async function loadStatsAndUpdateCategories() {\n        try {\n          const response = await fetch('http://localhost:8000/api/stats');\n          const stats = await response.json();\n\n          // \u2728 \u4F7F\u7528AI\u5206\u7C7B\u7EDF\u8BA1\n          document.querySelectorAll('.category-btn').forEach(btn => {\n            const category = btn.dataset.category;\n            const aiCategory = AI_CATEGORY_MAP[category];\n\n            let count;\n            if (category === '\u5168\u90E8') {\n              count = stats.total_news || 0;\n            } else {\n              count = stats.ai_category_stats?.[aiCategory] || 0;\n            }\n            btn.textContent = `${category} (${count})`;\n          });\n        } catch (error) {\n          console.error('\u52A0\u8F7D\u7EDF\u8BA1\u5931\u8D25:', error);\n        }\n      }\n\n      // \u9875\u9762\u52A0\u8F7D\u65F6\u83B7\u53D6\u7EDF\u8BA1\n      loadStatsAndUpdateCategories();\n\n      // \u5206\u7C7B\u7B5B\u9009\n      document.querySelectorAll('.category-btn').forEach(btn => {\n        btn.addEventListener('click', async (e) => {\n          const category = e.target.dataset.category;\n\n          // \u66F4\u65B0\u6D3B\u52A8\u72B6\u6001\n          document.querySelectorAll('.category-btn').forEach(b => b.classList.remove('active'));\n          e.target.classList.add('active');\n\n          // \u2728 \u4F7F\u7528AI\u5206\u7C7B\u7B5B\u9009\n          const aiCategory = AI_CATEGORY_MAP[category];\n          const url = aiCategory\n            ? `http://localhost:8000/api/news?ai_category=${aiCategory}&limit=50`\n            : 'http://localhost:8000/api/news?limit=50';\n\n          const response = await fetch(url);\n          const news = await response.json();\n\n          // \u66F4\u65B0\u663E\u793A\uFF08\u89E6\u53D1\u81EA\u5B9A\u4E49\u4E8B\u4EF6\uFF09\n          window.dispatchEvent(new CustomEvent('news-updated', { detail: news }));\n        });\n      });\n\n      // \u52A0\u8F7D\u66F4\u591A\n      document.getElementById('loadMoreBtn')?.addEventListener('click', async () => {\n        const currentCount = document.querySelectorAll('.news-card').length;\n        const response = await fetch(`http://localhost:8000/api/news?offset=${currentCount}&limit=20`);\n        const news = await response.json();\n\n        // \u89E6\u53D1\u66F4\u65B0\u4E8B\u4EF6\n        window.dispatchEvent(new CustomEvent('news-appended', { detail: news }));\n      });\n    <\/script> </body> </html> "], ['<html lang="zh-CN"> <head><meta charset="UTF-8"><meta name="viewport" content="width=device-width"><meta name="description" content="AI News Tracker - \u4F18\u96C5\u7684AI\u8D44\u8BAF\u9605\u8BFB\u5E73\u53F0"><title>AI News Tracker - AI\u8D44\u8BAF\u8FFD\u8E2A\u4E0E\u5185\u5BB9\u751F\u6210</title><link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>', '</head> <body> <div class="container"> <!-- \u4FA7\u8FB9\u680F --> ', ' <!-- \u4E3B\u5185\u5BB9\u533A --> <main class="main-content"> <!-- \u5934\u90E8 --> ', ' <!-- \u64CD\u4F5C\u680F --> <div class="action-bar"> <div class="categories"> ', " </div> ", " </div> <!-- \u8D44\u8BAF\u7F51\u683C --> ", " <!-- \u52A0\u8F7D\u66F4\u591A --> <div class=\"load-more\"> <button id=\"loadMoreBtn\">\u52A0\u8F7D\u66F4\u591A</button> </div> </main> </div> <script>\n      // \u2728 AI\u5206\u7C7B\u6620\u5C04\uFF08\u5C06\u524D\u7AEF\u6807\u7B7E\u6620\u5C04\u5230AI\u5206\u7C7B\uFF09\n      const AI_CATEGORY_MAP = {\n        '\u5168\u90E8': null,\n        '\u4EA7\u54C1': 'product',\n        '\u6A21\u578B': 'model',\n        '\u878D\u8D44': 'investment',\n        '\u89C2\u70B9': 'view'\n      };\n\n      // \u52A0\u8F7D\u7EDF\u8BA1\u4FE1\u606F\u5E76\u66F4\u65B0\u5206\u7C7B\u6309\u94AE\n      async function loadStatsAndUpdateCategories() {\n        try {\n          const response = await fetch('http://localhost:8000/api/stats');\n          const stats = await response.json();\n\n          // \u2728 \u4F7F\u7528AI\u5206\u7C7B\u7EDF\u8BA1\n          document.querySelectorAll('.category-btn').forEach(btn => {\n            const category = btn.dataset.category;\n            const aiCategory = AI_CATEGORY_MAP[category];\n\n            let count;\n            if (category === '\u5168\u90E8') {\n              count = stats.total_news || 0;\n            } else {\n              count = stats.ai_category_stats?.[aiCategory] || 0;\n            }\n            btn.textContent = \\`\\${category} (\\${count})\\`;\n          });\n        } catch (error) {\n          console.error('\u52A0\u8F7D\u7EDF\u8BA1\u5931\u8D25:', error);\n        }\n      }\n\n      // \u9875\u9762\u52A0\u8F7D\u65F6\u83B7\u53D6\u7EDF\u8BA1\n      loadStatsAndUpdateCategories();\n\n      // \u5206\u7C7B\u7B5B\u9009\n      document.querySelectorAll('.category-btn').forEach(btn => {\n        btn.addEventListener('click', async (e) => {\n          const category = e.target.dataset.category;\n\n          // \u66F4\u65B0\u6D3B\u52A8\u72B6\u6001\n          document.querySelectorAll('.category-btn').forEach(b => b.classList.remove('active'));\n          e.target.classList.add('active');\n\n          // \u2728 \u4F7F\u7528AI\u5206\u7C7B\u7B5B\u9009\n          const aiCategory = AI_CATEGORY_MAP[category];\n          const url = aiCategory\n            ? \\`http://localhost:8000/api/news?ai_category=\\${aiCategory}&limit=50\\`\n            : 'http://localhost:8000/api/news?limit=50';\n\n          const response = await fetch(url);\n          const news = await response.json();\n\n          // \u66F4\u65B0\u663E\u793A\uFF08\u89E6\u53D1\u81EA\u5B9A\u4E49\u4E8B\u4EF6\uFF09\n          window.dispatchEvent(new CustomEvent('news-updated', { detail: news }));\n        });\n      });\n\n      // \u52A0\u8F7D\u66F4\u591A\n      document.getElementById('loadMoreBtn')?.addEventListener('click', async () => {\n        const currentCount = document.querySelectorAll('.news-card').length;\n        const response = await fetch(\\`http://localhost:8000/api/news?offset=\\${currentCount}&limit=20\\`);\n        const news = await response.json();\n\n        // \u89E6\u53D1\u66F4\u65B0\u4E8B\u4EF6\n        window.dispatchEvent(new CustomEvent('news-appended', { detail: news }));\n      });\n    <\/script> </body> </html> "])), renderHead(), renderComponent($$result, "Sidebar", $$Sidebar, {}), renderComponent($$result, "Header", $$Header, {}), categories.map((cat, index) => renderTemplate`<button${addAttribute(`category-btn ${index === 0 ? "active" : ""}`, "class")}${addAttribute(cat, "data-category")}> ${cat} </button>`), renderComponent($$result, "RefreshButton", $$RefreshButton, {}), renderComponent($$result, "NewsGrid", $$NewsGrid, { "news": allNews }));
}, "/Users/lillianliao/notion_rag/ai_news_tracker/frontend/src/pages/index.astro", void 0);

const $$file = "/Users/lillianliao/notion_rag/ai_news_tracker/frontend/src/pages/index.astro";
const $$url = "";

const _page = /*#__PURE__*/Object.freeze(/*#__PURE__*/Object.defineProperty({
  __proto__: null,
  default: $$Index,
  file: $$file,
  url: $$url
}, Symbol.toStringTag, { value: 'Module' }));

const page = () => _page;

export { page };
