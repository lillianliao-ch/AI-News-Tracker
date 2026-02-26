/* empty css                                    */
import { c as createComponent, d as renderHead, e as renderComponent, b as addAttribute, r as renderTemplate } from '../chunks/astro/server_B231dkDe.mjs';
import 'kleur/colors';
import { $ as $$Header } from '../chunks/Header_CEVC7i23.mjs';
/* empty css                                    */
export { renderers } from '../renderers.mjs';

const $$Generate = createComponent(async ($$result, $$props, $$slots) => {
  let allNews = [];
  try {
    const response = await fetch("http://localhost:8000/api/news?limit=20");
    allNews = await response.json();
  } catch (error) {
    console.error("\u83B7\u53D6\u8D44\u8BAF\u5931\u8D25:", error);
  }
  return renderTemplate`<html lang="zh-CN"> <head><meta charset="UTF-8"><meta name="viewport" content="width=device-width"><title>内容生成 - AI News Tracker</title>${renderHead()}</head> <body> <div class="container"> ${renderComponent($$result, "Header", $$Header, {})} <div class="page-header"> <h1>✍️ 小红书文案生成</h1> <p class="subtitle">选择资讯，AI 自动生成 3 种风格的小红书文案，一键复制使用</p> </div> <div class="tips"> <p>💡 <strong>使用提示：</strong></p> <ul> <li><strong>版本 A - 硬核技术风：</strong>适合技术人员，用数据说话，专业但不晦涩</li> <li><strong>版本 B - 轻松科普风：</strong>适合大众用户，口语化表达，多用表情符号</li> <li><strong>版本 C - 热点观点风：</strong>适合行业观察者，有观点有立场，引发讨论</li> </ul> </div> <div class="news-list"> ${allNews.map((news) => renderTemplate`<div class="news-item"${addAttribute(news.news_id, "data-news-id")}> <h3>${news.title}</h3> <p class="summary">${news.summary?.substring(0, 120)}...</p> <p class="meta"> <span class="source">${news.source}</span> <span class="time"> ${news.publish_time ? new Date(news.publish_time).toLocaleString("zh-CN") : ""} </span> </p> <div class="actions"> <button class="generate-all-btn"${addAttribute(news.news_id, "data-news-id")}>
🚀 一键生成全部版本
</button> </div> <div class="result-container"${addAttribute(`result-${news.news_id}`, "id")} style="display: none;"> <div class="result-header"> <h4>✨ 生成结果</h4> <button class="copy-all-btn"${addAttribute(`result-content-${news.news_id}`, "data-target")}>
📋 复制全部
</button> </div> <div class="result-content"${addAttribute(`result-content-${news.news_id}`, "id")}> <p class="loading">⏳ 正在生成中...</p> </div> </div> </div>`)} </div> </div>   </body> </html>`;
}, "/Users/lillianliao/notion_rag/ai_news_tracker/frontend/src/pages/generate.astro", void 0);

const $$file = "/Users/lillianliao/notion_rag/ai_news_tracker/frontend/src/pages/generate.astro";
const $$url = "/generate";

const _page = /*#__PURE__*/Object.freeze(/*#__PURE__*/Object.defineProperty({
  __proto__: null,
  default: $$Generate,
  file: $$file,
  url: $$url
}, Symbol.toStringTag, { value: 'Module' }));

const page = () => _page;

export { page };
