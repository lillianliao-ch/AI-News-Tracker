import '@astrojs/internal-helpers/path';
import 'cookie';
import 'kleur/colors';
import { N as NOOP_MIDDLEWARE_FN } from './chunks/astro-designed-error-pages_i8mcvudy.mjs';
import 'es-module-lexer';
import { f as decodeKey } from './chunks/astro/server_B231dkDe.mjs';
import 'clsx';

function sanitizeParams(params) {
  return Object.fromEntries(
    Object.entries(params).map(([key, value]) => {
      if (typeof value === "string") {
        return [key, value.normalize().replace(/#/g, "%23").replace(/\?/g, "%3F")];
      }
      return [key, value];
    })
  );
}
function getParameter(part, params) {
  if (part.spread) {
    return params[part.content.slice(3)] || "";
  }
  if (part.dynamic) {
    if (!params[part.content]) {
      throw new TypeError(`Missing parameter: ${part.content}`);
    }
    return params[part.content];
  }
  return part.content.normalize().replace(/\?/g, "%3F").replace(/#/g, "%23").replace(/%5B/g, "[").replace(/%5D/g, "]");
}
function getSegment(segment, params) {
  const segmentPath = segment.map((part) => getParameter(part, params)).join("");
  return segmentPath ? "/" + segmentPath : "";
}
function getRouteGenerator(segments, addTrailingSlash) {
  return (params) => {
    const sanitizedParams = sanitizeParams(params);
    let trailing = "";
    if (addTrailingSlash === "always" && segments.length) {
      trailing = "/";
    }
    const path = segments.map((segment) => getSegment(segment, sanitizedParams)).join("") + trailing;
    return path || "/";
  };
}

function deserializeRouteData(rawRouteData) {
  return {
    route: rawRouteData.route,
    type: rawRouteData.type,
    pattern: new RegExp(rawRouteData.pattern),
    params: rawRouteData.params,
    component: rawRouteData.component,
    generate: getRouteGenerator(rawRouteData.segments, rawRouteData._meta.trailingSlash),
    pathname: rawRouteData.pathname || void 0,
    segments: rawRouteData.segments,
    prerender: rawRouteData.prerender,
    redirect: rawRouteData.redirect,
    redirectRoute: rawRouteData.redirectRoute ? deserializeRouteData(rawRouteData.redirectRoute) : void 0,
    fallbackRoutes: rawRouteData.fallbackRoutes.map((fallback) => {
      return deserializeRouteData(fallback);
    }),
    isIndex: rawRouteData.isIndex
  };
}

function deserializeManifest(serializedManifest) {
  const routes = [];
  for (const serializedRoute of serializedManifest.routes) {
    routes.push({
      ...serializedRoute,
      routeData: deserializeRouteData(serializedRoute.routeData)
    });
    const route = serializedRoute;
    route.routeData = deserializeRouteData(serializedRoute.routeData);
  }
  const assets = new Set(serializedManifest.assets);
  const componentMetadata = new Map(serializedManifest.componentMetadata);
  const inlinedScripts = new Map(serializedManifest.inlinedScripts);
  const clientDirectives = new Map(serializedManifest.clientDirectives);
  const serverIslandNameMap = new Map(serializedManifest.serverIslandNameMap);
  const key = decodeKey(serializedManifest.key);
  return {
    // in case user middleware exists, this no-op middleware will be reassigned (see plugin-ssr.ts)
    middleware() {
      return { onRequest: NOOP_MIDDLEWARE_FN };
    },
    ...serializedManifest,
    assets,
    componentMetadata,
    inlinedScripts,
    clientDirectives,
    routes,
    serverIslandNameMap,
    key
  };
}

const manifest = deserializeManifest({"hrefRoot":"file:///Users/lillianliao/notion_rag/ai_news_tracker/frontend/","adapterName":"@astrojs/node","routes":[{"file":"","links":[],"scripts":[],"styles":[],"routeData":{"type":"endpoint","isIndex":false,"route":"/_image","pattern":"^\\/_image$","segments":[[{"content":"_image","dynamic":false,"spread":false}]],"params":[],"component":"node_modules/astro/dist/assets/endpoint/node.js","pathname":"/_image","prerender":false,"fallbackRoutes":[],"_meta":{"trailingSlash":"ignore"}}},{"file":"","links":[],"scripts":[{"type":"inline","value":"async function r(n){const s=document.getElementById(`result-${n}`),t=document.getElementById(`result-content-${n}`),e=document.querySelector(`[data-news-id=\"${n}\"].generate-all-btn`);s&&(s.style.display=\"block\"),t&&(t.innerHTML='<p class=\"loading\">⏳ 正在生成 3 个版本的文案，请稍候...</p>'),e&&(e.disabled=!0,e.textContent=\"⏳ 生成中...\");try{const o=await fetch(\"http://localhost:8000/api/generate\",{method:\"POST\",headers:{\"Content-Type\":\"application/json\"},body:JSON.stringify({news_id:n,versions:[\"A\",\"B\",\"C\"]})});if(o.ok){const a=await o.json();if(a&&a.length>0){let l=\"\";a.forEach(c=>{const i={A:{name:\"硬核技术风\",class:\"tag-a\"},B:{name:\"轻松科普风\",class:\"tag-b\"},C:{name:\"热点观点风\",class:\"tag-c\"}}[c.version]||{name:\"未知\",class:\"\"};l+=`\n                  <div class=\"version-section\">\n                    <h3 class=\"version-title\">\n                      版本 ${c.version}\n                      <span class=\"version-tag ${i.class}\">${i.name}</span>\n                    </h3>\n                    <div class=\"generated-content\">${c.content}</div>\n                    <div class=\"generated-hashtags\">${c.hashtags?c.hashtags.join(\" \"):\"\"}</div>\n                  </div>\n                `}),t&&(t.innerHTML=l)}else t&&(t.innerHTML='<p class=\"loading\" style=\"color: #dc3545;\">❌ 生成失败：未返回内容</p>')}else{const a=await o.json();t&&(t.innerHTML=`<p class=\"loading\" style=\"color: #dc3545;\">❌ 生成失败：${a.detail||a.message||\"未知错误\"}</p>`)}}catch(o){console.error(\"生成错误:\",o),t&&(t.innerHTML=`<p class=\"loading\" style=\"color: #dc3545;\">❌ 生成失败：${o.message}</p>`)}finally{e&&(e.disabled=!1,e.textContent=\"🚀 一键生成全部版本\")}}function d(n){const s=document.getElementById(n);if(s){const t=s.innerText||s.textContent;navigator.clipboard.writeText(t).then(()=>{const e=document.querySelector(`[data-target=\"${n}\"].copy-all-btn`);if(e){const o=e.textContent;e.textContent=\"✅ 已复制\",e.classList.add(\"copied\"),setTimeout(()=>{e.textContent=o,e.classList.remove(\"copied\")},2e3)}}).catch(e=>{console.error(\"复制失败:\",e),alert(\"复制失败，请手动选择文本复制\")})}}document.addEventListener(\"DOMContentLoaded\",()=>{document.querySelectorAll(\".generate-all-btn\").forEach(t=>{t.addEventListener(\"click\",()=>{const e=t.dataset.newsId;r(e)})}),document.querySelectorAll(\".copy-all-btn\").forEach(t=>{t.addEventListener(\"click\",()=>{const e=t.dataset.target;d(e)})})});\n"}],"styles":[{"type":"external","src":"/_astro/generate.5taQMuu8.css"},{"type":"inline","content":"body{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;background:#f5f7fa;padding:20px;margin:0}.container{max-width:1200px;margin:0 auto}.page-header{text-align:center;margin-bottom:32px}h1{font-size:2rem;margin:0 0 8px;background:linear-gradient(135deg,#667eea,#764ba2);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}.subtitle{color:#666;margin:0}.tips{background:#fff;padding:20px;border-radius:12px;margin-bottom:32px;box-shadow:0 2px 4px #0000001a}.tips p{margin:0 0 12px;font-weight:600;color:#333}.tips ul{margin:0;padding-left:20px}.tips li{color:#666;margin-bottom:8px;line-height:1.6}.news-list{display:grid;gap:24px}.news-item{background:#fff;padding:24px;border-radius:12px;box-shadow:0 2px 8px #0000001a}.news-item h3{margin:0 0 12px;font-size:1.25rem;color:#1a1a1a}.summary{color:#666;margin-bottom:12px;line-height:1.6}.meta{display:flex;gap:16px;margin-bottom:16px;font-size:13px;color:#999}.actions{display:flex;gap:12px}.generate-all-btn{padding:12px 24px;background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;border:none;border-radius:8px;cursor:pointer;font-weight:600;font-size:15px;transition:all .2s}.generate-all-btn:hover{transform:translateY(-2px);box-shadow:0 4px 12px #667eea66}.generate-all-btn:disabled{background:#ccc;cursor:not-allowed;transform:none}.result-container{margin-top:20px;padding:20px;background:linear-gradient(135deg,#f8f9fa,#fff);border-radius:12px;border-left:4px solid #667eea}.result-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:16px}.result-header h4{margin:0;font-size:16px;font-weight:600;color:#667eea}.copy-all-btn{padding:6px 16px;background:#fff;border:2px solid #667eea;color:#667eea;border-radius:6px;cursor:pointer;font-weight:600;transition:all .2s}.copy-all-btn:hover{background:#667eea;color:#fff}.copy-all-btn.copied{background:#28a745;border-color:#28a745;color:#fff}.result-content{line-height:1.8}.result-content .loading{text-align:center;color:#999}.version-section{margin-bottom:24px;padding-bottom:20px;border-bottom:2px dashed #ddd}.version-section:last-child{border-bottom:none}.version-title{font-size:18px;font-weight:700;margin:0 0 12px;color:#333}.version-tag{display:inline-block;padding:4px 12px;border-radius:12px;font-size:12px;font-weight:600;margin-left:8px}.tag-a{background:#e3f2fd;color:#1976d2}.tag-b{background:#fce4ec;color:#c2185b}.tag-c{background:#e8f5e9;color:#388e3c}.generated-content{background:#fff;padding:16px;border-radius:8px;margin-top:12px;white-space:pre-wrap;color:#333;line-height:1.8}.generated-hashtags{color:#667eea;font-weight:500;margin-top:12px}\n"}],"routeData":{"route":"/generate","isIndex":false,"type":"page","pattern":"^\\/generate\\/?$","segments":[[{"content":"generate","dynamic":false,"spread":false}]],"params":[],"component":"src/pages/generate.astro","pathname":"/generate","prerender":false,"fallbackRoutes":[],"_meta":{"trailingSlash":"ignore"}}},{"file":"","links":[],"scripts":[],"styles":[{"type":"external","src":"/_astro/generate.5taQMuu8.css"},{"type":"inline","content":"body{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;background:#f5f7fa;padding:20px}.container{max-width:1200px;margin:0 auto}h1{font-size:2rem;margin-bottom:8px}.subtitle{color:#666;margin-bottom:32px}.placeholder{background:#fff;padding:60px 20px;border-radius:12px;text-align:center;box-shadow:0 2px 4px #0000001a}.placeholder p{color:#666;margin:8px 0}\n"}],"routeData":{"route":"/published","isIndex":false,"type":"page","pattern":"^\\/published\\/?$","segments":[[{"content":"published","dynamic":false,"spread":false}]],"params":[],"component":"src/pages/published.astro","pathname":"/published","prerender":false,"fallbackRoutes":[],"_meta":{"trailingSlash":"ignore"}}},{"file":"","links":[],"scripts":[{"type":"external","value":"/_astro/hoisted.BfliA9fX.js"}],"styles":[{"type":"external","src":"/_astro/generate.5taQMuu8.css"},{"type":"external","src":"/_astro/index.BAFXFnpb.css"}],"routeData":{"route":"/","isIndex":true,"type":"page","pattern":"^\\/$","segments":[],"params":[],"component":"src/pages/index.astro","pathname":"/","prerender":false,"fallbackRoutes":[],"_meta":{"trailingSlash":"ignore"}}}],"base":"/","trailingSlash":"ignore","compressHTML":true,"componentMetadata":[["/Users/lillianliao/notion_rag/ai_news_tracker/frontend/src/pages/generate.astro",{"propagation":"none","containsHead":true}],["/Users/lillianliao/notion_rag/ai_news_tracker/frontend/src/pages/published.astro",{"propagation":"none","containsHead":true}],["/Users/lillianliao/notion_rag/ai_news_tracker/frontend/src/pages/index.astro",{"propagation":"none","containsHead":true}]],"renderers":[],"clientDirectives":[["idle","(()=>{var l=(o,t)=>{let i=async()=>{await(await o())()},e=typeof t.value==\"object\"?t.value:void 0,s={timeout:e==null?void 0:e.timeout};\"requestIdleCallback\"in window?window.requestIdleCallback(i,s):setTimeout(i,s.timeout||200)};(self.Astro||(self.Astro={})).idle=l;window.dispatchEvent(new Event(\"astro:idle\"));})();"],["load","(()=>{var e=async t=>{await(await t())()};(self.Astro||(self.Astro={})).load=e;window.dispatchEvent(new Event(\"astro:load\"));})();"],["media","(()=>{var s=(i,t)=>{let a=async()=>{await(await i())()};if(t.value){let e=matchMedia(t.value);e.matches?a():e.addEventListener(\"change\",a,{once:!0})}};(self.Astro||(self.Astro={})).media=s;window.dispatchEvent(new Event(\"astro:media\"));})();"],["only","(()=>{var e=async t=>{await(await t())()};(self.Astro||(self.Astro={})).only=e;window.dispatchEvent(new Event(\"astro:only\"));})();"],["visible","(()=>{var l=(s,i,o)=>{let r=async()=>{await(await s())()},t=typeof i.value==\"object\"?i.value:void 0,c={rootMargin:t==null?void 0:t.rootMargin},n=new IntersectionObserver(e=>{for(let a of e)if(a.isIntersecting){n.disconnect(),r();break}},c);for(let e of o.children)n.observe(e)};(self.Astro||(self.Astro={})).visible=l;window.dispatchEvent(new Event(\"astro:visible\"));})();"]],"entryModules":{"\u0000noop-middleware":"_noop-middleware.mjs","\u0000@astro-page:node_modules/astro/dist/assets/endpoint/node@_@js":"pages/_image.astro.mjs","\u0000@astro-page:src/pages/generate@_@astro":"pages/generate.astro.mjs","\u0000@astro-page:src/pages/published@_@astro":"pages/published.astro.mjs","\u0000@astro-page:src/pages/index@_@astro":"pages/index.astro.mjs","\u0000@astrojs-ssr-virtual-entry":"entry.mjs","\u0000@astro-renderers":"renderers.mjs","\u0000@astrojs-ssr-adapter":"_@astrojs-ssr-adapter.mjs","/Users/lillianliao/notion_rag/ai_news_tracker/frontend/node_modules/astro/dist/env/setup.js":"chunks/astro/env-setup_Cr6XTFvb.mjs","\u0000@astrojs-manifest":"manifest_Bba304c2.mjs","@astrojs/react/client.js":"_astro/client.uNJO8lcC.js","/astro/hoisted.js?q=0":"_astro/hoisted.CqH34z7-.js","/astro/hoisted.js?q=1":"_astro/hoisted.BfliA9fX.js","astro:scripts/before-hydration.js":""},"inlinedScripts":[],"assets":["/_astro/generate.5taQMuu8.css","/_astro/index.BAFXFnpb.css","/_astro/client.uNJO8lcC.js","/_astro/hoisted.BfliA9fX.js"],"buildFormat":"directory","checkOrigin":false,"serverIslandNameMap":[],"key":"UqounRwFz842a2PS8qFUl+TuD9Tm6BKwH6S43vWc2VM=","experimentalEnvGetSecretEnabled":false});

export { manifest };
