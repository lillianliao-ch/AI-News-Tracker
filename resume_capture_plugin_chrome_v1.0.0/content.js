function cleanText(v) {
  return String(v || "").replace(/\s+/g, " ").trim();
}

function agentDebugLogContent(runId, hypothesisId, location, message, data) {
  // #region agent log
  fetch("http://127.0.0.1:7242/ingest/db2b23fc-ef66-489d-ade3-6dd5a6d07883", {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Debug-Session-Id": "18882a" },
    body: JSON.stringify({
      sessionId: "18882a",
      runId: String(runId || ""),
      hypothesisId: String(hypothesisId || ""),
      location: String(location || ""),
      message: String(message || ""),
      data: data && typeof data === "object" ? data : {},
      timestamp: Date.now()
    })
  }).catch(() => {});
  // #endregion
}

function splitLines(text) {
  return String(text || "")
    .split(/\n+/)
    .map((s) => cleanText(s))
    .filter(Boolean);
}

function normalizeResumeText(text) {
  const normalized = String(text || "")
    .replace(/\r\n/g, "\n")
    .replace(/\r/g, "\n")
    .replace(/\u00a0/g, " ")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
  return normalized.length > 200000 ? normalized.slice(0, 200000) : normalized;
}

function firstMatchText(selectors, root) {
  const scope = root && typeof root.querySelector === "function" ? root : document;
  for (const s of selectors) {
    const el = scope.querySelector(s);
    const t = cleanText(el ? el.textContent : "");
    if (t) return t;
  }
  return "";
}

function detectSourceSite() {
  const h = location.hostname.toLowerCase();
  if (h.includes("zhipin")) return "Boss直聘";
  if (h.includes("liepin")) return "猎聘";
  if (h.includes("51job")) return "前程无忧";
  return h;
}

function isBossSite() {
  return location.hostname.toLowerCase().includes("zhipin");
}

function isBossResumeFrame() {
  return isBossSite() && /\/web\/frame\/(?:c-resume|recommend(?:-v\d+)?)\/?/i.test(String(location.pathname || ""));
}

function shouldRunBossAutomationTickHere() {
  if (!isBossSite()) return false;
  const path = String(location.pathname || "").toLowerCase();
  if (/\/web\/common\/security\/scan\.html/.test(path)) return false;
  if (window.top !== window) {
    return isBossResumeFrame() || /\/web\/frame\/recommend/.test(path);
  }
  if (/\/web\/chat\/recommend/.test(path)) return false;
  return /\/recommend|\/chat|\/message|\/geek\/chat|\/job\/detail/.test(path);
}

function stripBossUiPrefix(text) {
  return cleanText(text).replace(/^(已读|未读|在线|离线|刚刚活跃|活跃|忙碌)/, "").trim();
}

function isBossNoiseName(name) {
  const text = cleanText(name);
  if (!text) return true;
  return /^(试试|牛人|示例|诊断|沟通|招呼|简历|详情|经历|经历概览|工作经历|教育经历|最近关注|工作概览|简历详情|限时免费体验|牛人诊断工具|查看示例|立即沟通|打招呼|收藏|已收藏|感兴趣|不感兴趣|屏蔽|不合适|举报|转发|转发牛人|职优|吾思职优|吾思职优沟通|已读|未读|人才库|基本信息|个人|个人信息|个人资料|个人介绍|姓名)$/u.test(text) || /免费体验|诊断工具|职优|沟通|打招呼|工作概览|简历详情|最近关注|同事沟通|基本信息|个人资料|个人介绍/u.test(text);
}

function isStrictCandidateName(name) {
  const text = cleanText(name);
  if (!text) return false;
  if (/^[\u4e00-\u9fa5]{1,8}(先生|女士)$/.test(text)) return true;
  if (/^[\u4e00-\u9fa5]{2,4}$/.test(text) && !isBossNoiseName(text)) return true;
  return false;
}

function extractSchoolName(text) {
  const t = cleanText(text);
  if (!t) return "";
  const m = t.match(/([\u4e00-\u9fa5A-Za-z0-9（）()·\-.]{2,64}(?:大学|学院|学校|研究院|研究所|中学|职高|技校|职业技术学院|专科学校))/u);
  return m ? cleanText(m[1]) : "";
}

function extractEducationKeyword(text) {
  const m = cleanText(text).match(/(博士后|博士|硕士|本科|大专|中专|高中|初中)/);
  return m ? m[1] : "";
}

function normalizeWorkYearsText(text) {
  const t = cleanText(text);
  const m = t.match(/(\d+\s*\+?\s*年)(?:经验)?/);
  return m ? cleanText(m[1]) : "";
}

function parsePhone(text) {
  const t = cleanText(text);
  const m = t.match(/(?:\+?86[-\s]?)?(1[3-9]\d{9})/);
  return m ? m[1] : "";
}

function parseEmail(text) {
  const t = cleanText(text);
  const m = t.match(/[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}/);
  return m ? m[0] : "";
}

function simpleHash(input) {
  let h = 2166136261;
  const s = String(input || "");
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h += (h << 1) + (h << 4) + (h << 7) + (h << 8) + (h << 24);
  }
  return (h >>> 0).toString(16);
}

function isValidSourceCandidateId(id) {
  const text = cleanText(id);
  if (!text) return false;
  if (text.length > 200) return false;
  if (!/^[A-Za-z0-9_-]+$/.test(text)) return false;
  if (/(immersive|translate|injected|stylesheet|extension|plugin|css)/i.test(text)) return false;
  return true;
}

function normalizeSourceCandidateId(id) {
  const text = cleanText(id);
  return isValidSourceCandidateId(text) ? text : "";
}

function isVisibleCaptureElement(el) {
  if (!el || typeof el.getBoundingClientRect !== "function") return false;
  const rect = el.getBoundingClientRect();
  if (rect.width < 260 || rect.height < 220) return false;
  const style = window.getComputedStyle(el);
  if (!style) return true;
  if (style.display === "none" || style.visibility === "hidden" || style.opacity === "0") return false;
  return true;
}

function pickBossPopupRoot() {
  if (isBossResumeFrame()) {
    return document.body || document.documentElement;
  }
  const selector = [
    "[role='dialog']",
    "[class*='dialog']",
    "[class*='Dialog']",
    "[class*='modal']",
    "[class*='Modal']",
    "[class*='popup']",
    "[class*='Popup']",
    "[class*='resume']",
    "[class*='Resume']"
  ].join(",");
  const all = document.querySelectorAll(selector);
  const maxScan = Math.min(all.length, 1200);
  const candidates = [];
  for (let i = 0; i < maxScan; i++) {
    const el = all[i];
    if (!isVisibleCaptureElement(el)) continue;
    const txt = cleanText(el.innerText || "");
    if (!txt || txt.length < 120) continue;
    const hasWork = txt.includes("工作经历");
    const hasEdu = txt.includes("教育经历");
    const hasSidebarNoise = /(最近关注|同事沟通|职优|吾思职优|立即沟通|打招呼)/.test(txt);
    let score = 0;
    if (hasWork) score += 5;
    if (hasEdu) score += 4;
    if (hasWork && hasEdu) score += 8;
    if (txt.includes("项目经验")) score += 2;
    if (txt.includes("最近关注")) score -= 3;
    if (hasSidebarNoise) score -= 8;
    if (txt.includes("在职") || txt.includes("离职")) score += 1;
    if (/\d{1,2}\s*岁/.test(txt) && /\d+\s*\+?\s*年/.test(txt) && /(博士后|博士|硕士|本科|大专|中专|高中|初中)/.test(txt)) score += 3;
    const rect = el.getBoundingClientRect();
    if (rect.width >= 480 && rect.width <= 1200) score += 2;
    if (rect.width >= 700) score += 2;
    if (rect.width < 420) score -= 6;
    if (rect.height >= 420) score += 2;
    if (rect.left >= window.innerWidth * 0.55) score -= 6;
    else if (rect.left <= window.innerWidth * 0.45) score += 2;
    if (rect.left >= 0 && rect.right <= window.innerWidth) score += 1;
    if (score <= 0) continue;
    if (txt.length > 32000) score -= 3;
    candidates.push({ el, score, len: txt.length });
  }
  candidates.sort((a, b) => {
    if (b.score !== a.score) return b.score - a.score;
    return a.len - b.len;
  });
  return candidates.length ? candidates[0].el : null;
}

function pickBossResumeIframe() {
  if (!isBossSite() || isBossResumeFrame()) return null;
  const frames = document.querySelectorAll("iframe");
  for (const frame of frames) {
    const src = cleanText(frame.getAttribute("src") || frame.getAttribute("data-src") || frame.src || "");
    if (!src) continue;
    if (!/c-resume/i.test(src)) continue;
    return frame;
  }
  return null;
}

function pickResumeRoot() {
  if (isBossSite()) {
    const popupRoot = pickBossPopupRoot();
    if (popupRoot) return popupRoot;
  }
  const candidates = [];
  const all = document.querySelectorAll("main,section,article,div");
  const maxScan = Math.min(all.length, 2500);
  for (let i = 0; i < maxScan; i++) {
    const el = all[i];
    if (!el || el === document.body || el === document.documentElement) continue;
    const txt = cleanText(el.innerText || "");
    if (!txt || txt.length < 120) continue;
    const hasWork = txt.includes("工作经历");
    const hasEdu = txt.includes("教育经历");
    const hasSidebarNoise = /(最近关注|同事沟通|职优|吾思职优|立即沟通|打招呼)/.test(txt);
    let score = 0;
    if (hasWork) score += 4;
    if (txt.includes("期望职位")) score += 3;
    if (txt.includes("项目经验")) score += 2;
    if (hasEdu) score += 2;
    if (hasWork && hasEdu) score += 6;
    if (txt.includes("最近关注")) score -= 3;
    if (hasSidebarNoise) score -= 7;
    if (/\d{1,2}\s*岁/.test(txt) && /\d+\s*\+?\s*年/.test(txt)) score += 2;
    if (score <= 0) continue;
    if (txt.length > 22000) score -= 4;
    else if (txt.length > 15000) score -= 2;
    const rect = el.getBoundingClientRect();
    if (rect.width >= 700) score += 2;
    if (rect.width < 420) score -= 6;
    if (rect.left >= window.innerWidth * 0.55) score -= 5;
    else if (rect.left <= window.innerWidth * 0.45) score += 2;
    candidates.push({ el, score, len: txt.length });
  }
  const anchor = document.querySelector("[data-geek-id],[data-resume-id],[data-cv-id]");
  if (anchor) {
    const c = anchor.closest("article,section,main,div");
    if (c) {
      const txt = cleanText(c.innerText || "");
      if (txt) candidates.push({ el: c, score: 10, len: txt.length });
    }
  }
  const dedup = [];
  const seen = new Set();
  for (const item of candidates) {
    if (seen.has(item.el)) continue;
    seen.add(item.el);
    dedup.push(item);
  }
  dedup.sort((a, b) => {
    if (b.score !== a.score) return b.score - a.score;
    return a.len - b.len;
  });
  if (dedup.length > 0) return dedup[0].el;
  return document.body;
}

function clampCaptureRect(rect, viewportWidth, viewportHeight) {
  const vw = Math.max(1, Number(viewportWidth) || window.innerWidth || 1);
  const vh = Math.max(1, Number(viewportHeight) || window.innerHeight || 1);
  const left = Math.max(0, Math.min(vw - 1, Math.floor(Number(rect.left) || 0)));
  const top = Math.max(0, Math.min(vh - 1, Math.floor(Number(rect.top) || 0)));
  const right = Math.max(left + 1, Math.min(vw, Math.ceil(Number(rect.right) || (left + 1))));
  const bottom = Math.max(top + 1, Math.min(vh, Math.ceil(Number(rect.bottom) || (top + 1))));
  return {
    left,
    top,
    width: Math.max(1, right - left),
    height: Math.max(1, bottom - top),
    viewportWidth: vw,
    viewportHeight: vh,
  };
}

function pickResumeCaptureRegion() {
  const viewportWidth = Math.max(1, window.innerWidth || document.documentElement?.clientWidth || 1);
  const viewportHeight = Math.max(1, window.innerHeight || document.documentElement?.clientHeight || 1);
  const entries = [];
  const noiseRe = /(最近关注|同事沟通|职优|吾思职优|立即沟通|打招呼|收藏|已收藏|感兴趣|不感兴趣|屏蔽|不合适|举报|转发)/;

  function pushElement(el, baseScore, source) {
    if (!el || typeof el.getBoundingClientRect !== "function") return;
    const rect = el.getBoundingClientRect();
    if (!rect || rect.width < 260 || rect.height < 220) return;
    const txt = cleanText(el.innerText || el.textContent || "");
    let score = Number(baseScore) || 0;
    if (hasLooseTitle(txt, "经历概览")) score += 10;
    if (hasLooseTitle(txt, "工作经历")) score += 8;
    if (hasLooseTitle(txt, "项目经验")) score += 6;
    if (hasLooseTitle(txt, "教育经历")) score += 2;
    if (noiseRe.test(txt)) score -= 10;
    if (rect.left <= viewportWidth * 0.48) score += 8;
    else score -= 8;
    if (rect.width >= viewportWidth * 0.45) score += 6;
    if (rect.width < viewportWidth * 0.3) score -= 5;
    if (rect.height >= viewportHeight * 0.45) score += 4;
    if (score <= 0) return;
    const hasMrMs = /[\u4e00-\u9fa5]{1,8}(先生|女士)/.test(txt);
    const hasTitleKw = /(工程师|开发|测试|架构|算法|前端|后端|全栈|运维|产品|设计|经理|总监|主管|专员|顾问|主任|老师|销售|运营|财务|人事|程序员)/.test(txt);
    entries.push({
      source,
      score,
      textLen: txt.length,
      hasMrMs,
      hasTitleKw,
      rect: clampCaptureRect(
        {
          left: rect.left - 8,
          top: rect.top - 8,
          right: rect.right + 8,
          bottom: rect.bottom + 8,
        },
        viewportWidth,
        viewportHeight
      ),
    });
  }

  const root = pickResumeRoot();
  pushElement(root, 30, "pickResumeRoot");

  const popupRoot = pickBossPopupRoot();
  if (popupRoot && popupRoot !== root) pushElement(popupRoot, 20, "pickBossPopupRoot");

  if (isBossSite()) {
    const frames = document.querySelectorAll("iframe");
    for (const frame of frames) {
      const src = cleanText(frame.getAttribute("src") || frame.getAttribute("data-src") || frame.src || "");
      if (!src || !/\/web\/frame\/(?:recommend(?:-v\d+)?|c-resume)\b/i.test(src)) continue;
      pushElement(frame, 36, "bossResumeIframe");
    }
  }

  const all = document.querySelectorAll("main,section,article,div");
  const maxScan = Math.min(all.length, 1200);
  for (let i = 0; i < maxScan; i++) {
    pushElement(all[i], 4, "genericBlock");
  }

  entries.sort((a, b) => {
    if (b.score !== a.score) return b.score - a.score;
    const areaA = a.rect.width * a.rect.height;
    const areaB = b.rect.width * b.rect.height;
    if (areaB !== areaA) return areaB - areaA;
    return b.textLen - a.textLen;
  });

  if (entries.length > 0) {
    // #region agent log
    agentDebugLogContent(`run_${Date.now()}`, "H9_H10", "content.js:pickResumeCaptureRegion", "capture region selected", {
      source: entries[0].source,
      score: entries[0].score,
      textLen: entries[0].textLen,
      hasMrMs: Boolean(entries[0].hasMrMs),
      hasTitleKw: Boolean(entries[0].hasTitleKw),
      left: entries[0].rect.left,
      top: entries[0].rect.top,
      width: entries[0].rect.width,
      height: entries[0].rect.height
    });
    // #endregion
    return {
      ...entries[0].rect,
      score: entries[0].score,
      source: entries[0].source,
    };
  }

  return {
    left: 0,
    top: 0,
    width: Math.max(1, Math.floor(viewportWidth * 0.72)),
    height: viewportHeight,
    viewportWidth,
    viewportHeight,
    score: 1,
    source: "fallbackViewportLeft",
  };
}

