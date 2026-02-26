/* empty css                                    */
import { c as createComponent, d as renderHead, e as renderComponent, r as renderTemplate } from '../chunks/astro/server_B231dkDe.mjs';
import 'kleur/colors';
import { $ as $$Header } from '../chunks/Header_CEVC7i23.mjs';
/* empty css                                     */
export { renderers } from '../renderers.mjs';

const $$Published = createComponent(($$result, $$props, $$slots) => {
  return renderTemplate`<html lang="zh-CN"> <head><meta charset="UTF-8"><meta name="viewport" content="width=device-width"><title>已发布 - AI News Tracker</title>${renderHead()}</head> <body> <div class="container"> ${renderComponent($$result, "Header", $$Header, {})} <h1>📊 已发布内容</h1> <p class="subtitle">查看已经发布到小红书的内容</p> <div class="placeholder"> <p>🚧 功能开发中...</p> <p>这个页面将显示已生成并发布到小红书的内容列表。</p> </div> </div>  </body> </html>`;
}, "/Users/lillianliao/notion_rag/ai_news_tracker/frontend/src/pages/published.astro", void 0);

const $$file = "/Users/lillianliao/notion_rag/ai_news_tracker/frontend/src/pages/published.astro";
const $$url = "/published";

const _page = /*#__PURE__*/Object.freeze(/*#__PURE__*/Object.defineProperty({
  __proto__: null,
  default: $$Published,
  file: $$file,
  url: $$url
}, Symbol.toStringTag, { value: 'Module' }));

const page = () => _page;

export { page };