function extractCandidateId(resumeRoot) {
  const u = new URL(location.href);
  const fromQuery =
    u.searchParams.get("geekId") ||
    u.searchParams.get("geek_id") ||
    u.searchParams.get("candidateId") ||
    u.searchParams.get("resumeId") ||
    u.searchParams.get("uid");
  const queryId = normalizeSourceCandidateId(fromQuery);
  if (queryId) return queryId;
  const scope = resumeRoot && typeof resumeRoot.querySelector === "function" ? resumeRoot : null;
  const attrNodes = [];
  if (scope && typeof scope.getAttribute === "function") {
    attrNodes.push(scope);
  }
  const nestedAttrNode = (scope || document).querySelector("[data-geek-id],[data-resume-id],[data-cv-id]");
  if (nestedAttrNode) {
    attrNodes.push(nestedAttrNode);
  }
  for (const node of attrNodes) {
    if (!node || typeof node.getAttribute !== "function") continue;
    const rawId = node.getAttribute("data-geek-id") || node.getAttribute("data-resume-id") || node.getAttribute("data-cv-id");
    const attrId = normalizeSourceCandidateId(rawId);
    if (attrId) return attrId;
  }
  const htmlText = resumeRoot && resumeRoot.innerHTML ? resumeRoot.innerHTML : "";
  const fromHtml =
    htmlText.match(/"(?:geekId|resumeId|candidateId|cvId)"\s*:\s*"([A-Za-z0-9_-]{1,200})"/i) ||
    htmlText.match(/(?:geekId|resumeId|candidateId|cvId)=([A-Za-z0-9_-]{1,200})/i);
  if (fromHtml) {
    const htmlId = normalizeSourceCandidateId(fromHtml[1]);
    if (htmlId) return htmlId;
  }
  const pathMatch = String(location.pathname || "").match(/\/(?:resume|geek|candidate)\/([A-Za-z0-9_-]{1,200})(?:[/?#]|$)/i);
  if (pathMatch) {
    const pathId = normalizeSourceCandidateId(pathMatch[1]);
    if (pathId) return pathId;
  }
  const explicitParamMatch = `${location.pathname}${location.search}${location.hash}`.match(/(?:[?&#](?:geekId|geek_id|candidateId|resumeId|uid)=)([A-Za-z0-9_-]{1,200})(?:[&#/]|$)/i);
  if (!explicitParamMatch) return "";
  return normalizeSourceCandidateId(explicitParamMatch[1]);
}

function extractNameToken(text) {
  const t = stripBossUiPrefix(cleanText(text));
  if (!t) return "";
  const m = t.match(/([\u4e00-\u9fa5]{1,8}(?:先生|女士))/);
  if (!m) return "";
  const name = stripBossUiPrefix(cleanText(m[1]));
  if (isBossNoiseName(name)) return "";
  if (/(工作经历|项目经验|教育经历|最近关注|同事沟通|工作概览|简历详情|牛人诊断工具|查看示例|立即沟通|打招呼|经历概览|不合适|举报|转发|转发牛人|收藏|屏蔽)/.test(name)) return "";
  if (/(公司|集团|大学|学院|学校|工程师|经理|总监|主管)/.test(name)) return "";
  if (!isStrictCandidateName(name)) return "";
  return name;
}

function extractNameByLabel(text) {
  const t = stripBossUiPrefix(cleanText(text));
  if (!t) return "";
  const m = t.match(/姓名\s*[:：]?\s*([\u4e00-\u9fa5]{1,8}(?:先生|女士)|[\u4e00-\u9fa5]{2,4})/);
  if (!m) return "";
  const name = stripBossUiPrefix(cleanText(m[1]));
  if (!name || isBossNoiseName(name)) return "";
  if (/(公司|集团|大学|学院|学校|工程师|经理|总监|主管|经历|概览|简历|详情|沟通|打招呼|收藏|屏蔽|举报|转发|职位|人才库)/.test(name)) return "";
  if (!/^[\u4e00-\u9fa5]{2,4}$/.test(name) && !/^[\u4e00-\u9fa5]{1,8}(先生|女士)$/.test(name)) return "";
  return name;
}

function extractRealName(text) {
  const t = stripBossUiPrefix(cleanText(text));
  if (!t) return "";
  const byLabel = extractNameByLabel(t);
  if (byLabel) return byLabel;
  const m = t.match(/^([\u4e00-\u9fa5]{2,4})(?:\s*[\|｜]|\s+[男女]|\s+\d{1,2}\s*岁|\s*[（(]\s*[男女]\s*[)）]|\s|$)/);
  if (m) {
    const name = stripBossUiPrefix(cleanText(m[1]));
    if (name && !isBossNoiseName(name) && !/(公司|集团|大学|学院|学校|工程师|经理|总监|主管|经历|概览|简历|详情|沟通|打招呼|收藏|屏蔽|举报|转发|职位|人才库)/.test(name)) return name;
  }
  if (/^[\u4e00-\u9fa5]{2,4}$/.test(t) && !isBossNoiseName(t) && !/(公司|集团|大学|学院|学校|工程师|经理|总监|主管|经历|概览|简历|详情|沟通|打招呼|收藏|屏蔽|举报|转发)/.test(t)) {
    return t;
  }
  return "";
}

function getHeaderNameLines(lines) {
  if (!Array.isArray(lines) || !lines.length) return [];
  const stop = findNextSectionIndex(lines, 0, ["经历概览", "工作经历", "项目经验", "教育经历"]);
  const end = stop > 0 ? Math.min(stop, 80) : Math.min(lines.length, 80);
  return lines.slice(0, Math.max(1, end));
}

function getNameNoisePenalty(line) {
  const t = cleanText(line);
  if (!t) return 0;
  if (/(工作经历|项目经验|教育经历|经历概览|工作概览|简历详情|最近关注|同事沟通|在线活跃|牛人诊断工具|查看示例|立即沟通|打招呼|收藏|屏蔽|举报|转发)/.test(t)) return -90;
  if (/(基本信息|个人信息|个人资料|个人介绍|简历|姓名|职位|人才库)/.test(t)) return -28;
  return 0;
}

function getNameLengthScore(name) {
  const core = cleanText(name).replace(/(先生|女士)$/u, "");
  if (core.length === 2 || core.length === 3) return 12;
  if (core.length === 4) return 7;
  if (core.length === 1) return 1;
  return 0;
}

function pushNameCandidate(candidates, name, source, lineIdx, lineText) {
  const n = cleanText(name);
  if (!n || isBossNoiseName(n) || !isStrictCandidateName(n)) return;
  const baseMap = {
    label: 120,
    selectorLabel: 112,
    selectorReal: 102,
    headerReal: 96,
    headerPrefix: 88,
    headerMrMs: 80,
    joinedMrMs: 72,
    loose: 60,
  };
  let score = (baseMap[source] || 0) + getNameLengthScore(n);
  if (/(先生|女士)$/.test(n)) score -= 2;
  if (source !== "label" && source !== "selectorLabel") score += getNameNoisePenalty(lineText);
  score -= Math.min(Math.max(0, Number(lineIdx) || 0), 40) * 0.12;
  if (score <= 0) return;
  const old = candidates.get(n);
  if (!old || score > old.score) candidates.set(n, { name: n, score });
}

function guessName(lines, resumeRoot) {
  const candidates = new Map();
  const headerLines = getHeaderNameLines(lines);
  for (let i = 0; i < Math.min(headerLines.length, 60); i++) {
    pushNameCandidate(candidates, extractNameByLabel(headerLines[i]), "label", i, headerLines[i]);
  }
  const headerJoined = headerLines.slice(0, 80).join(" ");
  pushNameCandidate(candidates, extractNameByLabel(headerJoined), "label", 0, headerJoined);
  const selectorSet = isBossSite()
    ? [
      ".geek-name",
      ".resume-name",
      "[data-role='candidate-name']",
      ".candidate-name"
    ]
    : [
      ".geek-name",
      ".name",
      ".resume-name",
      "[data-role='candidate-name']",
      ".candidate-name",
      "h1",
      "h2"
    ];
  const fromSelectors = firstMatchText(selectorSet, resumeRoot);
  if (fromSelectors) {
    pushNameCandidate(candidates, extractNameByLabel(fromSelectors), "selectorLabel", 0, fromSelectors);
    pushNameCandidate(candidates, extractRealName(fromSelectors), "selectorReal", 0, fromSelectors);
    pushNameCandidate(candidates, extractNameToken(fromSelectors), "headerMrMs", 0, fromSelectors);
  }
  for (let i = 0; i < Math.min(headerLines.length, 50); i++) {
    const line = headerLines[i];
    if (!line) continue;
    const byRealName = line.match(/^([\u4e00-\u9fa5]{2,4})(?:\s*\||\s+男|\s+女|\s+\d{1,2}\s*岁|\s|$)/);
    if (byRealName) pushNameCandidate(candidates, extractRealName(byRealName[1]), "headerReal", i, line);
    const byPrefix = line.match(/^([\u4e00-\u9fa5]{1,8}(?:先生|女士))(?:\s*\||\s+\d{1,2}\s*岁|\s|$)/);
    if (byPrefix) pushNameCandidate(candidates, extractNameToken(byPrefix[1]), "headerPrefix", i, line);
    const byMrMs = line.match(/^([\u4e00-\u9fa5]{1,8}(?:先生|女士))(?:\s|$)/);
    if (byMrMs) pushNameCandidate(candidates, extractNameToken(byMrMs[1]), "headerMrMs", i, line);
    if (!/[：:]/.test(line) && /^[\u4e00-\u9fa5]{2,4}$/.test(line) && !/(公司|经历|大学|学院|基本信息|个人信息|个人资料|个人介绍|简历)/.test(line)) {
      pushNameCandidate(candidates, extractRealName(line), "loose", i, line);
    }
  }
  pushNameCandidate(candidates, extractNameToken(headerJoined), "joinedMrMs", headerLines.length, headerJoined);
  if (!candidates.size) return "";
  const ranked = Array.from(candidates.values()).sort((a, b) => b.score - a.score);
  return ranked[0]?.name || "";
}

function trimSectionTitle(line, title) {
  const text = cleanText(line);
  if (!text) return "";
  if (!title || !text.startsWith(title)) return text;
  return cleanText(text.slice(title.length).replace(/^[:：]\s*/, ""));
}

function buildLooseTitleRegExp(title) {
  const chars = String(title || "").split("").map((c) => c.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));
  return new RegExp(chars.join("\\s*"));
}

function hasLooseTitle(text, title) {
  const t = cleanText(text);
  if (!t || !title) return false;
  if (t.includes(title)) return true;
  return buildLooseTitleRegExp(title).test(t);
}

function findSectionIndex(lines, title, fromIdx) {
  const start = Number.isInteger(fromIdx) ? Math.max(0, fromIdx) : 0;
  for (let i = start; i < lines.length; i++) {
    const line = cleanText(lines[i]);
    if (!line) continue;
    if (line === title) return i;
    if (line.startsWith(`${title}：`) || line.startsWith(`${title}:`) || line.startsWith(`${title} `)) return i;
    if (line.startsWith(title)) return i;
    if (hasLooseTitle(line, title)) return i;
  }
  return -1;
}

function findNextSectionIndex(lines, fromIdx, titles) {
  const start = Number.isInteger(fromIdx) ? Math.max(0, fromIdx) : 0;
  let best = -1;
  for (const title of titles) {
    const idx = findSectionIndex(lines, title, start);
    if (idx >= 0 && (best < 0 || idx < best)) best = idx;
  }
  return best;
}

function collectSectionLines(lines, startIdx, endIdx, title) {
  if (!Number.isInteger(startIdx) || startIdx < 0 || startIdx >= lines.length) return [];
  const end = Number.isInteger(endIdx) && endIdx > startIdx ? Math.min(endIdx, lines.length) : lines.length;
  const out = [];
  const firstTail = trimSectionTitle(lines[startIdx], title);
  if (firstTail) out.push(firstTail);
  for (let i = startIdx + 1; i < end; i++) {
    const line = cleanText(lines[i]);
    if (line) out.push(line);
  }
  return out;
}

function normalizeWorkExperienceText(lines) {
  if (!Array.isArray(lines) || !lines.length) return "";
  const out = [];
  for (const row of lines) {
    const line = cleanText(row);
    if (!line) continue;
    if (/^(工作经历|经历概览|最近关注|同事沟通|工作概览)$/.test(line) || hasLooseTitle(line, "工作经历")) continue;
    out.push(line);
  }
  return out.join("\n").slice(0, 8000);
}

function extractWorkExperienceTextFromRawText(rawText) {
  const text = String(rawText || "");
  if (!text) return "";
  const re = /工\s*作\s*经\s*历[:：]?\s*([\s\S]{20,12000}?)(?:项\s*目\s*经\s*验|教\s*育\s*经\s*历|自\s*我\s*评\s*价|语\s*言\s*能\s*力|证\s*书|技\s*能|最\s*近\s*关\s*注|同\s*事\s*沟\s*通|工\s*作\s*概\s*览|$)/;
  const m = text.match(re);
  if (!m) return "";
  const block = String(m[1] || "")
    .replace(/\u00a0/g, " ")
    .replace(/[ \t]+\n/g, "\n")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
  return normalizeWorkExperienceText(splitLines(block));
}

function extractWorkExperienceText(lines) {
  if (!Array.isArray(lines) || !lines.length) return "";
  const workIdx = findSectionIndex(lines, "工作经历", 0);
  if (workIdx < 0) return "";
  const workEnd = findNextSectionIndex(lines, workIdx + 1, ["项目经验", "教育经历", "自我评价", "语言能力", "证书", "技能", "最近关注", "同事沟通", "工作概览"]);
  const workLines = collectSectionLines(lines, workIdx, workEnd, "工作经历");
  return normalizeWorkExperienceText(workLines);
}

function normalizeWorkYearsNumber(text) {
  const m = cleanText(text).match(/(\d+)\s*\+?\s*年/);
  return m ? Number(m[1]) : -1;
}

function parseBossHeaderByOrder(lines, headerEndIdx) {
  const stop = headerEndIdx > 0 ? Math.min(headerEndIdx, lines.length) : Math.min(lines.length, 40);
  const scanEnd = Math.min(stop, 20);
  let name = "";
  let nameIdx = -1;
  for (let i = 0; i < scanEnd; i++) {
    const line = cleanText(lines[i]);
    if (!line) continue;
    if (/(工作经历|项目经验|教育经历|最近关注|同事沟通|工作概览|简历详情|经历概览)/.test(line)) continue;
    const rn = extractRealName(line);
    if (rn) {
      name = rn;
      nameIdx = i;
      break;
    }
    const m = line.match(/([\u4e00-\u9fa5]{1,8}(?:先生|女士))/);
    if (!m) continue;
    const token = stripBossUiPrefix(cleanText(m[1]));
    if (isBossNoiseName(token) || !isStrictCandidateName(token)) continue;
    name = token;
    nameIdx = i;
    break;
  }
  const profileStart = nameIdx >= 0 ? Math.min(nameIdx + 1, lines.length) : 0;
  const profileStop = Math.min(stop, profileStart + 10);
  let workYears = "";
  let educationHighest = "";
  for (let i = profileStart; i < profileStop; i++) {
    const line = cleanText(lines[i]);
    if (!line) continue;
    if (!workYears && /\d{1,2}\s*岁/.test(line)) {
      const y = normalizeWorkYearsText(line);
      if (y) workYears = y;
    }
    if (!educationHighest) {
      const e = extractEducationKeyword(line);
      if (e) educationHighest = e;
    }
  }
  if (!workYears) {
    let best = "";
    let bestNum = -1;
    for (let i = profileStart; i < profileStop; i++) {
      const y = normalizeWorkYearsText(lines[i]);
      if (!y) continue;
      const num = normalizeWorkYearsNumber(y);
      if (num > bestNum) {
        bestNum = num;
        best = y;
      }
    }
    workYears = best;
  }
  return { name, workYears, educationHighest };
}

function parseBossExpectedTitleByOrder(sectionLines) {
  for (const raw of sectionLines.slice(0, 8)) {
    const line = cleanText(raw);
    if (!line) continue;
    const tokens = line
      .split(/\s+|[|｜]/)
      .map((t) => cleanText(t))
      .filter(Boolean)
      .filter((t) => !/^行业/.test(t) && !/^面议$/.test(t) && !/^\d+(?:\.\d+)?\s*-\s*\d+(?:\.\d+)?\s*[kKwW]$/.test(t) && !/^\d+(?:\.\d+)?\s*[kKwW]$/.test(t));
    for (const token of tokens) {
      if (/(工程师|开发|测试|架构|算法|前端|后端|全栈|运维|产品|设计|经理|总监|顾问|专员|主管|主任|讲师|老师|销售|运营|财务|人事|程序员)/.test(token)) {
        return token;
      }
    }
  }
  return "";
}

function normalizeBossWorkLine(line) {
  return cleanText(line)
    .replace(/\d{4}[.\-/]\d{1,2}\s*[-~至]+\s*(?:至今|\d{4}[.\-/]\d{1,2})/g, " ")
    .replace(/\d+\s*年\s*\d*\s*个月/g, " ")
    .replace(/\d+\s*个月/g, " ")
    .replace(/^[一二三四五六七八九十\d]+[、.．)\]]\s*/, " ")
    .trim();
}

function isLikelyCompanyText(text) {
  const t = cleanText(text);
  if (!t) return false;
  return /(?:有限公司|股份有限公司|公司|集团|研究院|研究所|中心|工作室|事务所|银行|医院|科技|软件|信息|网络|电子|通信|汽车|工业|制造|大学|学院|学校)/.test(t);
}

function isLikelyTitleText(text) {
  const t = cleanText(text);
  if (!t) return false;
  if (/(工程师|开发|测试|架构|算法|前端|后端|全栈|运维|产品|设计|经理|总监|顾问|专员|主管|主任|讲师|老师|销售|运营|财务|人事|程序员)/.test(t)) return true;
  if (t.length <= 24 && /(java|python|golang|go|php|c\+\+|c#|前端|后端|全栈)/i.test(t)) return true;
  return false;
}

function fixCompanyTitleOrder(currentCompany, currentTitle) {
  const company = cleanText(currentCompany);
  const title = cleanText(currentTitle);
  if (!company && !title) return { currentCompany: "", currentTitle: "" };
  if (company && title && isLikelyTitleText(company) && isLikelyCompanyText(title)) {
    return { currentCompany: title, currentTitle: company };
  }
  if (!company && title && isLikelyCompanyText(title) && !isLikelyTitleText(title)) {
    return { currentCompany: title, currentTitle: "" };
  }
  if (!title && company && isLikelyTitleText(company) && !isLikelyCompanyText(company)) {
    return { currentCompany: "", currentTitle: company };
  }
  return { currentCompany: company, currentTitle: title };
}

function parseCompanyTitleFromBossLine(line) {
  const text = normalizeBossWorkLine(line);
  if (!text) return { currentCompany: "", currentTitle: "" };
  const m = text.match(/^(.+?(?:有限公司|股份有限公司|公司|集团|研究院|研究所|中心|工作室|事务所|银行|医院|科技|软件|信息|网络|电子|通信|汽车|工业|制造))(?:[\s|｜/]+)(.+)$/);
  if (m) {
    return fixCompanyTitleOrder(
      cleanText(m[1]),
      cleanText(m[2]).replace(/^[\s|｜/]+/, "").replace(/[·•｜|].*$/, "")
    );
  }
  const parts = text.split(/[\s|｜/]+/).filter(Boolean);
  if (parts.length >= 2) {
    const first = cleanText(parts[0]);
    const second = cleanText(parts[1]).replace(/[·•｜|].*$/, "");
    if (isLikelyCompanyText(first) && (!isLikelyCompanyText(second) || isLikelyTitleText(second))) {
      return fixCompanyTitleOrder(first, second);
    }
    if (isLikelyCompanyText(second) && isLikelyTitleText(first)) {
      return fixCompanyTitleOrder(second, first);
    }
  }
  if (parts.length === 1 && isLikelyCompanyText(parts[0])) {
    return {
      currentCompany: cleanText(parts[0]),
      currentTitle: ""
    };
  }
  return { currentCompany: "", currentTitle: "" };
}

function parseBossWorkByOrder(sectionLines, expectedTitle) {
  let currentCompany = "";
  let currentTitle = "";
  const timeRe = /\d{4}[.\-/]\d{1,2}\s*[-~至]+\s*(?:至今|\d{4}[.\-/]\d{1,2})/;
  const titleKwRe = /(工程师|开发|测试|架构|算法|前端|后端|全栈|运维|产品|设计|经理|总监|顾问|专员|主管|主任|讲师|老师|销售|运营|财务|人事|程序员)/;
  let companyIdx = -1;
  for (let i = 0; i < Math.min(sectionLines.length, 24); i++) {
    const line = cleanText(sectionLines[i]);
    if (!line) continue;
    if (/^(业绩|内容|职责|项目经历|教育经历|工作内容|最近关注|同事沟通)/.test(line)) continue;
    let parsed = parseCompanyTitleFromBossLine(line);
    if ((!parsed.currentCompany && !parsed.currentTitle) && i + 1 < sectionLines.length && timeRe.test(sectionLines[i + 1])) {
      parsed = parseCompanyTitleFromBossLine(`${line} ${sectionLines[i + 1]}`);
    }
    if (parsed.currentCompany || parsed.currentTitle) {
      currentCompany = parsed.currentCompany || currentCompany;
      currentTitle = parsed.currentTitle || currentTitle;
      companyIdx = i;
      break;
    }
  }
  if (currentCompany && !currentTitle && companyIdx >= 0) {
    for (let j = companyIdx + 1; j < Math.min(sectionLines.length, companyIdx + 6); j++) {
      const next = normalizeBossWorkLine(sectionLines[j]);
      if (!next) continue;
      if (/^(业绩|内容|职责|项目经历|教育经历|工作内容|最近关注|同事沟通)/.test(next)) continue;
      if (timeRe.test(next)) continue;
      if (titleKwRe.test(next) && next.length <= 40) {
        currentTitle = next.replace(/[·•｜|].*$/, "");
        break;
      }
    }
  }
  if (!currentCompany || !currentTitle) {
    for (let i = 0; i < Math.min(sectionLines.length, 16); i++) {
      const line = normalizeBossWorkLine(sectionLines[i]);
      if (!line) continue;
      if (!currentCompany && /(?:有限公司|股份有限公司|公司|集团|研究院|研究所|科技|软件|信息|网络|电子|通信|汽车|工业|制造)/.test(line)) {
        currentCompany = line;
      }
      if (currentCompany && !currentTitle) {
        for (let j = i + 1; j < Math.min(sectionLines.length, i + 5); j++) {
          const next = normalizeBossWorkLine(sectionLines[j]);
          if (!next) continue;
          if (/^(业绩|内容|职责|项目经历|教育经历|工作内容)/.test(next)) continue;
          if (next.length <= 40) {
            currentTitle = next.replace(/[·•｜|].*$/, "");
            break;
          }
        }
      }
      if (currentCompany && currentTitle) break;
    }
  }
  if (!currentTitle && expectedTitle) currentTitle = expectedTitle;
  return fixCompanyTitleOrder(currentCompany, currentTitle);
}

function parseBossEducationByOrder(sectionLines, fallbackEducation) {
  let educationSchool = "";
  let educationHighest = fallbackEducation || "";
  for (const line of sectionLines.slice(0, 30)) {
    const text = cleanText(line);
    if (!text) continue;
    if (!educationSchool) {
      const school = extractSchoolName(text);
      if (school) educationSchool = school;
    }
    if (!educationHighest) {
      const edu = extractEducationKeyword(text);
      if (edu) educationHighest = edu;
    }
    if (educationSchool && educationHighest) break;
  }
  return { educationSchool, educationHighest };
}

function parseBossByOrderedSections(lines) {
  if (!isBossSite() || !Array.isArray(lines) || !lines.length) return null;
  const expectedIdx = findSectionIndex(lines, "期望职位", 0);
  const workIdx = findSectionIndex(lines, "工作经历", expectedIdx >= 0 ? expectedIdx : 0);
  const projectIdx = findSectionIndex(lines, "项目经历", workIdx >= 0 ? workIdx : 0);
  const educationIdx = findSectionIndex(lines, "教育经历", workIdx >= 0 ? workIdx : 0);
  if (expectedIdx < 0 && workIdx < 0 && educationIdx < 0) return null;
  const headerEnd = expectedIdx >= 0 ? expectedIdx : (workIdx >= 0 ? workIdx : Math.min(lines.length, 40));
  const header = parseBossHeaderByOrder(lines, headerEnd);
  const expectedLines = collectSectionLines(lines, expectedIdx, workIdx > expectedIdx ? workIdx : -1, "期望职位");
  const expectedTitle = parseBossExpectedTitleByOrder(expectedLines);
  const workEndCandidates = [projectIdx, educationIdx].filter((x) => x > workIdx);
  const workEnd = workEndCandidates.length ? Math.min(...workEndCandidates) : -1;
  const workLines = collectSectionLines(lines, workIdx, workEnd, "工作经历");
  const workExperienceText = normalizeWorkExperienceText(workLines);
  const workInfo = parseBossWorkByOrder(workLines, expectedTitle);
  const educationEnd = findNextSectionIndex(lines, educationIdx >= 0 ? educationIdx + 1 : 0, ["自我评价", "语言能力", "证书", "技能", "最近关注", "同事沟通"]);
  const educationLines = collectSectionLines(lines, educationIdx, educationEnd, "教育经历");
  const educationInfo = parseBossEducationByOrder(educationLines, header.educationHighest);
  return {
    name: header.name,
    workYears: header.workYears,
    educationSchool: educationInfo.educationSchool,
    educationHighest: educationInfo.educationHighest || header.educationHighest || "",
    currentCompany: workInfo.currentCompany,
    currentTitle: workInfo.currentTitle || expectedTitle || "",
    workExperienceText
  };
}

function guessProfileLine(lines) {
  if (isBossSite()) {
    const topLines = lines.slice(0, 40);
    for (const l of topLines) {
      if (/\d{1,2}\s*岁/.test(l) && /\d+\s*\+?\s*年/.test(l)) return l;
      if (/\d+\s*\+?\s*年/.test(l) && /(博士后|博士|硕士|本科|大专|中专|高中|初中)/.test(l)) return l;
    }
  }
  return lines.find((l) => /\d{1,2}\s*岁/.test(l) && /\d+\s*\+?\s*年/.test(l)) || lines.find((l) => /\d+\s*\+?\s*年/.test(l) && /(博士后|博士|硕士|本科|大专|中专|高中|初中)/.test(l)) || "";
}

function guessEducation(lines, profileLine, resumeRoot) {
  const fromSelectors = firstMatchText([
    ".education",
    ".edu",
    "[data-role='candidate-education']"
  ], resumeRoot);
  const fromSelectorKeyword = extractEducationKeyword(fromSelectors);
  if (fromSelectorKeyword) return fromSelectorKeyword;
  const fromProfileKeyword = extractEducationKeyword(profileLine);
  if (fromProfileKeyword) return fromProfileKeyword;
  if (isBossSite()) {
    for (const line of lines.slice(0, 80)) {
      const k = extractEducationKeyword(line);
      if (k) return k;
    }
  }
  const m2 = extractEducationKeyword(lines.join(" "));
  if (m2) return m2;
  return "";
}

function guessSchool(lines, resumeRoot) {
  const fromSelectors = firstMatchText([
    ".school",
    ".school-name",
    ".edu-school",
    "[data-role='candidate-school']",
    "[class*='school']",
    "[class*='School']"
  ], resumeRoot);
  const fromSelectorSchool = extractSchoolName(fromSelectors);
  if (fromSelectorSchool) return fromSelectorSchool;
  const sectionStart = lines.findIndex((l) => /^教育经历/.test(l));
  if (sectionStart >= 0) {
    for (let i = sectionStart + 1; i < Math.min(lines.length, sectionStart + 80); i++) {
      const line = lines[i];
      if (!line) continue;
      if (/^(工作经历|项目经验|自我评价|语言能力|证书|技能|最近关注|在线活跃|同事沟通)/.test(line)) break;
      const school = extractSchoolName(line);
      if (school) return school;
    }
  }
  for (const line of lines.slice(0, 120)) {
    const school = extractSchoolName(line);
    if (school) return school;
  }
  return "";
}

function guessWorkYears(lines, profileLine, resumeRoot) {
  const fromSelectors = firstMatchText([
    ".work-years",
    ".experience",
    "[data-role='candidate-experience']"
  ], resumeRoot);
  const fromSelectorsYears = normalizeWorkYearsText(fromSelectors);
  if (fromSelectorsYears) return fromSelectorsYears;
  const fromProfileYears = normalizeWorkYearsText(profileLine);
  if (fromProfileYears) return fromProfileYears;
  if (isBossSite()) {
    for (const line of lines.slice(0, 80)) {
      const years = normalizeWorkYearsText(line);
      if (years) return years;
    }
  }
  const m2 = normalizeWorkYearsText(lines.join(" "));
  return m2 || "";
}

function guessFromExpectedLine(lines) {
  const idx = lines.findIndex((l) => /^期望职位/.test(l));
  if (idx < 0) return { currentTitle: "", currentCompany: "" };
  let line = lines[idx].replace(/^期望职位[:：]?\s*/, "").trim();
  if (!line && lines[idx + 1]) line = lines[idx + 1];
  if (!line) return { currentTitle: "", currentCompany: "" };
  const tokens = line.split(/\s+/).filter(Boolean);
  const filtered = tokens.filter((t) => !/^行业/.test(t) && !/^\d+(?:\.\d+)?\s*-\s*\d+(?:\.\d+)?\s*[kKwW]$/.test(t) && !/^\d+(?:\.\d+)?\s*[kKwW]$/.test(t) && !/^面议$/.test(t));
  if (!filtered.length) return { currentTitle: "", currentCompany: "" };
  const titleHint = filtered.find((t) => /(工程师|开发|测试|架构|算法|前端|后端|全栈|运维|产品|设计|经理|总监|顾问|专员|主管|主任|讲师|老师|销售|运营|财务|人事)/.test(t));
  if (titleHint) return { currentTitle: titleHint, currentCompany: "" };
  if (filtered.length >= 2) return { currentTitle: filtered[1], currentCompany: "" };
  return { currentTitle: filtered[0], currentCompany: "" };
}

function guessCurrentWork(lines, resumeRoot) {
  const fromSelectorsTitle = firstMatchText([
    ".job-title",
    ".resume-title",
    ".position",
    "[data-role='candidate-position']"
  ], resumeRoot);
  const fromSelectorsCompany = firstMatchText([
    ".company-name",
    ".resume-company",
    "[data-role='candidate-company']"
  ], resumeRoot);
  let currentCompany = fromSelectorsCompany;
  let currentTitle = fromSelectorsTitle;
  const timeRe = /\d{4}[.\-/]\d{1,2}\s*[-~至]+\s*(?:至今|\d{4}[.\-/]\d{1,2})/;
  const sectionStart = lines.findIndex((l) => /^工作经历/.test(l));
  if (sectionStart >= 0 && (!currentCompany || !currentTitle)) {
    const section = [];
    for (let i = sectionStart + 1; i < Math.min(lines.length, sectionStart + 90); i++) {
      const l = lines[i];
      if (/^(项目经验|教育经历|自我评价|语言能力|证书|技能|最近关注|在线活跃)/.test(l)) break;
      section.push(l);
    }
    for (let i = 0; i < section.length; i++) {
      const line = cleanText(section[i]);
      if (!line || /^(业绩|内容|职责)[:：]?$/.test(line)) continue;
      if (timeRe.test(line)) {
        const beforeTime = cleanText(line.replace(timeRe, " "));
        const m = beforeTime.match(/^(.+?(?:有限公司|股份有限公司|公司|集团|研究院|研究所|大学|学院|中心|工作室|事务所|银行|医院|科技|软件|信息|网络))(?:[\s|｜/]+)(.+)$/);
        if (m) {
          if (!currentCompany) currentCompany = cleanText(m[1]);
          if (!currentTitle) currentTitle = cleanText(m[2]).replace(/^[\s|｜/]+/, "").replace(/[·•｜|].*$/, "");
          break;
        }
        const parts = beforeTime.split(/\s+/).filter(Boolean);
        if (parts.length >= 2) {
          if (!currentCompany) currentCompany = cleanText(parts[0]);
          if (!currentTitle) currentTitle = cleanText(parts[1]).replace(/[·•｜|].*$/, "");
          break;
        }
      }
      if (!currentCompany && /(?:有限公司|股份有限公司|公司|集团|研究院|研究所|大学|学院|中心|工作室|事务所|银行|医院|科技|软件|信息|网络)/.test(line)) {
        currentCompany = line;
        for (let j = i + 1; j < Math.min(section.length, i + 6); j++) {
          const next = cleanText(section[j]);
          if (!next) continue;
          if (timeRe.test(next) || /^(业绩|内容|职责)[:：]?$/.test(next)) continue;
          if (/^(项目经验|教育经历|自我评价|语言能力|证书|技能)/.test(next)) break;
          if (!currentTitle && next.length <= 40) currentTitle = next.replace(/[·•｜|].*$/, "");
          break;
        }
        if (currentCompany && currentTitle) break;
      }
    }
  }
  const idx = lines.findIndex((l) => /^工作经历/.test(l));
  if (idx >= 0 && (!currentCompany || !currentTitle)) {
    const block = lines.slice(idx + 1, idx + 40);
    for (let i = 0; i < block.length; i++) {
      const line = block[i];
      if (/^(项目经验|教育经历|自我评价|语言能力|证书|技能)/.test(line)) break;
      if (!/\d{4}[.\-/]\d{1,2}|\b至今\b/.test(line)) continue;
      const beforeTime = line.replace(/\d{4}[.\-/]\d{1,2}\s*[-~至]+\s*(?:至今|\d{4}[.\-/]\d{1,2})/, "").trim();
      if (!beforeTime) continue;
      const m = beforeTime.match(/^(.+?(?:有限公司|股份有限公司|公司|集团|研究院|研究所|大学|学院|中心|工作室|事务所|银行|医院|科技|软件|信息|网络))(?:[\s|｜/]+)(.+)$/);
      if (m) {
        if (!currentCompany) currentCompany = cleanText(m[1]);
        if (!currentTitle) currentTitle = cleanText(m[2]).replace(/^[\s|｜/]+/, "");
        break;
      }
      if (!currentCompany && /(?:有限公司|股份有限公司|公司|集团|研究院|科技|软件|信息|网络)/.test(beforeTime)) {
        currentCompany = beforeTime;
        const next = cleanText(block[i + 1] || "");
        if (!currentTitle && next && !/\d{4}[.\-/]\d{1,2}/.test(next) && !/(工作内容|项目经验|教育经历)/.test(next) && next.length <= 32) {
          currentTitle = next;
        }
      }
    }
  }
  return fixCompanyTitleOrder(currentCompany, currentTitle);
}

function pickBossSidebarRoot() {
  const direct = document.querySelector(".resume-summary");
  if (direct) return direct;
  const wildcard = document.querySelector("[class*='resume-summary']");
  if (wildcard) return wildcard;
  const dialog = pickBossPopupRoot();
  if (dialog && dialog !== document.body && typeof dialog.querySelector === "function") {
    return dialog.querySelector(".resume-summary,[class*='resume-summary']");
  }
  return null;
}

function collectBossSidebarData() {
  const empty = {
    sourceSite: detectSourceSite(),
    sourceCandidateId: "",
    name: "",
    phone: "",
    email: "",
    currentCompany: "",
    currentTitle: "",
    workExperienceText: "",
    resumeText: "",
    educationSchool: "",
    educationHighest: "",
    workYears: "",
    pageUrl: location.href
  };
  if (!isBossSite() || isBossResumeFrame()) {
    return empty;
  }
  const sidebarRoot = pickBossSidebarRoot();
  const root = sidebarRoot || pickBossPopupRoot() || document.body;
  const rawText = root ? String(root.innerText || "") : "";
  const fullText = cleanText(rawText);
  const resumeText = normalizeResumeText(rawText);
  const lines = splitLines(rawText);
  const profileLine = guessProfileLine(lines);
  const educationSchool = guessSchool(lines, root);
  const educationHighest = guessEducation(lines, profileLine, root);
  const workYears = guessWorkYears(lines, profileLine, root);
  const expectedInfo = guessFromExpectedLine(lines);
  const workInfo = guessCurrentWork(lines, root);
  const workExperienceText = extractWorkExperienceText(lines);
  const currentCompany = workInfo.currentCompany || expectedInfo.currentCompany || "";
  const currentTitle = workInfo.currentTitle || expectedInfo.currentTitle || "";
  const fromNameSelector = firstMatchText([
    ".geek-name",
    ".resume-name",
    ".candidate-name",
    "[data-role='candidate-name']",
    "h1",
    "h2"
  ], document);
  const name = extractRealName(fromNameSelector) || extractNameToken(fromNameSelector) || guessName(lines, root);
  const phone = parsePhone(fullText);
  const email = parseEmail(fullText);
  const id = extractCandidateId(root);
  const fallbackSeed = [detectSourceSite(), name, phone, email, currentCompany, currentTitle, workYears, educationHighest, lines.slice(0, 20).join("|")].join("|");
  return {
    sourceSite: detectSourceSite(),
    sourceCandidateId: id || `sidebar_${simpleHash(fallbackSeed)}`,
    name,
    phone,
    email,
    currentCompany,
    currentTitle,
    workExperienceText,
    resumeText,
    educationSchool,
    educationHighest,
    workYears,
    pageUrl: location.href
  };
}

function hasCandidateSignals(candidate) {
  if (!candidate || typeof candidate !== "object") return false;
  return Boolean(
    cleanText(candidate.name) ||
    cleanText(candidate.currentCompany) ||
    cleanText(candidate.currentTitle) ||
    cleanText(candidate.workExperienceText) ||
    normalizeResumeText(candidate.resumeText) ||
    cleanText(candidate.educationSchool) ||
    cleanText(candidate.workYears) ||
    cleanText(candidate.educationHighest) ||
    cleanText(candidate.phone) ||
    cleanText(candidate.email)
  );
}

function isValidCandidate(candidate) {
  if (!candidate || typeof candidate !== "object") return false;
  const name = cleanText(candidate.name);
  if (!name || isBossNoiseName(name) || !isStrictCandidateName(name)) return false;
  if (/(工作经历|项目经验|教育经历|最近关注|同事沟通|工作概览|简历详情)/.test(name)) return false;
  if (candidate.sourceCandidateId && !isValidSourceCandidateId(candidate.sourceCandidateId)) return false;
  if (!(cleanText(candidate.currentCompany) || cleanText(candidate.currentTitle) || cleanText(candidate.workExperienceText) || cleanText(candidate.educationSchool) || cleanText(candidate.workYears) || cleanText(candidate.educationHighest) || cleanText(candidate.phone) || cleanText(candidate.email))) {
    return false;
  }
  return true;
}

function collectCandidateFromRoot(resumeRoot, pageUrl) {
  const root = resumeRoot && typeof resumeRoot.querySelector === "function" ? resumeRoot : pickResumeRoot();
  const rawText = root ? String(root.innerText || "") : (document.body ? document.body.innerText : "");
  const fullText = cleanText(rawText);
  const resumeText = normalizeResumeText(rawText);
  const lines = splitLines(rawText);
  const orderedBoss = parseBossByOrderedSections(lines);
  const profileLine = guessProfileLine(lines);
  const name = cleanText((orderedBoss && orderedBoss.name) || guessName(lines, root));
  const educationSchool = cleanText((orderedBoss && orderedBoss.educationSchool) || guessSchool(lines, root));
  const educationHighest = cleanText((orderedBoss && orderedBoss.educationHighest) || guessEducation(lines, profileLine, root));
  const workYears = cleanText((orderedBoss && orderedBoss.workYears) || guessWorkYears(lines, profileLine, root));
  const expectedInfo = guessFromExpectedLine(lines);
  const workInfo = guessCurrentWork(lines, root);
  const currentCompany = cleanText((orderedBoss && orderedBoss.currentCompany) || workInfo.currentCompany || expectedInfo.currentCompany || "");
  const currentTitle = cleanText((orderedBoss && orderedBoss.currentTitle) || workInfo.currentTitle || expectedInfo.currentTitle || "");
  const workExperienceText = String((orderedBoss && orderedBoss.workExperienceText) || extractWorkExperienceText(lines) || extractWorkExperienceTextFromRawText(rawText) || "").trim();
  const phone = parsePhone(fullText);
  const email = parseEmail(fullText);
  const id = extractCandidateId(root);
  const fallbackSeed = [detectSourceSite(), name, phone, email, currentCompany, currentTitle, workYears, educationHighest, workExperienceText.slice(0, 1000), lines.slice(0, 20).join("|")].join("|");
  const sourceCandidateId = id || `fallback_${simpleHash(fallbackSeed)}`;
  return {
    sourceSite: detectSourceSite(),
    sourceCandidateId,
    name,
    phone,
    email,
    currentCompany,
    currentTitle,
    workExperienceText,
    resumeText,
    educationSchool,
    educationHighest,
    workYears,
    pageUrl: pageUrl || location.href
  };
}

function collectResumeData() {
  const candidates = [];
  candidates.push(collectCandidateFromRoot(pickResumeRoot(), location.href));

  if (isBossSite() && !isBossResumeFrame()) {
    const frame = pickBossResumeIframe();
    if (frame) {
      try {
        const doc = frame.contentDocument;
        const frameRoot = doc && doc.body ? doc.body : null;
        if (frameRoot) {
          candidates.push(collectCandidateFromRoot(frameRoot, cleanText(frame.src || "")));
        }
      } catch (_) {
      }
    }
  }

  if (document.body) {
    candidates.push(collectCandidateFromRoot(document.body, location.href));
  }

  let best = null;
  let bestScore = -1;
  for (const candidate of candidates) {
    if (!hasCandidateSignals(candidate)) continue;
    const score =
      (isStrictCandidateName(candidate.name) ? 8 : -8) +
      (cleanText(candidate.currentCompany) ? 2 : 0) +
      (cleanText(candidate.currentTitle) ? 2 : 0) +
      (cleanText(candidate.workExperienceText) ? 3 : 0) +
      (cleanText(candidate.educationSchool) ? 2 : 0) +
      (cleanText(candidate.workYears) ? 1 : 0);
    if (score > bestScore) {
      bestScore = score;
      best = candidate;
    }
  }
  return best || collectCandidateFromRoot(pickResumeRoot(), location.href);
}

function isVisibleBossAction(el) {
  if (!el || typeof el.getBoundingClientRect !== "function") return false;
  const rect = el.getBoundingClientRect();
  if (rect.width < 20 || rect.height < 16) return false;
  if (rect.bottom <= 0 || rect.top >= window.innerHeight) return false;
  const style = window.getComputedStyle(el);
  if (!style) return true;
  return style.display !== "none" && style.visibility !== "hidden" && style.opacity !== "0";
}

function pickBossActionButton(root, regex) {
  const scope = root && typeof root.querySelectorAll === "function" ? root : document;
  const nodes = scope.querySelectorAll("button,a,span,div");
  for (const node of nodes) {
    const text = cleanText(node.innerText || node.textContent || "");
    if (!text || !regex.test(text)) continue;
    if (!isVisibleBossAction(node)) continue;
    return node;
  }
  return null;
}

function triggerBossClick(node) {
  if (!node) return false;
  try {
    node.click();
    return true;
  } catch (_) {}
  try {
    node.dispatchEvent(new MouseEvent("click", { bubbles: true, cancelable: true, view: window }));
    return true;
  } catch (_) {}
  return false;
}

function pickBossRecommendCardRoot(button) {
  let node = button;
  while (node && node !== document.body) {
    const text = cleanText(node.innerText || "");
    const rect = typeof node.getBoundingClientRect === "function" ? node.getBoundingClientRect() : null;
    if (text && rect && rect.width >= 280 && rect.height >= 80 && rect.height <= 520 && text.length <= 1600) {
      const hasProfile = /(\d{1,2}\s*岁|\d+\s*\+?\s*年|本科|硕士|大专|中专|博士|应届)/.test(text);
      const hasAction = /打招呼|立即沟通|继续沟通/.test(text);
      if (hasProfile && hasAction) return node;
    }
    node = node.parentElement;
  }
  return button && typeof button.closest === "function" ? button.closest("li,article,section,div") : null;
}

function extractBossRecommendCurrentJobText() {
  const nodes = document.querySelectorAll("div,span,a,h1,h2,h3");
  const candidates = [];
  const maxScan = Math.min(nodes.length, 1800);
  for (let i = 0; i < maxScan; i++) {
    const node = nodes[i];
    if (!isVisibleBossAction(node)) continue;
    const rect = node.getBoundingClientRect();
    if (rect.top > 220) continue;
    const text = cleanText(node.innerText || node.textContent || "");
    if (!text || text.length < 2 || text.length > 120) continue;
    if (/^(推荐牛人|筛选|在线|活跃|打招呼|立即沟通|继续沟通|收藏|不合适|举报|转发)$/u.test(text)) continue;
    let score = 0;
    if (rect.top < 140) score += 3;
    if (rect.left >= window.innerWidth * 0.45) score += 4;
    if (/经理|总监|工程师|专员|助理|顾问|hr|人事|销售|产品|运营|财务|会计|招聘|猎头|设计|前端|后端|java|python/i.test(text)) score += 5;
    if (/\d{1,2}\s*-\s*\d{1,2}\s*[kK]/.test(text)) score += 2;
    if (/北京|上海|深圳|广州|杭州|苏州|成都|武汉|西安|长沙|天津|南京|重庆/.test(text)) score += 1;
    if (score <= 0) continue;
    candidates.push({ text, score });
  }
  candidates.sort((a, b) => b.score - a.score || a.text.length - b.text.length);
  return candidates[0] ? candidates[0].text : "";
}

function collectBossRecommendContext() {
  const cards = collectBossRecommendCards();
  const hasDetailPopup = hasBossRecommendDetailPopup();
  const pageText = cleanText((document.body && document.body.innerText) || "");
  const state = hasDetailPopup
    ? "Boss推荐牛人详情页"
    : ((/推荐牛人/.test(pageText) || /recommend/i.test(`${location.pathname}${location.search}`))
      ? "Boss推荐牛人页"
      : "other");
  return {
    page_type: "recommend",
    page_state: state,
    current_job_title: extractBossRecommendCurrentJobText(),
    page_text: pageText.slice(0, 1200),
    page_url: location.href,
    card_count: cards.length,
    has_detail_popup: hasDetailPopup,
    has_greet_action: cards.length > 0 || hasBossRecommendGreetAction(),
    frame_scope: window.top === window ? "top" : "iframe"
  };
}

function collectBossRecommendCards() {
  if (!isBossSite()) return [];
  const buttons = Array.from(document.querySelectorAll("button,a,span,div")).filter((node) => {
    const text = cleanText(node.innerText || node.textContent || "");
    return text && /打招呼|立即沟通|继续沟通/.test(text) && isVisibleBossAction(node);
  });
  const cards = [];
  const seen = new Set();
  for (const btn of buttons) {
    const root = pickBossRecommendCardRoot(btn);
    if (!root || seen.has(root)) continue;
    seen.add(root);
    const rawText = cleanText(root.innerText || "");
    if (!rawText || rawText.length < 12) continue;
    const lines = splitLines(root.innerText || "").slice(0, 40);
    const name = guessName(lines, root) || extractRealName(lines[0] || "") || extractNameToken(rawText) || "";
    const workYears = normalizeWorkYearsText(rawText) || ((rawText.match(/(\d+\s*\+?\s*年)/) || [])[1] || "");
    const education = extractEducationKeyword(rawText) || "";
    const salary = cleanText((rawText.match(/(\d{1,2}\s*-\s*\d{1,2}\s*[kK])/i) || [])[1] || "");
    const age = cleanText((rawText.match(/(\d{1,2}\s*岁)/) || [])[1] || "");
    const city = cleanText((rawText.match(/(北京|上海|深圳|广州|杭州|苏州|成都|武汉|西安|长沙|天津|南京|重庆)/) || [])[1] || "");
    let currentTitle = "";
    let currentCompany = "";
    for (const line of lines) {
      if (!currentTitle && /经理|总监|工程师|专员|助理|顾问|hr|人事|销售|产品|运营|财务|会计|招聘|猎头|设计|前端|后端|java|python/i.test(line)) {
        currentTitle = line;
      }
      if (!currentCompany && /公司|集团|科技|信息|网络|传媒|控股|有限|银行|医院|学校/.test(line)) {
        currentCompany = line;
      }
      if (currentTitle && currentCompany) break;
    }
    const tags = lines.filter((line) => {
      if (!line || line === name) return false;
      if (line.length > 16) return false;
      if (/打招呼|立即沟通|继续沟通|不合适|举报|转发/.test(line)) return false;
      return true;
    }).slice(0, 6);
    const candidateKey = extractCandidateId(root) || root.getAttribute("data-geek-id") || root.getAttribute("data-resume-id") || `boss_${simpleHash([name, currentTitle, currentCompany, salary, rawText.slice(0, 160)].join("|"))}`;
    cards.push({
      candidate_key: cleanText(candidateKey),
      sourceCandidateId: cleanText(candidateKey),
      name,
      currentTitle: cleanText(currentTitle),
      currentCompany: cleanText(currentCompany),
      workYears: cleanText(workYears),
      education: cleanText(education),
      salary,
      age,
      city,
      tags,
      raw_text: rawText.slice(0, 1200),
      greet_available: true,
      _root: root,
      _button: btn
    });
  }
  cards.sort((a, b) => {
    const ra = a._root && typeof a._root.getBoundingClientRect === "function" ? a._root.getBoundingClientRect() : { top: 0, left: 0 };
    const rb = b._root && typeof b._root.getBoundingClientRect === "function" ? b._root.getBoundingClientRect() : { top: 0, left: 0 };
    if (ra.top !== rb.top) return ra.top - rb.top;
    return ra.left - rb.left;
  });
  return cards;
}

function countBossRecommendCardsSafe() {
  try {
    return collectBossRecommendCards().length;
  } catch (_) {
    return 0;
  }
}

function countBossMessageItemsSafe() {
  try {
    return collectBossMessageItems().length;
  } catch (_) {
    return 0;
  }
}

function hasBossRecommendGreetAction() {
  try {
    return Boolean(pickBossActionButton(document.body, /打招呼|立即沟通|继续沟通|发送招呼/));
  } catch (_) {
    return false;
  }
}

function hasBossRecommendDetailPopup() {
  const root = pickBossPopupRoot();
  if (!root) return false;
  const text = cleanText(root.innerText || "");
  if (!text || text.length < 80) return false;
  if (!/(工作经历|教育经历|项目经验|期望职位)/.test(text)) return false;
  if (/沟通|聊天|消息记录|发送消息/.test(text)) return false;
  return true;
}

function serializeBossCard(card) {
  const plain = {};
  const source = card && typeof card === "object" ? card : {};
  for (const [key, value] of Object.entries(source)) {
    if (key.startsWith("_")) continue;
    plain[key] = value;
  }
  return plain;
}

function waitMs(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function runtimeMessage(message) {
  return new Promise((resolve, reject) => {
    try {
      chrome.runtime.sendMessage(message, (response) => {
        if (chrome.runtime.lastError) {
          reject(new Error(chrome.runtime.lastError.message));
          return;
        }
        resolve(response || null);
      });
    } catch (e) {
      reject(e);
    }
  });
}

let BOSS_RUNNER_CONFIG_CACHE = null;
let BOSS_RUNNER_CONFIG_TS = 0;
let BOSS_RUNNER_BUSY = false;
let BOSS_RUNNER_LAST_WARN = 0;
let BOSS_RUNNER_LAST_STATE_KEY = "";
let BOSS_RUNNER_LAST_STATE_TS = 0;
let BOSS_RUNNER_ACTIVE_TASK_ID = 0;

function buildBossRunnerStateKey(status, detail) {
  const payload = detail && typeof detail === "object" ? detail : {};
  return `${cleanText(status)}|${Object.keys(payload).sort().map((key) => `${key}:${String(payload[key])}`).join("|")}`;
}

function reportBossRunnerState(status, detail = {}, throttleMs = 15000) {
  const payload = detail && typeof detail === "object" ? detail : {};
  const key = buildBossRunnerStateKey(status, payload);
  const now = Date.now();
  try {
    window.__BOSS_RUNNER_LAST_STATE = {
      status: cleanText(status) || "unknown",
      detail: payload,
      url: location.href,
      title: cleanText(document.title || ""),
      ts: now
    };
  } catch (_) {}
  if (key === BOSS_RUNNER_LAST_STATE_KEY && now - BOSS_RUNNER_LAST_STATE_TS < throttleMs) return;
  BOSS_RUNNER_LAST_STATE_KEY = key;
  BOSS_RUNNER_LAST_STATE_TS = now;
  try {
    console.info("[BossRunner]", cleanText(status) || "unknown", payload);
  } catch (_) {}
  try {
    agentDebugLogContent(`run_${now}`, "BossRunner", "content.js:bossRunner", cleanText(status) || "unknown", payload);
  } catch (_) {}
}

function buildBossRunnerHeartbeatPayload(task, runnerStatus, detail = {}, context = {}) {
  const taskInfo = task && typeof task === "object" ? task : {};
  const payload = detail && typeof detail === "object" ? { ...detail } : {};
  const pageType = cleanText(context.page_type || payload.page_type || "");
  const currentJobTitle = cleanText(context.current_job_title || payload.current_job_title || "");
  const expectedJobTitle = cleanText(context.expected_job_title || payload.expected_job_title || taskInfo.target_job_title || "");
  const pageState = cleanText(context.page_state || payload.page_state || "");
  const pageUrl = String(context.page_url || payload.page_url || location.href || "");
  const pageTitle = cleanText(context.page_title || payload.page_title || document.title || "");
  const summaryText = cleanText(
    context.summary_text
    || payload.summary_text
    || payload.wait_reason
    || payload.message
    || payload.error
    || ""
  );
  return {
    runner_status: cleanText(runnerStatus || ""),
    summary_text: summaryText,
    page_type: pageType,
    page_url: pageUrl,
    page_title: pageTitle,
    page_state: pageState,
    current_job_title: currentJobTitle,
    expected_job_title: expectedJobTitle,
    wait_reason: cleanText(payload.wait_reason || ""),
    message: cleanText(payload.message || ""),
    error: cleanText(payload.error || ""),
    page_ready: typeof payload.page_ready === "boolean" ? payload.page_ready : undefined,
    runnable: typeof payload.runnable === "boolean" ? payload.runnable : undefined,
    match_ok: typeof payload.match_ok === "boolean" ? payload.match_ok : undefined,
    match_score: Number(payload.match_score || 0) || 0,
    card_count: Number(payload.card_count || 0) || 0,
    conversation_count: Number(payload.conversation_count || 0) || 0,
    detail: {
      ...payload,
      page_type: pageType,
      page_state: pageState,
      current_job_title: currentJobTitle,
      expected_job_title: expectedJobTitle
    }
  };
}

async function sendBossRunnerHeartbeat(task, runnerStatus, detail = {}, context = {}) {
  const taskId = Number(task?.id || BOSS_RUNNER_ACTIVE_TASK_ID || 0) || 0;
  if (!taskId) return null;
  BOSS_RUNNER_ACTIVE_TASK_ID = taskId;
  const payload = buildBossRunnerHeartbeatPayload({ ...(task || {}), id: taskId }, runnerStatus, detail, context);
  return bossFetchJson(`/automation/demo/boss/tasks/${taskId}/runner-heartbeat`, payload, "POST");
}

function buildBossMismatchPromptKey(task, syncRes) {
  const expected = cleanText(syncRes?.expected_job_title || task?.target_job_title || "");
  const current = cleanText(syncRes?.current_job_title || "");
  return `boss_force_match:${Number(task?.id || 0) || 0}:${expected}:${current}`;
}

async function getBossRunnerConfig(force = false) {
  const now = Date.now();
  if (!force && BOSS_RUNNER_CONFIG_CACHE && now - BOSS_RUNNER_CONFIG_TS < 6000) {
    return BOSS_RUNNER_CONFIG_CACHE;
  }
  const res = await runtimeMessage({ type: "getBossRunnerConfig" }).catch(() => null);
  const next = {
    ok: Boolean(res && res.ok),
    apiBase: cleanText(res?.apiBase || "http://127.0.0.1:8000"),
    token: cleanText(res?.token || ""),
    bossAutomationEnabled: res?.bossAutomationEnabled !== false
  };
  BOSS_RUNNER_CONFIG_CACHE = next;
  BOSS_RUNNER_CONFIG_TS = now;
  return next;
}

async function bossFetchJson(path, payload = null, method = "POST") {
  let config = await getBossRunnerConfig();
  if (config?.bossAutomationEnabled && (!config?.apiBase || !config?.token)) {
    config = await getBossRunnerConfig(true);
  }
  if (!config?.bossAutomationEnabled) {
    reportBossRunnerState("boss_runner_disabled", { path });
    return { ok: false, disabled: true, error: "Boss执行器已关闭" };
  }
  if (!config?.apiBase || !config?.token) {
    reportBossRunnerState("boss_runner_auth_missing", {
      path,
      has_api_base: Boolean(config?.apiBase),
      has_token: Boolean(config?.token)
    });
    return { ok: false, disabled: true, error: "未获取到系统地址或登录Token" };
  }
  const target = `${config.apiBase}${path}`;
  let resp;
  try {
    resp = await fetch(target, {
      method,
      headers: {
        "Authorization": `Bearer ${config.token}`,
        "Content-Type": "application/json"
      },
      body: method === "GET" ? undefined : JSON.stringify(payload || {})
    });
  } catch (e) {
    reportBossRunnerState("boss_runner_request_failed", {
      path,
      error: String(e?.message || e || "")
    });
    return { ok: false, error: String(e?.message || e || "") };
  }
  const raw = await resp.text();
  let data = {};
  try {
    data = raw ? JSON.parse(raw) : {};
  } catch (_) {
    reportBossRunnerState("boss_runner_bad_response", {
      path,
      status: resp?.status || 0
    });
    data = { detail: raw || "" };
  }
  if (!resp.ok) {
    reportBossRunnerState("boss_runner_api_error", {
      path,
      status: resp?.status || 0,
      error: cleanText(data?.detail || "")
    });
    return { ok: false, error: data?.detail || `HTTP ${resp.status}` };
  }
  return data || { ok: true };
}

function markBossCardState(card, state) {
  const root = card && card._root;
  if (!root) return;
  root.setAttribute("data-finance-boss-state", state || "");
  if (state === "done") root.style.outline = "1px solid #16a34a";
  if (state === "skip") root.style.outline = "1px solid #94a3b8";
  if (state === "processing") root.style.outline = "1px solid #2563eb";
}

async function openBossRecommendCard(card) {
  const root = card && card._root;
  if (!root) return false;
  const targets = [root];
  const anchor = root.querySelector("a");
  if (anchor && !targets.includes(anchor)) targets.push(anchor);
  for (const target of targets) {
    try {
      target.scrollIntoView({ block: "center", inline: "nearest" });
    } catch (_) {}
    if (!triggerBossClick(target)) continue;
    for (let i = 0; i < 8; i++) {
      await waitMs(180);
      if (hasBossRecommendDetailPopup()) return true;
    }
  }
  return hasBossRecommendDetailPopup();
}

async function collectBossDetailCandidate() {
  for (let i = 0; i < 6; i++) {
    try {
      const candidate = collectResumeData();
      if (candidate && (cleanText(candidate.resumeText) || cleanText(candidate.workExperienceText) || cleanText(candidate.currentCompany) || cleanText(candidate.currentTitle))) {
        return candidate;
      }
    } catch (_) {}
    await waitMs(420);
  }
  try {
    return collectResumeData();
  } catch (_) {
    return null;
  }
}

function readBossPrimaryActionText(card) {
  const roots = [
    pickBossPopupRoot(),
    pickResumeRoot(),
    card && card._root,
    document.body
  ];
  for (const root of roots) {
    if (!root) continue;
    const btn = pickBossActionButton(root, /打招呼|立即沟通|继续沟通|发送招呼|发消息|已沟通|沟通中/);
    const text = cleanText(btn?.innerText || btn?.textContent || "");
    if (text) return text;
  }
  return "";
}

async function clickBossGreetButton(card) {
  const popupRoot = pickBossPopupRoot() || pickResumeRoot() || document.body;
  let btn = pickBossActionButton(popupRoot, /打招呼|立即沟通|继续沟通|发送招呼/);
  if (!btn && card && card._root) {
    btn = pickBossActionButton(card._root, /打招呼|立即沟通|继续沟通|发送招呼/);
  }
  if (!btn) return { ok: false, error: "未找到打招呼按钮" };
  const beforeText = cleanText(btn.innerText || btn.textContent || "");
  if (/继续沟通|已沟通|发消息|沟通中/.test(beforeText)) {
    return { ok: true, already: true };
  }
  try {
    btn.scrollIntoView({ block: "center", inline: "nearest" });
  } catch (_) {}
  if (!triggerBossClick(btn)) return { ok: false, error: "点击打招呼按钮失败" };
  await waitMs(520);
  for (let i = 0; i < 3; i++) {
    const confirm = pickBossActionButton(document.body, /发送招呼|立即发送|确认发送|确定/);
    if (!confirm) break;
    if (!triggerBossClick(confirm)) return { ok: false, error: "点击发送确认失败" };
    await waitMs(420);
  }
  for (let i = 0; i < 8; i++) {
    const afterText = readBossPrimaryActionText(card);
    if (/继续沟通|已沟通|发消息|沟通中/.test(afterText)) return { ok: true };
    if (beforeText && afterText && afterText !== beforeText && !/打招呼|发送招呼/.test(afterText)) {
      return { ok: true };
    }
    await waitMs(220);
  }
  return { ok: false, error: "点击后未检测到打招呼成功状态" };
}

function pickBossRecommendCloseButton() {
  const popupRoot = pickBossPopupRoot();
  const popupRect = popupRoot?.getBoundingClientRect?.() || null;
  const nodes = Array.from(document.querySelectorAll("button, [role='button'], a, span, div"));
  let best = null;
  let bestScore = -1;
  for (const node of nodes) {
    if (!isVisibleBossAction(node)) continue;
    const text = cleanText(node.innerText || node.textContent || "");
    const aria = cleanText(node.getAttribute?.("aria-label") || "");
    const title = cleanText(node.getAttribute?.("title") || "");
    const cls = cleanText(typeof node.className === "string" ? node.className : "");
    const label = `${text} ${aria} ${title} ${cls}`.toLowerCase();
    let score = 0;
    if (/关闭|close|收起|返回/.test(label)) score += 8;
    if (/^(×|x)$/i.test(text)) score += 7;
    if (/close|btn-close|icon-close/.test(label)) score += 5;
    const rect = node.getBoundingClientRect();
    if (rect.top < 140) score += 2;
    if (rect.left > window.innerWidth * 0.55) score += 4;
    if (popupRect && rect.left >= popupRect.left - 24 && rect.right <= popupRect.right + 24 && rect.top >= popupRect.top - 24 && rect.top <= popupRect.top + 120) {
      score += 4;
    }
    if (score > bestScore) {
      best = node;
      bestScore = score;
    }
  }
  return bestScore > 0 ? best : null;
}

async function closeBossRecommendDetail() {
  if (!hasBossRecommendDetailPopup()) return true;
  const btn = pickBossRecommendCloseButton();
  if (btn) {
    try {
      btn.click();
    } catch (_) {
      try {
        btn.dispatchEvent(new MouseEvent("click", { bubbles: true, cancelable: true, view: window }));
      } catch (_) {}
    }
    await waitMs(520);
    if (!hasBossRecommendDetailPopup()) return true;
  }
  try {
    document.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape", code: "Escape", keyCode: 27, which: 27, bubbles: true }));
    document.dispatchEvent(new KeyboardEvent("keyup", { key: "Escape", code: "Escape", keyCode: 27, which: 27, bubbles: true }));
  } catch (_) {}
  await waitMs(360);
  return !hasBossRecommendDetailPopup();
}

function detectBossAutomationPage() {
  const path = String(location.pathname || "").toLowerCase();
  const title = cleanText(document.title || "").toLowerCase();
  const text = cleanText(document.body?.innerText || "").slice(0, 1800).toLowerCase();
  const recommendCardCount = countBossRecommendCardsSafe();
  const messageItemCount = countBossMessageItemsSafe();
  const hasRecommendDetail = hasBossRecommendDetailPopup();
  const hasGreetAction = hasBossRecommendGreetAction();
  const hasMessageInput = Boolean(pickBossMessageInput());
  const hasSendButton = Boolean(pickBossMessageSendButton());
  const isChatRecommendPath = /\/chat\/recommend|\/web\/chat\/recommend/.test(path);
  const recommendLikely = isBossResumeFrame() || /\/recommend|\/web\/frame\/recommend|\/geek\/job|\/job\/detail/.test(path) || /推荐牛人|牛人/.test(title) || /推荐牛人|牛人|打招呼|立即沟通|继续沟通|人选/.test(text);
  const messageLikely = !isChatRecommendPath && (/\/chat|\/message|\/geek\/chat/.test(path) || /沟通|聊天|消息/.test(title) || /沟通|聊天|消息|发送/.test(text));
  const recommendScore =
    (isBossResumeFrame() ? 8 : 0) +
    (isChatRecommendPath ? 8 : 0) +
    ((/\/recommend|\/web\/frame\/recommend/.test(path) || /推荐牛人/.test(title)) ? 6 : 0) +
    (recommendLikely ? 2 : 0) +
    Math.min(recommendCardCount, 5) * 3 +
    (hasRecommendDetail ? 8 : 0) +
    (hasGreetAction ? 6 : 0);
  const messageScore =
    ((/\/chat|\/message|\/geek\/chat/.test(path) || /沟通|聊天|消息/.test(title)) ? 6 : 0) +
    (messageLikely ? 2 : 0) +
    Math.min(messageItemCount, 5) * 3 +
    (hasMessageInput ? 4 : 0) +
    (hasSendButton ? 3 : 0);
  let pageType = "";
  let reason = "no_signal";
  if (recommendScore > messageScore && (recommendScore >= 4 || recommendLikely)) {
    pageType = "recommend";
    reason = recommendScore >= 4 ? "recommend_score" : "recommend_hint";
  } else if (messageScore > recommendScore && (messageScore >= 4 || messageLikely)) {
    pageType = "messages";
    reason = messageScore >= 4 ? "message_score" : "message_hint";
  } else if (recommendScore === messageScore && recommendScore >= 4) {
    pageType = hasRecommendDetail || hasGreetAction || recommendCardCount >= messageItemCount ? "recommend" : "messages";
    reason = "score_tie";
  } else if (recommendLikely && !messageLikely) {
    pageType = "recommend";
    reason = "recommend_hint_only";
  } else if (messageLikely && !recommendLikely) {
    pageType = "messages";
    reason = "message_hint_only";
  } else if (recommendLikely && messageLikely) {
    pageType = recommendScore >= messageScore ? "recommend" : "messages";
    reason = "dual_hint";
  }
  return {
    pageType,
    reason,
    path,
    title,
    recommendLikely,
    messageLikely,
    recommendScore,
    messageScore,
    recommendCardCount,
    messageItemCount,
    hasRecommendDetail,
    hasGreetAction,
    hasMessageInput,
    hasSendButton
  };
}

function detectBossAutomationPageType() {
  return detectBossAutomationPage().pageType;
}

function isVisibleBossNode(node) {
  if (!node || typeof node.getBoundingClientRect !== "function") return false;
  const rect = node.getBoundingClientRect();
  if (rect.width < 40 || rect.height < 24) return false;
  if (rect.bottom <= 0 || rect.right <= 0 || rect.top >= window.innerHeight || rect.left >= window.innerWidth) return false;
  try {
    const style = window.getComputedStyle(node);
    if (style.display === "none" || style.visibility === "hidden" || Number(style.opacity || 1) <= 0) return false;
  } catch (_) {}
  return true;
}

function pickBossMessageName(lines) {
  for (const line of lines) {
    const candidate = stripBossUiPrefix(line);
    if (isStrictCandidateName(candidate)) return candidate;
  }
  for (const line of lines) {
    const candidate = stripBossUiPrefix(line);
    if (/^[\u4e00-\u9fa5A-Za-z·]{2,12}$/u.test(candidate) && !isBossNoiseName(candidate)) return candidate;
  }
  return "";
}

function collectBossMessageItems() {
  const nodes = Array.from(document.querySelectorAll("li, a, [role='listitem'], div"));
  const items = [];
  const seen = new Set();
  for (const node of nodes) {
    if (!isVisibleBossNode(node)) continue;
    const rect = node.getBoundingClientRect();
    if (rect.left > window.innerWidth * 0.5 || rect.width < 120 || rect.height < 40 || rect.height > 180) continue;
    const text = cleanText(node.innerText || node.textContent || "");
    if (!text || text.length > 180) continue;
    const lines = splitLines(node.innerText || node.textContent || "").slice(0, 6);
    const name = pickBossMessageName(lines);
    if (!name) continue;
    const sourceCandidateId = cleanText(node.getAttribute("data-id") || node.dataset?.id || node.dataset?.geekId || node.dataset?.candidateId || "");
    const preview = cleanText(lines.filter((line) => cleanText(line) !== name).join(" "));
    const key = `${sourceCandidateId || ""}|${name}|${preview}`;
    if (seen.has(key)) continue;
    seen.add(key);
    const unread = /未读|新消息|\d+$/.test(text);
    items.push({
      source_candidate_id: sourceCandidateId,
      candidate_name: name,
      candidate_title: cleanText(lines[1] || ""),
      candidate_company: cleanText(lines[2] || ""),
      last_message_text: preview,
      unread,
      _root: node
    });
  }
  items.sort((a, b) => {
    const ra = a._root?.getBoundingClientRect?.() || { top: 0, left: 0 };
    const rb = b._root?.getBoundingClientRect?.() || { top: 0, left: 0 };
    if (ra.top !== rb.top) return ra.top - rb.top;
    return ra.left - rb.left;
  });
  return items;
}

function collectBossMessageContext() {
  const items = collectBossMessageItems();
  return {
    page_type: "messages",
    page_url: location.href,
    page_state: document.title || "",
    page_text: cleanText(document.body?.innerText || "").slice(0, 1200),
    has_message_input: Boolean(pickBossMessageInput()),
    has_send_button: Boolean(pickBossMessageSendButton()),
    conversation_count: items.length,
    items: items.map((item) => ({
      source_candidate_id: item.source_candidate_id,
      candidate_name: item.candidate_name,
      candidate_title: item.candidate_title,
      candidate_company: item.candidate_company,
      last_message_text: item.last_message_text,
      unread: item.unread
    }))
  };
}

async function openBossMessageConversation(target) {
  const items = collectBossMessageItems();
  const sourceId = cleanText(target?.source_candidate_id || "");
  const name = cleanText(target?.candidate_name || "");
  const matched = items.find((item) => {
    if (sourceId && cleanText(item.source_candidate_id) === sourceId) return true;
    if (name && cleanText(item.candidate_name) === name) return true;
    return false;
  });
  if (!matched?._root) return { ok: false, error: "未找到会话入口" };
  try {
    matched._root.scrollIntoView({ block: "center", inline: "nearest" });
  } catch (_) {}
  try {
    matched._root.click();
  } catch (_) {
    try {
      matched._root.dispatchEvent(new MouseEvent("click", { bubbles: true, cancelable: true, view: window }));
    } catch (e) {
      return { ok: false, error: String(e?.message || e || "") };
    }
  }
  await waitMs(1000);
  return { ok: true, item: matched };
}

function pickBossMessageInput() {
  const nodes = Array.from(document.querySelectorAll("textarea, [contenteditable='true'], input[type='text']"));
  const candidates = nodes.filter((node) => {
    if (!isVisibleBossNode(node)) return false;
    if (node.readOnly || node.disabled) return false;
    const rect = node.getBoundingClientRect();
    return rect.top > window.innerHeight * 0.45 && rect.left > window.innerWidth * 0.3;
  });
  candidates.sort((a, b) => {
    const ra = a.getBoundingClientRect();
    const rb = b.getBoundingClientRect();
    return rb.top - ra.top;
  });
  return candidates[0] || null;
}

function fillBossMessageInput(node, text) {
  if (!node) return false;
  const value = String(text || "").trim();
  if (!value) return false;
  try { node.focus(); } catch (_) {}
  const tag = String(node.tagName || "").toLowerCase();
  if (tag === "textarea" || tag === "input") {
    try {
      node.value = value;
      node.dispatchEvent(new Event("input", { bubbles: true }));
      node.dispatchEvent(new Event("change", { bubbles: true }));
      return true;
    } catch (_) {
      return false;
    }
  }
  try {
    node.textContent = "";
    document.execCommand("insertText", false, value);
  } catch (_) {
    try {
      node.textContent = value;
    } catch (_) {
      return false;
    }
  }
  try {
    node.dispatchEvent(new InputEvent("input", { bubbles: true, data: value, inputType: "insertText" }));
  } catch (_) {
    try { node.dispatchEvent(new Event("input", { bubbles: true })); } catch (_) {}
  }
  return true;
}

function pickBossMessageSendButton() {
  const buttons = Array.from(document.querySelectorAll("button, [role='button'], a"));
  return buttons.find((node) => {
    if (!isVisibleBossNode(node)) return false;
    const text = cleanText(node.textContent || "");
    if (!/^(发送|发出|立即发送|send)$/i.test(text)) return false;
    const rect = node.getBoundingClientRect();
    return rect.top > window.innerHeight * 0.45 && rect.left > window.innerWidth * 0.3;
  }) || null;
}

async function clickBossMessageSendButton() {
  const btn = pickBossMessageSendButton();
  if (!btn) return { ok: false, error: "未找到发送按钮" };
  try {
    btn.click();
  } catch (_) {
    try {
      btn.dispatchEvent(new MouseEvent("click", { bubbles: true, cancelable: true, view: window }));
    } catch (e) {
      return { ok: false, error: String(e?.message || e || "") };
    }
  }
  await waitMs(520);
  return { ok: true };
}

function collectBossConversationTranscript() {
  const nodes = Array.from(document.querySelectorAll("div, p, li"));
  const items = [];
  const seen = new Set();
  for (const node of nodes) {
    if (!isVisibleBossNode(node)) continue;
    const rect = node.getBoundingClientRect();
    if (rect.left < window.innerWidth * 0.35 || rect.top < 80 || rect.bottom > window.innerHeight - 120) continue;
    const text = cleanText(node.innerText || node.textContent || "");
    if (!text || text.length > 260) continue;
    if (/发送|立即沟通|打招呼|在线|离线|刚刚活跃/.test(text)) continue;
    const sender = rect.left < window.innerWidth * 0.55 ? "candidate" : "system";
    const key = `${sender}|${text}`;
    if (seen.has(key)) continue;
    seen.add(key);
    items.push({ sender, content: text, top: rect.top, left: rect.left });
  }
  items.sort((a, b) => (a.top === b.top ? a.left - b.left : a.top - b.top));
  return items.map(({ sender, content }) => ({ sender, content })).slice(-20);
}

function isBossTaskDetailAiEnabled(task) {
  const value = task?.mode_config?.detail_ai_enabled;
  if (typeof value === "boolean") return value;
  const text = cleanText(value).toLowerCase();
  return ["1", "true", "yes", "y", "on", "enable", "enabled", "是"].includes(text);
}

async function runBossRecommendAutomation(task) {
  if (hasBossRecommendDetailPopup()) {
    await closeBossRecommendDetail();
    await waitMs(180);
  }
  const context = collectBossRecommendContext();
  const syncRes = await bossFetchJson(`/automation/demo/boss/tasks/${task.id}/page-sync`, context, "POST");
  if (!syncRes?.ok) {
    await sendBossRunnerHeartbeat(task, "recommend_sync_failed", {
      summary_text: syncRes?.error || "推荐页同步失败",
      error: syncRes?.error || "",
      card_count: context.card_count,
      current_job_title: context.current_job_title,
      page_type: context.page_type
    }, context);
    return;
  }
  if (!syncRes.match_ok) {
    await sendBossRunnerHeartbeat(task, "recommend_waiting", {
      summary_text: syncRes.wait_reason || "等待Boss推荐牛人页面",
      wait_reason: syncRes.wait_reason || "",
      page_ready: Boolean(syncRes.page_ready),
      runnable: Boolean(syncRes.runnable),
      match_ok: Boolean(syncRes.match_ok),
      match_score: Number(syncRes.match_score || 0) || 0,
      card_count: context.card_count,
      current_job_title: syncRes.current_job_title || context.current_job_title,
      expected_job_title: syncRes.expected_job_title || task?.target_job_title || "",
      page_type: context.page_type
    }, context);
    if (/等待职位匹配/.test(syncRes.wait_reason || "")) {
      const mismatchKey = buildBossMismatchPromptKey(task, syncRes);
      const forced = sessionStorage.getItem(mismatchKey) === "1";
      if (!forced) {
        const yes = window.confirm(
          `职位名称不匹配，是否继续？\n目标职位：${syncRes.expected_job_title || task?.target_job_title || "未设置"}\n当前页面：${syncRes.current_job_title || "未识别"}`
        );
        if (!yes) {
          await sendBossRunnerHeartbeat(task, "recommend_paused_mismatch", {
            summary_text: "岗位不匹配，任务已暂停",
            wait_reason: syncRes.wait_reason || "",
            match_score: Number(syncRes.match_score || 0) || 0,
            current_job_title: syncRes.current_job_title || context.current_job_title,
            expected_job_title: syncRes.expected_job_title || task?.target_job_title || "",
            page_type: context.page_type
          }, context);
          await bossFetchJson(`/automation/demo/tasks/${task.id}/pause`, null, "POST");
          return;
        }
        sessionStorage.setItem(mismatchKey, "1");
      }
    }
    return;
  }
  await sendBossRunnerHeartbeat(task, "recommend_ready", {
    summary_text: syncRes.current_job_title ? `推荐页已就绪：${syncRes.current_job_title}` : "推荐页已就绪",
    page_ready: true,
    runnable: true,
    match_ok: true,
    match_score: Number(syncRes.match_score || 0) || 0,
    card_count: context.card_count,
    current_job_title: syncRes.current_job_title || context.current_job_title,
    expected_job_title: syncRes.expected_job_title || task?.target_job_title || "",
    page_type: context.page_type
  }, context);
  const processed = new Set(Array.isArray(task?.summary?.processed_ids) ? task.summary.processed_ids.map((v) => cleanText(v)) : []);
  const cards = collectBossRecommendCards().filter((card) => {
    return card.greet_available && card.candidate_key && !processed.has(card.candidate_key);
  });
  if (!cards.length) {
    await sendBossRunnerHeartbeat(task, "recommend_no_cards", {
      summary_text: "当前页暂无可处理卡片",
      wait_reason: "当前页暂无可处理卡片",
      card_count: 0,
      current_job_title: context.current_job_title,
      expected_job_title: syncRes.expected_job_title || task?.target_job_title || "",
      page_type: context.page_type
    }, context);
    return;
  }
  const card = cards[0];
  const cardPayload = serializeBossCard(card);
  markBossCardState(card, "processing");
  await sendBossRunnerHeartbeat(task, "recommend_processing_card", {
    summary_text: `正在处理：${cleanText(card.name || card.currentTitle || "候选人")}`,
    card_count: cards.length,
    current_job_title: context.current_job_title,
    expected_job_title: syncRes.expected_job_title || task?.target_job_title || "",
    page_type: context.page_type,
    candidate_key: cleanText(card.candidate_key || "")
  }, context);
  const cardRes = await bossFetchJson(`/automation/demo/boss/tasks/${task.id}/card-evaluate`, { card: cardPayload }, "POST");
  if (!cardRes?.ok || !cardRes.pass) {
    await sendBossRunnerHeartbeat(task, "recommend_card_skipped", {
      summary_text: `已跳过：${cleanText(card.name || card.currentTitle || "候选人")}`,
      error: cardRes?.error || "",
      card_count: cards.length,
      current_job_title: context.current_job_title,
      expected_job_title: syncRes.expected_job_title || task?.target_job_title || "",
      page_type: context.page_type
    }, context);
    markBossCardState(card, "skip");
    return;
  }
  if (!isBossTaskDetailAiEnabled(task)) {
    const openedDetail = await openBossRecommendCard(card);
    if (!openedDetail) {
      await bossFetchJson(`/automation/demo/boss/tasks/${task.id}/greet`, {
        card: cardPayload,
        candidate: {},
        success: false,
        message: task?.greet_strategy?.opening || "",
        match_score: cardRes.score || 0,
        must_hits: cardRes.keyword_hits || [],
        preferred_hits: [],
        error: "打开详情失败"
      }, "POST");
      await sendBossRunnerHeartbeat(task, "recommend_detail_failed", {
        summary_text: `打开详情失败：${cleanText(card.name || card.currentTitle || "候选人")}`,
        error: "打开详情失败",
        current_job_title: context.current_job_title,
        expected_job_title: syncRes.expected_job_title || task?.target_job_title || "",
        page_type: context.page_type
      }, context);
      markBossCardState(card, "skip");
      return;
    }
    const greetRes = await clickBossGreetButton(card);
    await bossFetchJson(`/automation/demo/boss/tasks/${task.id}/greet`, {
      card: cardPayload,
      candidate: {},
      success: Boolean(greetRes?.ok),
      message: task?.greet_strategy?.opening || "",
      match_score: cardRes.score || 0,
      must_hits: cardRes.keyword_hits || [],
      preferred_hits: [],
      error: greetRes?.error || ""
    }, "POST");
    await closeBossRecommendDetail();
    await sendBossRunnerHeartbeat(task, greetRes?.ok ? "recommend_greet_success" : "recommend_greet_failed", {
      summary_text: `${greetRes?.ok ? "已打招呼" : "打招呼失败"}：${cleanText(card.name || card.currentTitle || "候选人")}`,
      error: greetRes?.error || "",
      current_job_title: context.current_job_title,
      expected_job_title: syncRes.expected_job_title || task?.target_job_title || "",
      page_type: context.page_type
    }, context);
    markBossCardState(card, greetRes?.ok ? "done" : "skip");
    return;
  }
  const opened = await openBossRecommendCard(card);
  if (!opened) {
    await bossFetchJson(`/automation/demo/boss/tasks/${task.id}/greet`, {
      card: cardPayload,
      candidate: {},
      success: false,
      error: "打开详情失败"
    }, "POST");
    await sendBossRunnerHeartbeat(task, "recommend_detail_failed", {
      summary_text: `打开详情失败：${cleanText(card.name || card.currentTitle || "候选人")}`,
      error: "打开详情失败",
      current_job_title: context.current_job_title,
      expected_job_title: syncRes.expected_job_title || task?.target_job_title || "",
      page_type: context.page_type
    }, context);
    markBossCardState(card, "skip");
    return;
  }
  const candidate = await collectBossDetailCandidate();
  if (!candidate) {
    await closeBossRecommendDetail();
    await bossFetchJson(`/automation/demo/boss/tasks/${task.id}/greet`, {
      card: cardPayload,
      candidate: {},
      success: false,
      error: "未识别到详情数据"
    }, "POST");
    await sendBossRunnerHeartbeat(task, "recommend_detail_failed", {
      summary_text: "未识别到详情数据",
      error: "未识别到详情数据",
      current_job_title: context.current_job_title,
      expected_job_title: syncRes.expected_job_title || task?.target_job_title || "",
      page_type: context.page_type
    }, context);
    markBossCardState(card, "skip");
    return;
  }
  const detailRes = await bossFetchJson(`/automation/demo/boss/tasks/${task.id}/detail-evaluate`, { card: cardPayload, candidate }, "POST");
  if (!detailRes?.ok || !detailRes.pass) {
    await closeBossRecommendDetail();
    await sendBossRunnerHeartbeat(task, "recommend_detail_skipped", {
      summary_text: `详情未通过：${cleanText(card.name || card.currentTitle || "候选人")}`,
      error: detailRes?.error || "",
      current_job_title: context.current_job_title,
      expected_job_title: syncRes.expected_job_title || task?.target_job_title || "",
      page_type: context.page_type
    }, context);
    markBossCardState(card, "skip");
    return;
  }
  const greetRes = await clickBossGreetButton(card);
  await bossFetchJson(`/automation/demo/boss/tasks/${task.id}/greet`, {
    card: cardPayload,
    candidate,
    success: Boolean(greetRes?.ok),
    message: detailRes.message || task?.greet_strategy?.opening || "",
    match_score: detailRes.score || cardRes.score || 0,
    must_hits: detailRes.must_hits || [],
    preferred_hits: detailRes.preferred_hits || [],
    error: greetRes?.error || ""
  }, "POST");
  await closeBossRecommendDetail();
  await sendBossRunnerHeartbeat(task, greetRes?.ok ? "recommend_greet_success" : "recommend_greet_failed", {
    summary_text: `${greetRes?.ok ? "已打招呼" : "打招呼失败"}：${cleanText(card.name || card.currentTitle || "候选人")}`,
    error: greetRes?.error || "",
    current_job_title: context.current_job_title,
    expected_job_title: syncRes.expected_job_title || task?.target_job_title || "",
    page_type: context.page_type
  }, context);
  markBossCardState(card, greetRes?.ok ? "done" : "skip");
}

async function runBossMessageAutomation(task) {
  const context = collectBossMessageContext();
  const syncRes = await bossFetchJson(`/automation/demo/boss/tasks/${task.id}/message-page-sync`, context, "POST");
  if (!syncRes?.ok) {
    await sendBossRunnerHeartbeat(task, "message_sync_failed", {
      summary_text: syncRes?.error || "消息页同步失败",
      error: syncRes?.error || "",
      conversation_count: context.conversation_count,
      page_type: context.page_type
    }, context);
    return;
  }
  if (!syncRes.runnable) {
    await sendBossRunnerHeartbeat(task, "message_waiting", {
      summary_text: syncRes.wait_reason || "等待Boss消息页面",
      wait_reason: syncRes.wait_reason || "",
      runnable: Boolean(syncRes.runnable),
      conversation_count: context.conversation_count,
      page_type: context.page_type
    }, context);
    return;
  }
  await sendBossRunnerHeartbeat(task, "message_ready", {
    summary_text: "消息页已就绪",
    runnable: true,
    conversation_count: context.conversation_count,
    page_type: context.page_type
  }, context);
  const queueRes = await bossFetchJson(`/automation/demo/boss/tasks/${task.id}/message-queue`, null, "GET");
  if (!queueRes?.ok || !queueRes.conversation) {
    await sendBossRunnerHeartbeat(task, "message_queue_empty", {
      summary_text: queueRes?.wait_reason || "消息队列暂无待处理会话",
      wait_reason: queueRes?.wait_reason || "消息队列暂无待处理会话",
      conversation_count: context.conversation_count,
      page_type: context.page_type
    }, context);
    return;
  }
  const opened = await openBossMessageConversation(queueRes.conversation);
  if (!opened?.ok) {
    await sendBossRunnerHeartbeat(task, "message_open_failed", {
      summary_text: opened?.error || "未找到会话入口",
      error: opened?.error || "未找到会话入口",
      conversation_count: context.conversation_count,
      page_type: context.page_type
    }, context);
    return;
  }
  await sendBossRunnerHeartbeat(task, "message_processing", {
    summary_text: `正在处理会话：${cleanText(queueRes.conversation?.candidate_name || opened?.item?.candidate_name || "候选人")}`,
    conversation_count: context.conversation_count,
    page_type: context.page_type
  }, context);
  const transcript = collectBossConversationTranscript();
  const lastCandidate = [...transcript].reverse().find((item) => item.sender === "candidate")?.content || opened?.item?.last_message_text || "";
  const decisionRes = await bossFetchJson(`/automation/demo/boss/tasks/${task.id}/message-decide`, {
    conversation_id: queueRes.conversation.id,
    last_candidate_text: lastCandidate,
    messages: transcript
  }, "POST");
  if (!decisionRes?.ok || decisionRes.action !== "send" || !decisionRes.message) {
    await sendBossRunnerHeartbeat(task, "message_waiting", {
      summary_text: decisionRes?.wait_reason || decisionRes?.error || "未到发送时机",
      wait_reason: decisionRes?.wait_reason || "",
      error: decisionRes?.error || "",
      conversation_count: context.conversation_count,
      page_type: context.page_type
    }, context);
    return;
  }
  const input = pickBossMessageInput();
  if (!fillBossMessageInput(input, decisionRes.message)) {
    await bossFetchJson(`/automation/demo/boss/tasks/${task.id}/message-send-result`, {
      conversation_id: queueRes.conversation.id,
      success: false,
      message: decisionRes.message,
      error: "未找到可用输入框"
    }, "POST");
    await sendBossRunnerHeartbeat(task, "message_send_failed", {
      summary_text: "未找到可用输入框",
      error: "未找到可用输入框",
      conversation_count: context.conversation_count,
      page_type: context.page_type
    }, context);
    return;
  }
  await sendBossRunnerHeartbeat(task, "message_sending", {
    summary_text: `正在发送消息：${cleanText(queueRes.conversation?.candidate_name || opened?.item?.candidate_name || "候选人")}`,
    conversation_count: context.conversation_count,
    page_type: context.page_type
  }, context);
  const sendRes = await clickBossMessageSendButton();
  await bossFetchJson(`/automation/demo/boss/tasks/${task.id}/message-send-result`, {
    conversation_id: queueRes.conversation.id,
    success: Boolean(sendRes?.ok),
    message: decisionRes.message,
    error: sendRes?.error || ""
  }, "POST");
  await sendBossRunnerHeartbeat(task, sendRes?.ok ? "message_sent" : "message_send_failed", {
    summary_text: `${sendRes?.ok ? "已发送消息" : "发送失败"}：${cleanText(queueRes.conversation?.candidate_name || opened?.item?.candidate_name || "候选人")}`,
    error: sendRes?.error || "",
    conversation_count: context.conversation_count,
    page_type: context.page_type
  }, context);
}

async function runBossAutomationTick() {
  if (BOSS_RUNNER_BUSY) return;
  if (!shouldRunBossAutomationTickHere()) return;
  const pageInfo = detectBossAutomationPage();
  const pageType = pageInfo.pageType;
  if (!pageType) {
    reportBossRunnerState("boss_runner_page_unrecognized", {
      path: pageInfo.path,
      recommend_likely: pageInfo.recommendLikely,
      message_likely: pageInfo.messageLikely,
      recommend_score: pageInfo.recommendScore,
      message_score: pageInfo.messageScore,
      recommend_cards: pageInfo.recommendCardCount,
      message_items: pageInfo.messageItemCount,
      has_recommend_detail: pageInfo.hasRecommendDetail,
      has_greet_action: pageInfo.hasGreetAction,
      has_message_input: pageInfo.hasMessageInput,
      has_send_button: pageInfo.hasSendButton
    });
    if (BOSS_RUNNER_ACTIVE_TASK_ID) {
      await sendBossRunnerHeartbeat({ id: BOSS_RUNNER_ACTIVE_TASK_ID }, "boss_runner_page_unrecognized", {
        summary_text: "当前Boss页面未识别",
        wait_reason: "当前Boss页面未识别",
        page_type: "",
        page_state: pageInfo.reason,
        detail: {
          ...pageInfo
        }
      });
    }
    return;
  }
  BOSS_RUNNER_BUSY = true;
  try {
    let config = await getBossRunnerConfig();
    if (config?.bossAutomationEnabled && (!config?.apiBase || !config?.token)) {
      config = await getBossRunnerConfig(true);
    }
    if (!config?.bossAutomationEnabled || !config?.token) {
      if (Date.now() - BOSS_RUNNER_LAST_WARN > 15000) {
        BOSS_RUNNER_LAST_WARN = Date.now();
        reportBossRunnerState("boss_runner_config_missing", {
          page_type: pageType,
          has_api_base: Boolean(config?.apiBase),
          has_token: Boolean(config?.token),
          enabled: config?.bossAutomationEnabled !== false
        });
      }
      return;
    }
    const activeTaskRes = await bossFetchJson(`/automation/demo/boss/active-task?page_type=${encodeURIComponent(pageType)}`, null, "GET");
    if (!activeTaskRes?.ok || !activeTaskRes.task) {
      BOSS_RUNNER_ACTIVE_TASK_ID = 0;
      return;
    }
    const task = activeTaskRes.task;
    BOSS_RUNNER_ACTIVE_TASK_ID = Number(task?.id || 0) || 0;
    if (pageType === "recommend") {
      await runBossRecommendAutomation(task);
      return;
    }
    if (pageType === "messages") {
      await runBossMessageAutomation(task);
    }
  } catch (e) {
    const errorMessage = String(e?.message || e || "未知异常");
    reportBossRunnerState("boss_runner_tick_failed", {
      page_type: pageType,
      error: errorMessage
    });
    if (BOSS_RUNNER_ACTIVE_TASK_ID) {
      try {
        await sendBossRunnerHeartbeat({ id: BOSS_RUNNER_ACTIVE_TASK_ID }, "boss_runner_tick_failed", {
          summary_text: "插件执行异常",
          wait_reason: "插件执行异常",
          error: errorMessage,
          page_type: pageType
        }, {
          page_type: pageType
        });
      } catch (_) {
      }
    }
  } finally {
    BOSS_RUNNER_BUSY = false;
  }
}

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (!message || !message.type) {
    sendResponse({ ok: false, error: "unsupported_message_type" });
    return false;
  }
  if (message.type === "collectResumeData") {
    try {
      const candidate = collectResumeData();
      if (!isValidCandidate(candidate)) {
        if (isBossSite() && hasCandidateSignals(candidate)) {
          sendResponse({ ok: true, candidate });
          return true;
        }
        sendResponse({ ok: false, error: "未识别到候选人信息，请先打开候选人完整详情页" });
        return true;
      }
      sendResponse({ ok: true, candidate });
    } catch (e) {
      sendResponse({ ok: false, error: String(e) });
    }
    return true;
  }
  if (message.type === "getResumeCaptureRegion") {
    try {
      const region = pickResumeCaptureRegion();
      sendResponse({ ok: true, region });
    } catch (e) {
      sendResponse({ ok: false, error: String(e) });
    }
    return true;
  }
  if (message.type === "collectSidebarData") {
    try {
      const data = collectBossSidebarData();
      sendResponse({ ok: true, data });
    } catch (e) {
      sendResponse({ ok: false, error: String(e) });
    }
    return true;
  }
  if (message.type === "detectBossRecommendContext") {
    try {
      sendResponse({ ok: true, context: collectBossRecommendContext() });
    } catch (e) {
      sendResponse({ ok: false, error: String(e) });
    }
    return true;
  }
  if (message.type === "collectBossRecommendCards") {
    try {
      const cards = collectBossRecommendCards().map((item) => ({
        candidate_key: item.candidate_key,
        sourceCandidateId: item.sourceCandidateId,
        name: item.name,
        currentTitle: item.currentTitle,
        currentCompany: item.currentCompany,
        workYears: item.workYears,
        education: item.education,
        salary: item.salary,
        age: item.age,
        city: item.city,
        tags: item.tags,
        raw_text: item.raw_text,
        greet_available: item.greet_available,
      }));
      sendResponse({ ok: true, cards });
    } catch (e) {
      sendResponse({ ok: false, error: String(e) });
    }
    return true;
  }
  sendResponse({ ok: false, error: "unsupported_message_type" });
  return false;
});

if (shouldRunBossAutomationTickHere()) {
  setTimeout(() => { runBossAutomationTick().catch(() => {}); }, 1200);
  setInterval(() => { runBossAutomationTick().catch(() => {}); }, 5000);
}
