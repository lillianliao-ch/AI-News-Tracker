let LAST_CANDIDATE = null;
let BUSY = false;
let LAST_IMPORTED_TALENT_ID = 0;
let LAST_REPORT_RESUME_ID = 0;
let ORDER_SEARCH_TIMEOUT = null;

function escapeHtml(v) {
  return String(v == null ? "" : v)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
}

function cleanCaptureText(v) { return String(v == null ? "" : v).trim(); }
function normalizeResumeText(v) {
  const text = String(v == null ? "" : v).replace(/\r\n/g, "\n").replace(/\r/g, "\n").replace(/\u00a0/g, " ").trim();
  return text.length > 200000 ? text.slice(0, 200000) : text;
}
function getResumeText() {
  return normalizeResumeText(document.getElementById("resumeText")?.value || "");
}
function setResumeText(v) {
  const el = document.getElementById("resumeText");
  if (!el) return;
  el.value = normalizeResumeText(v);
}

function setRecommendEnabled(enabled) {
  const btn = document.getElementById("btnRecommend");
  if (!btn) return;
  btn.disabled = BUSY || !enabled;
}

function setGenerateReportEnabled(enabled) {
  const btn = document.getElementById("btnGenerateReport");
  if (!btn) return;
  btn.disabled = BUSY || !enabled;
}

function resetRecommendState() {
  LAST_IMPORTED_TALENT_ID = 0;
  setRecommendEnabled(false);
}

function setReportResumeId(resumeId) {
  LAST_REPORT_RESUME_ID = Number(resumeId || 0) || 0;
  setGenerateReportEnabled(Boolean(LAST_REPORT_RESUME_ID));
}

function resetReportState() {
  setReportResumeId(0);
}

function hasSchoolKeyword(v) {
  return /(大学|学院|学校|研究院|研究所|中学|职高|技校|职业技术学院|专科学校)/.test(cleanCaptureText(v));
}

function isNoiseName(v) {
  const text = cleanCaptureText(v);
  if (!text) return true;
  return /^(试试|牛人|示例|诊断|沟通|招呼|简历|详情|经历|经历概览|工作经历|教育经历|最近关注|工作概览|简历详情|收藏|已收藏|感兴趣|不感兴趣|屏蔽|不合适|举报|转发|转发牛人|职优|吾思职优|吾思职优沟通|已读|未读)$/u.test(text) || /职优|打招呼|立即沟通|最近关注/.test(text);
}

function isStrictMrMsName(v) {
  const text = cleanCaptureText(v);
  if (/^[\u4e00-\u9fa5]{1,8}(先生|女士)$/.test(text)) return true;
  if (/^[\u4e00-\u9fa5]{2,4}$/.test(text) && !isNoiseName(text)) return true;
  return false;
}

function candidateQualityScore(candidate) {
  if (!candidate || typeof candidate !== "object") return 0;
  let score = 0;
  const name = cleanCaptureText(candidate.name);
  if (name && isStrictMrMsName(name) && !isNoiseName(name)) score += 8; else score -= 8;
  if (cleanCaptureText(candidate.currentCompany)) score += 2;
  if (cleanCaptureText(candidate.currentTitle)) score += 2;
  if (cleanCaptureText(candidate.workExperienceText)) score += 5; else score -= 3;
  if (hasSchoolKeyword(candidate.educationSchool)) score += 3;
  else if (hasSchoolKeyword(candidate.educationHighest)) score += 2;
  if (cleanCaptureText(candidate.workYears)) score += 1;
  if (cleanCaptureText(candidate.phone)) score += 1;
  if (cleanCaptureText(candidate.email)) score += 1;
  if (normalizeResumeText(candidate.resumeText).length > 100) score += 2;
  return score;
}

function showResult(lines) {
  const el = document.getElementById("result");
  if (!el) return;
  el.classList.add("show");
  el.innerHTML = lines.map((l) => {
    if (typeof l === "string") return `<div class="r-line">${escapeHtml(l)}</div>`;
    const cls = l.cls || "";
    return `<div class="r-line ${cls}">${escapeHtml(l.text)}</div>`;
  }).join("");
}

function showOk(msg) { showResult([{ text: msg, cls: "r-ok" }]); }
function showErr(msg) { showResult([{ text: msg, cls: "r-err" }]); }
function showInfo(msg) { showResult([{ text: msg, cls: "r-info" }]); }

function normalizeApiBase(v) {
  const raw = String(v || "").trim();
  if (!raw) return "";
  const withProtocol = /^https?:\/\//i.test(raw) ? raw : `http://${raw}`;
  return withProtocol.replace(/\/+$/, "");
}

function normalizeToken(v) {
  const t = String(v || "").trim();
  return t.replace(/^Bearer\s+/i, "").replace(/^"+|"+$/g, "").trim();
}

function getApiBase() {
  return normalizeApiBase(document.getElementById("apiBase")?.value || "");
}

function saveApiBase() {
  const apiBase = getApiBase();
  if (apiBase) chrome.storage.local.set({ apiBase });
}

function setButtonsBusy(isBusy) {
  BUSY = isBusy;
  for (const id of ["btnCapture", "btnClipboard", "btnImport"]) {
    const btn = document.getElementById(id);
    if (btn) btn.disabled = isBusy;
  }
  const recommendSubmit = document.getElementById("btnRecommendSubmit");
  if (recommendSubmit) recommendSubmit.disabled = isBusy;
  const reportSubmit = document.getElementById("btnConfirmGenerateReport");
  if (reportSubmit) reportSubmit.disabled = isBusy;
  const uploadInput = document.getElementById("pluginUploadFile");
  if (uploadInput) uploadInput.disabled = isBusy;
  const uploadDropzone = document.getElementById("pluginUploadDropzone");
  if (uploadDropzone) uploadDropzone.classList.toggle("busy", isBusy);
  setRecommendEnabled(Boolean(LAST_IMPORTED_TALENT_ID));
  setGenerateReportEnabled(Boolean(LAST_REPORT_RESUME_ID));
}

async function getCurrentTab() {
  const allTabs = await chrome.tabs.query({ active: true });
  for (const tab of allTabs) {
    if (tab && tab.id && tab.url && isSupportedPage(tab.url)) return tab;
  }
  for (const tab of allTabs) {
    if (tab && tab.id && tab.url && !tab.url.startsWith("chrome-extension://")) return tab;
  }
  return allTabs[0] || null;
}

function isSameOrigin(urlA, urlB) {
  try { return new URL(String(urlA || "")).origin === new URL(String(urlB || "")).origin; }
  catch (_) { return false; }
}

function extractOrigin(url) {
  try { return new URL(String(url || "")).origin; }
  catch (_) { return ""; }
}

function isLikelyFinanceSystemTitle(title) {
  return /翰格管理系统|HunkTiger/i.test(String(title || "").trim());
}

function isPrivateNetworkUrl(url) {
  try {
    const host = new URL(String(url || "")).hostname.toLowerCase();
    return host === "127.0.0.1" || host === "localhost" ||
      /^192\.168\.\d+\.\d+$/.test(host) ||
      /^10\.\d+\.\d+\.\d+$/.test(host) ||
      /^172\.(1[6-9]|2\d|3[0-1])\.\d+\.\d+$/.test(host);
  } catch (_) {
    return false;
  }
}

function applyApiBase(apiBase) {
  const clean = normalizeApiBase(apiBase);
  if (!clean) return "";
  const input = document.getElementById("apiBase");
  if (input) input.value = clean;
  chrome.storage.local.set({ apiBase: clean });
  return clean;
}

function applyToken(token) {
  const clean = normalizeToken(token);
  if (!clean) return "";
  chrome.storage.local.set({ token: clean });
  return clean;
}

function applyResolvedApiAuth(auth) {
  applyApiBase(auth?.apiBase || "");
  return applyToken(auth?.token || "");
}

async function readTokenFromTab(tabId) {
  try {
    const result = await chrome.scripting.executeScript({
      target: { tabId },
      func: () => {
        try {
          const direct = [
            localStorage.getItem("TOKEN"), sessionStorage.getItem("TOKEN"),
            localStorage.getItem("token"), sessionStorage.getItem("token"),
            localStorage.getItem("access_token"), sessionStorage.getItem("access_token")
          ];
          for (const v of direct) { if (typeof v === "string" && v.trim()) return v.trim(); }
          for (let i = 0; i < localStorage.length; i++) {
            const k = localStorage.key(i);
            if (!k || !/token/i.test(k)) continue;
            const v = localStorage.getItem(k);
            if (typeof v === "string" && v.trim()) return v.trim();
          }
        } catch (_) {}
        return "";
      }
    });
    return normalizeToken(result?.[0]?.result || "");
  } catch (_) { return ""; }
}

async function readAuthSnapshotFromTab(tabId) {
  try {
    const result = await chrome.scripting.executeScript({
      target: { tabId },
      func: () => {
        try {
          const direct = [
            localStorage.getItem("TOKEN"), sessionStorage.getItem("TOKEN"),
            localStorage.getItem("token"), sessionStorage.getItem("token"),
            localStorage.getItem("access_token"), sessionStorage.getItem("access_token")
          ];
          let token = "";
          for (const value of direct) {
            if (typeof value === "string" && value.trim()) {
              token = value.trim();
              break;
            }
          }
          if (!token) {
            for (let i = 0; i < localStorage.length; i++) {
              const k = localStorage.key(i);
              if (!k || !/token/i.test(k)) continue;
              const value = localStorage.getItem(k);
              if (typeof value === "string" && value.trim()) {
                token = value.trim();
                break;
              }
            }
          }
          return {
            token,
            role: String(localStorage.getItem("ROLE") || sessionStorage.getItem("ROLE") || "").trim(),
            username: String(localStorage.getItem("USERNAME") || sessionStorage.getItem("USERNAME") || "").trim(),
            title: String(document.title || "").trim()
          };
        } catch (_) {
          return { token: "", role: "", username: "", title: "" };
        }
      }
    });
    const raw = result?.[0]?.result || {};
    return {
      token: normalizeToken(raw.token || ""),
      role: String(raw.role || "").trim(),
      username: String(raw.username || "").trim(),
      title: String(raw.title || "").trim()
    };
  } catch (_) {
    return { token: "", role: "", username: "", title: "" };
  }
}

function scoreApiAuthCandidate(tab, snapshot, preferredOrigin = "") {
  const origin = extractOrigin(tab?.url || "");
  if (!origin || !snapshot?.token) return -1;
  let score = 0;
  if (preferredOrigin && isSameOrigin(origin, preferredOrigin)) score += 100;
  if (isLikelyFinanceSystemTitle(snapshot.title)) score += 60;
  if (snapshot.role || snapshot.username) score += 30;
  if (isPrivateNetworkUrl(origin)) score += 20;
  return score;
}

async function discoverApiAuth(preferredApiBase) {
  const preferredOrigin = normalizeApiBase(preferredApiBase);
  const tabs = await chrome.tabs.query({});
  let best = null;
  for (const tab of tabs) {
    if (!tab?.id || !tab.url) continue;
    const url = String(tab.url || "").toLowerCase();
    if (url.startsWith("chrome://") || url.startsWith("edge://") || url.startsWith("chrome-extension://")) continue;
    const snapshot = await readAuthSnapshotFromTab(tab.id);
    const score = scoreApiAuthCandidate(tab, snapshot, preferredOrigin);
    if (score < 0) continue;
    const candidate = {
      apiBase: extractOrigin(tab.url),
      token: snapshot.token,
      score
    };
    if (!best || candidate.score > best.score) best = candidate;
  }
  if (best?.apiBase && best?.token) {
    applyResolvedApiAuth(best);
    return { apiBase: best.apiBase, token: best.token };
  }
  return { apiBase: preferredOrigin, token: "" };
}

async function autoResolveToken(apiBase) {
  const fromStorage = await chrome.storage.local.get(["apiBase", "token"]);
  const cached = normalizeToken(fromStorage?.token || "");
  const storedBase = normalizeApiBase(fromStorage?.apiBase || "");
  if (cached && (storedBase || apiBase)) {
    return applyResolvedApiAuth({ apiBase: storedBase || apiBase, token: cached });
  }
  const targetBase = storedBase || normalizeApiBase(apiBase);
  const currentTab = await getCurrentTab();
  if (currentTab && currentTab.id && targetBase && isSameOrigin(currentTab.url, targetBase)) {
    const t = await readTokenFromTab(currentTab.id);
    if (t) return applyResolvedApiAuth({ apiBase: targetBase, token: t });
  }
  const tabs = await chrome.tabs.query({});
  for (const tab of tabs) {
    if (!tab?.id || !tab.url) continue;
    if (!targetBase || !isSameOrigin(tab.url, targetBase)) continue;
    const t = await readTokenFromTab(tab.id);
    if (t) return applyResolvedApiAuth({ apiBase: targetBase, token: t });
  }
  const discovered = await discoverApiAuth(targetBase || apiBase);
  if (discovered?.token) return applyResolvedApiAuth(discovered);
  throw new Error("未找到登录Token，请先登录系统并保持页面打开");
}

function isSupportedPage(url) {
  try {
    const host = new URL(String(url || "")).hostname.toLowerCase();
    return host === "zhipin.com" || host.endsWith(".zhipin.com") ||
      host === "liepin.com" || host.endsWith(".liepin.com") ||
      host === "51job.com" || host.endsWith(".51job.com");
  } catch (_) { return false; }
}

function isBossPage(url) {
  try {
    const host = new URL(String(url || "")).hostname.toLowerCase();
    return host === "zhipin.com" || host.endsWith(".zhipin.com");
  } catch (_) { return false; }
}

function detectSourceSiteByUrl(url) {
  try {
    const host = new URL(String(url || "")).hostname.toLowerCase();
    if (host === "zhipin.com" || host.endsWith(".zhipin.com")) return "Boss直聘";
    if (host === "liepin.com" || host.endsWith(".liepin.com")) return "猎聘";
    if (host === "51job.com" || host.endsWith(".51job.com")) return "前程无忧";
    return host;
  } catch (_) { return ""; }
}

async function injectContentScript(tabId) {
  await chrome.scripting.executeScript({ target: { tabId, allFrames: true }, files: ["content.js"] });
}

function isConnectionErrorMessage(msg) {
  const text = String(msg || "");
  return text.includes("Could not establish connection") || text.includes("Receiving end does not exist") ||
    text.includes("No tab with id") || text.includes("No frame with id") || text.includes("Frame with ID");
}

function sleep(ms) { return new Promise((r) => setTimeout(r, ms)); }

async function requestMessageFromFrame(tabId, frameId, message) {
  try { return await chrome.tabs.sendMessage(tabId, message, { frameId }); }
  catch (e) {
    if (isConnectionErrorMessage(String(e?.message || e || ""))) {
      await injectContentScript(tabId);
      return await chrome.tabs.sendMessage(tabId, message, { frameId });
    }
    throw e;
  }
}

async function requestMessageFromFrameWithRetry(tabId, frameId, message, retry = 2, delayMs = 220) {
  let lastErr = null;
  for (let i = 0; i <= retry; i++) {
    try { const res = await requestMessageFromFrame(tabId, frameId, message); if (res) return res; }
    catch (e) { lastErr = e; }
    if (i < retry) await sleep(delayMs);
  }
  if (lastErr) throw lastErr;
  return null;
}

async function getBossResumeFrameIds(tabId) {
  try {
    const frames = await chrome.webNavigation.getAllFrames({ tabId });
    if (!Array.isArray(frames)) return [];
    const scored = [];
    for (const frame of frames) {
      if (!frame || typeof frame.frameId !== "number" || frame.frameId <= 0) continue;
      const frameUrl = String(frame.url || "");
      if (!frameUrl || !/zhipin\.com/i.test(frameUrl)) continue;
      let score = 10;
      if (/\/web\/frame\/c-resume\b/i.test(frameUrl)) score = 100;
      else if (/\/web\/frame\/recommend\b/i.test(frameUrl)) score = 90;
      else if (/\/web\/frame\//i.test(frameUrl)) score = 60;
      scored.push({ id: frame.frameId, score });
    }
    scored.sort((a, b) => b.score - a.score);
    return Array.from(new Set(scored.map((item) => item.id)));
  } catch (_) { return []; }
}

function mergeCandidate(primary, secondary) {
  const a = primary && typeof primary === "object" ? primary : {};
  const b = secondary && typeof secondary === "object" ? secondary : {};
  return {
    sourceSite: a.sourceSite || b.sourceSite || "",
    sourceCandidateId: a.sourceCandidateId || b.sourceCandidateId || "",
    name: a.name || b.name || "",
    phone: a.phone || b.phone || "",
    email: a.email || b.email || "",
    currentCompany: a.currentCompany || b.currentCompany || "",
    currentTitle: a.currentTitle || b.currentTitle || "",
    workExperienceText: a.workExperienceText || b.workExperienceText || "",
    resumeText: normalizeResumeText(a.resumeText).length >= normalizeResumeText(b.resumeText).length
      ? normalizeResumeText(a.resumeText)
      : normalizeResumeText(b.resumeText),
    educationSchool: a.educationSchool || b.educationSchool || "",
    educationHighest: a.educationHighest || b.educationHighest || "",
    workYears: a.workYears || b.workYears || "",
    pageUrl: a.pageUrl || b.pageUrl || ""
  };
}

function hasCandidateData(candidate) {
  if (!candidate || typeof candidate !== "object") return false;
  return Boolean(
    String(candidate.name || "").trim() || String(candidate.currentCompany || "").trim() ||
    String(candidate.currentTitle || "").trim() || String(candidate.workExperienceText || "").trim() ||
    normalizeResumeText(candidate.resumeText) ||
    String(candidate.educationSchool || "").trim() || String(candidate.educationHighest || "").trim() ||
    String(candidate.workYears || "").trim() || String(candidate.phone || "").trim() ||
    String(candidate.email || "").trim()
  );
}

async function cropImageDataUrl(dataUrl, region) {
  if (!dataUrl || !region || typeof region !== "object") return "";
  const img = await new Promise((resolve, reject) => {
    const node = new Image();
    node.onload = () => resolve(node);
    node.onerror = () => reject(new Error("截图解码失败"));
    node.src = dataUrl;
  });
  const viewportWidth = Math.max(1, Number(region.viewportWidth) || img.width);
  const viewportHeight = Math.max(1, Number(region.viewportHeight) || img.height);
  const ratioX = img.width / viewportWidth;
  const ratioY = img.height / viewportHeight;
  const x = Math.max(0, Math.floor((Number(region.left) || 0) * ratioX));
  const y = Math.max(0, Math.floor((Number(region.top) || 0) * ratioY));
  const width = Math.max(1, Math.floor((Number(region.width) || viewportWidth) * ratioX));
  const height = Math.max(1, Math.floor((Number(region.height) || viewportHeight) * ratioY));
  const cropW = Math.min(width, img.width - x);
  const cropH = Math.min(height, img.height - y);
  const canvas = document.createElement("canvas");
  canvas.width = Math.max(1, cropW);
  canvas.height = Math.max(1, cropH);
  const ctx = canvas.getContext("2d");
  if (!ctx) return "";
  ctx.drawImage(img, x, y, cropW, cropH, 0, 0, cropW, cropH);
  return canvas.toDataURL("image/png");
}

async function requestCandidateByOcr(tab, runId) {
  if (!tab || !tab.id) return { ok: false, error: "未获取到标签页" };
  const regionRes = await requestMessageFromFrameWithRetry(tab.id, 0, { type: "getResumeCaptureRegion" }, 1, 180).catch(() => null);
  if (!regionRes || !regionRes.ok || !regionRes.region) {
    return { ok: false, error: "未定位到简历区域" };
  }
  const fullImage = await chrome.tabs.captureVisibleTab(tab.windowId, { format: "png" });
  const croppedImage = await cropImageDataUrl(fullImage, regionRes.region);
  const base64 = String(croppedImage || "").split(",")[1] || "";
  if (!base64 || base64.length < 1000) {
    return { ok: false, error: "截图为空" };
  }
  const sourceSite = detectSourceSiteByUrl(tab.url || "");
  const data = await callApi("/plugin/ocr/parse", {
    imageBase64: base64, sourceSite, pageUrl: tab.url || "", debugRunId: runId
  }, runId);
  if (!data || !data.ok || !data.candidate) {
    return { ok: false, error: String(data?.error || "OCR解析失败") };
  }
  const candidate = data.candidate || {};
  if (!candidate.sourceSite) candidate.sourceSite = sourceSite;
  if (!candidate.pageUrl) candidate.pageUrl = tab.url || "";
  candidate.resumeText = normalizeResumeText(data.text || candidate.resumeText || "");
  return { ok: true, candidate };
}

async function requestCandidateFromTabDom(tabId, tabUrl) {
  if (!isBossPage(tabUrl)) {
    return await requestMessageFromFrame(tabId, 0, { type: "collectResumeData" });
  }
  let topCandidate = null;
  const topRes = await requestMessageFromFrameWithRetry(tabId, 0, { type: "collectResumeData" }, 1, 200).catch(() => null);
  if (topRes?.ok && topRes.candidate) topCandidate = topRes.candidate;
  let frameIds = await getBossResumeFrameIds(tabId);
  if (!frameIds.length) { await sleep(260); frameIds = await getBossResumeFrameIds(tabId); }
  if (!frameIds.length) { await sleep(420); frameIds = await getBossResumeFrameIds(tabId); }
  let iframeCandidate = null;
  for (const frameId of frameIds) {
    for (let i = 0; i < 8; i++) {
      const frameRes = await requestMessageFromFrameWithRetry(tabId, frameId, { type: "collectResumeData" }, 1, 220).catch(() => null);
      if (frameRes?.ok && frameRes.candidate) {
        const currentScore = candidateQualityScore(frameRes.candidate);
        if (!iframeCandidate || currentScore > candidateQualityScore(iframeCandidate)) iframeCandidate = frameRes.candidate;
        if (currentScore >= 7) break;
      }
      if (i < 7) await sleep(260);
    }
  }
  const mainCandidates = [topCandidate, iframeCandidate].filter((x) => hasCandidateData(x));
  const withWorkExp = mainCandidates.filter((x) => cleanCaptureText(x?.workExperienceText));
  const rankedMain = (withWorkExp.length ? withWorkExp : mainCandidates).sort((a, b) => candidateQualityScore(b) - candidateQualityScore(a));
  let merged = mergeCandidate(rankedMain[0] || null, rankedMain[1] || null);
  if (!hasCandidateData(merged)) {
    const retryTopRes = await requestMessageFromFrameWithRetry(tabId, 0, { type: "collectResumeData" }, 2, 260).catch(() => null);
    if (retryTopRes?.ok && retryTopRes.candidate) merged = mergeCandidate(retryTopRes.candidate, merged);
  }
  if (hasCandidateData(merged)) return { ok: true, candidate: merged };
  return { ok: false, error: frameIds.length ? "未获取到简历数据" : "未找到简历区域" };
}

async function requestCandidateFromTab(tab) {
  const runId = `run_${Date.now()}`;
  const tabId = tab?.id || 0;
  const tabUrl = String(tab?.url || "");
  let ocrResult = null;
  try { ocrResult = await requestCandidateByOcr(tab, runId); } catch (_) {}
  let domResult = null;
  try { domResult = await requestCandidateFromTabDom(tabId, tabUrl); } catch (_) {}
  const ocrCandidate = ocrResult?.ok ? ocrResult.candidate : null;
  const domCandidate = domResult?.ok ? domResult.candidate : null;
  if (ocrCandidate && domCandidate) {
    const scoreOcr = candidateQualityScore(ocrCandidate);
    const scoreDom = candidateQualityScore(domCandidate);
    const merged = scoreOcr >= scoreDom
      ? mergeCandidate(ocrCandidate, domCandidate)
      : mergeCandidate(domCandidate, ocrCandidate);
    return { ok: true, candidate: merged };
  }
  if (ocrCandidate) return { ok: true, candidate: ocrCandidate };
  if (domCandidate) return { ok: true, candidate: domCandidate };
  if (domResult && typeof domResult.ok === "boolean") return domResult;
  if (ocrResult && typeof ocrResult.ok === "boolean") return ocrResult;
  return { ok: false, error: "抓取失败" };
}

async function callApi(path, payload) {
  const apiBase = getApiBase();
  if (!apiBase) throw new Error("请先填写系统地址");
  const token = await autoResolveToken(apiBase);
  const target = `${apiBase}${path}`;
  const timeoutMs = String(path || "").includes("/plugin/ocr/parse") ? 90000 : 20000;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  let resp;
  try {
    resp = await fetch(target, {
      method: "POST",
      headers: { "Authorization": `Bearer ${token}`, "Content-Type": "application/json" },
      body: JSON.stringify(payload || {}),
      signal: controller.signal
    });
  } catch (e) {
    clearTimeout(timer);
    throw (e?.name === "AbortError")
      ? new Error("请求超时，请检查系统地址和网络")
      : new Error("网络请求失败，请检查系统地址和服务状态");
  }
  clearTimeout(timer);
  const raw = await resp.text();
  let data;
  try { data = raw ? JSON.parse(raw) : {}; } catch (_) { data = { detail: raw || "" }; }
  if (!resp.ok) throw new Error(data?.detail || `请求失败(${resp.status})`);
  return data;
}

async function callApiGet(path) {
  const apiBase = getApiBase();
  if (!apiBase) throw new Error("请先填写系统地址");
  const token = await autoResolveToken(apiBase);
  const target = `${apiBase}${path}`;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 20000);
  let resp;
  try {
    resp = await fetch(target, {
      method: "GET",
      headers: { "Authorization": `Bearer ${token}` },
      signal: controller.signal
    });
  } catch (e) {
    clearTimeout(timer);
    throw (e?.name === "AbortError")
      ? new Error("请求超时，请检查系统地址和网络")
      : new Error("网络请求失败，请检查系统地址和服务状态");
  }
  clearTimeout(timer);
  const raw = await resp.text();
  let data;
  try { data = raw ? JSON.parse(raw) : {}; } catch (_) { data = { detail: raw || "" }; }
  if (!resp.ok) throw new Error(data?.detail || `请求失败(${resp.status})`);
  return data;
}

async function callApiForm(path, formData) {
  const apiBase = getApiBase();
  if (!apiBase) throw new Error("请先填写系统地址");
  const token = await autoResolveToken(apiBase);
  const target = `${apiBase}${path}`;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 20000);
  let resp;
  try {
    resp = await fetch(target, {
      method: "POST",
      headers: { "Authorization": `Bearer ${token}` },
      body: formData,
      signal: controller.signal
    });
  } catch (e) {
    clearTimeout(timer);
    throw (e?.name === "AbortError")
      ? new Error("请求超时，请检查系统地址和网络")
      : new Error("网络请求失败，请检查系统地址和服务状态");
  }
  clearTimeout(timer);
  const raw = await resp.text();
  let data;
  try { data = raw ? JSON.parse(raw) : {}; } catch (_) { data = { detail: raw || "" }; }
  if (!resp.ok) throw new Error(data?.detail || `请求失败(${resp.status})`);
  return data;
}

function parseFilenameFromDisposition(contentDisposition) {
  const cd = String(contentDisposition || "");
  const utf8Match = cd.match(/filename\*\s*=\s*UTF-8''([^;]+)/i);
  if (utf8Match && utf8Match[1]) {
    try { return decodeURIComponent(utf8Match[1]); } catch (_) { return utf8Match[1]; }
  }
  const quotedMatch = cd.match(/filename\s*=\s*"([^"]+)"/i);
  if (quotedMatch && quotedMatch[1]) return quotedMatch[1];
  const plainMatch = cd.match(/filename\s*=\s*([^;]+)/i);
  if (plainMatch && plainMatch[1]) return plainMatch[1].trim();
  return "";
}

async function callApiDownload(path, fallbackFilename) {
  const apiBase = getApiBase();
  if (!apiBase) throw new Error("请先填写系统地址");
  const token = await autoResolveToken(apiBase);
  const target = `${apiBase}${path}`;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 45000);
  let resp;
  try {
    resp = await fetch(target, {
      method: "GET",
      headers: { "Authorization": `Bearer ${token}` },
      signal: controller.signal
    });
  } catch (e) {
    clearTimeout(timer);
    throw (e?.name === "AbortError")
      ? new Error("下载超时，请检查系统地址和网络")
      : new Error("下载失败，请检查系统地址和服务状态");
  }
  clearTimeout(timer);
  if (!resp.ok) {
    const raw = await resp.text();
    let data;
    try { data = raw ? JSON.parse(raw) : {}; } catch (_) { data = { detail: raw || "" }; }
    throw new Error(data?.detail || `下载失败(${resp.status})`);
  }
  const blob = await resp.blob();
  const filename = parseFilenameFromDisposition(resp.headers.get("content-disposition")) || fallbackFilename || "download.bin";
  const objectUrl = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = objectUrl;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(objectUrl);
}

function setUploadMessage(text, tone = "ok") {
  const msgEl = document.getElementById("pluginUploadMsg");
  if (!msgEl) return;
  if (!text) {
    msgEl.textContent = "";
    return;
  }
  const color = tone === "err" ? "#dc2626" : tone === "info" ? "#475569" : "#16a34a";
  msgEl.innerHTML = `<span style="color:${color};">${escapeHtml(text)}</span>`;
}

function setUploadProgress(percent) {
  const progressEl = document.getElementById("pluginUploadProgress");
  if (!progressEl) return;
  progressEl.style.display = "block";
  const fill = progressEl.querySelector(".progress-fill");
  if (fill) fill.style.width = `${Math.max(0, Math.min(100, Number(percent) || 0))}%`;
}

async function uploadResumeFile(file) {
  if (!file || BUSY) return;
  const ext = String(file.name || "").toLowerCase().split(".").pop();
  const allowed = ["pdf", "doc", "docx", "txt", "jpg", "jpeg", "png"];
  if (!allowed.includes(ext)) {
    setUploadMessage(`不支持的文件类型: ${ext || "-"}`, "err");
    return;
  }
  setButtonsBusy(true);
  setUploadMessage("", "info");
  setUploadProgress(25);
  showInfo("正在上传简历文件...");
  try {
    saveApiBase();
    const formData = new FormData();
    formData.append("file", file);
    const res = await callApiForm("/resumes/upload", formData);
    setUploadProgress(100);
    if (!res?.ok) {
      const prefix = res?.duplicate ? "检测到重复: " : "上传失败: ";
      const message = `${prefix}${res?.msg || res?.detail || "未知错误"}`;
      setUploadMessage(message, "err");
      showErr(message);
      return;
    }
    setReportResumeId(res?.id);
    const info = res?.extracted_info || {};
    const extracted = [];
    if (info.name) extracted.push(`姓名:${info.name}`);
    if (info.phone) extracted.push(`电话:${info.phone}`);
    if (info.email) extracted.push(`邮箱:${info.email}`);
    const suffix = extracted.length ? `已提取: ${extracted.join("，")}` : "可直接生成报告";
    setUploadMessage(`上传成功！${suffix}`, "ok");
    const lines = [{ text: `上传成功，简历ID：${Number(res?.id || 0) || "-"}`, cls: "r-ok" }];
    if (extracted.length) lines.push({ text: extracted.join("，"), cls: "r-info" });
    lines.push({ text: "可点击“生成报告”继续操作", cls: "r-info" });
    showResult(lines);
  } catch (e) {
    const msg = String(e?.message || e);
    setUploadMessage(`上传失败: ${msg}`, "err");
    showErr(msg);
  } finally {
    setTimeout(() => {
      const progressEl = document.getElementById("pluginUploadProgress");
      if (progressEl) progressEl.style.display = "none";
      const fill = progressEl?.querySelector(".progress-fill");
      if (fill) fill.style.width = "0%";
    }, 1500);
    setButtonsBusy(false);
  }
}

function setupPluginUploadDropzone() {
  const dropzone = document.getElementById("pluginUploadDropzone");
  const fileInput = document.getElementById("pluginUploadFile");
  if (!dropzone || !fileInput) return;
  if (fileInput._pluginUploadBound) return;
  fileInput._pluginUploadBound = true;
  dropzone.addEventListener("click", () => {
    if (BUSY) return;
    fileInput.click();
  });
  fileInput.addEventListener("change", async (e) => {
    const file = e?.target?.files?.[0];
    if (!file) return;
    await uploadResumeFile(file);
    e.target.value = "";
  });
  dropzone.addEventListener("dragover", (e) => {
    e.preventDefault();
    if (BUSY) return;
    dropzone.classList.add("dragover");
  });
  dropzone.addEventListener("dragleave", (e) => {
    e.preventDefault();
    dropzone.classList.remove("dragover");
  });
  dropzone.addEventListener("drop", async (e) => {
    e.preventDefault();
    dropzone.classList.remove("dragover");
    if (BUSY) return;
    const file = e?.dataTransfer?.files?.[0];
    if (!file) return;
    await uploadResumeFile(file);
  });
}

function setGenerateReportMsg(text, tone = "info") {
  const msgEl = document.getElementById("generateReportMsg");
  if (!msgEl) return;
  if (!text) {
    msgEl.textContent = "";
    return;
  }
  const color = tone === "err" ? "#dc2626" : tone === "ok" ? "#16a34a" : "#64748b";
  msgEl.innerHTML = `<span style="color:${color};">${escapeHtml(text)}</span>`;
}

async function loadReportTemplates() {
  const select = document.getElementById("reportTemplateSelect");
  if (!select) return;
  select.innerHTML = '<option value="">-- 加载中 --</option>';
  try {
    const data = await callApiGet("/resume-templates");
    const templates = Array.isArray(data?.templates) ? data.templates : [];
    if (data?.ok && templates.length) {
      let html = '<option value="">-- 请选择模板 --</option>';
      for (const template of templates) {
        const id = Number(template?.id || 0);
        if (!id) continue;
        const name = escapeHtml(template?.name || `模板${id}`);
        html += `<option value="${id}">${name}</option>`;
      }
      select.innerHTML = html || '<option value="">-- 暂无模板，请先上传 --</option>';
      return;
    }
    select.innerHTML = '<option value="">-- 暂无模板，请先上传 --</option>';
  } catch (_) {
    select.innerHTML = '<option value="">-- 加载失败 --</option>';
  }
}

async function showGenerateReportModal() {
  if (!LAST_REPORT_RESUME_ID) {
    showErr("请先录入人才或上传简历后再生成报告");
    return;
  }
  const modal = document.getElementById("generateReportModal");
  if (!modal) return;
  setGenerateReportMsg("", "info");
  modal.style.display = "flex";
  modal.classList.add("show");
  await loadReportTemplates();
}

function closeGenerateReportModal() {
  const modal = document.getElementById("generateReportModal");
  if (!modal) return;
  modal.classList.remove("show");
  modal.style.display = "none";
}

async function uploadReportTemplate(input) {
  if (BUSY) return;
  const file = input?.files?.[0];
  if (!file) return;
  const ext = String(file.name || "").toLowerCase().split(".").pop();
  if (!["txt", "docx", "doc"].includes(ext)) {
    setGenerateReportMsg("仅支持txt、docx、doc格式", "err");
    input.value = "";
    return;
  }
  setButtonsBusy(true);
  setGenerateReportMsg("正在上传模板...", "info");
  try {
    const formData = new FormData();
    formData.append("file", file);
    const res = await callApiForm("/resume-templates/upload", formData);
    if (!res?.ok) throw new Error(res?.detail || res?.msg || "模板上传失败");
    await loadReportTemplates();
    const select = document.getElementById("reportTemplateSelect");
    if (select && res?.id) select.value = String(res.id);
    setGenerateReportMsg("模板上传成功", "ok");
  } catch (e) {
    setGenerateReportMsg(`模板上传失败: ${String(e?.message || e)}`, "err");
  } finally {
    input.value = "";
    setButtonsBusy(false);
  }
}

async function downloadResumeReport(resumeId) {
  const targetResumeId = Number(resumeId || LAST_REPORT_RESUME_ID || 0);
  if (!targetResumeId) throw new Error("请先选择可生成报告的简历");
  await callApiDownload(`/resumes/${targetResumeId}/report`, `report_${targetResumeId}.docx`);
}

async function confirmGenerateReport() {
  if (BUSY) return;
  const templateId = String(document.getElementById("reportTemplateSelect")?.value || "").trim();
  if (!templateId) {
    setGenerateReportMsg("请选择一个模板", "err");
    return;
  }
  const resumeId = Number(LAST_REPORT_RESUME_ID || 0);
  if (!resumeId) {
    setGenerateReportMsg("请先录入人才或上传简历", "err");
    return;
  }
  const btn = document.getElementById("btnConfirmGenerateReport");
  const defaultText = "开始生成";
  setButtonsBusy(true);
  if (btn) btn.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="spin"><circle cx="12" cy="12" r="10"></circle><path d="M12 6v6l4 2"></path></svg> 生成中...';
  setGenerateReportMsg("AI正在生成报告，请稍候...", "info");
  try {
    const formData = new FormData();
    formData.append("template_id", templateId);
    const res = await callApiForm(`/resumes/${resumeId}/generate-report`, formData);
    if (!res?.ok) throw new Error(res?.detail || res?.msg || "生成失败");
    setGenerateReportMsg("报告生成成功，正在下载...", "ok");
    await downloadResumeReport(resumeId);
    closeGenerateReportModal();
    showOk("报告生成成功，已开始下载");
  } catch (e) {
    setGenerateReportMsg(`生成失败: ${String(e?.message || e)}`, "err");
  } finally {
    if (btn) btn.textContent = defaultText;
    setButtonsBusy(false);
  }
}

function populateForm(candidate, onlyFillEmpty = false) {
  if (!candidate) return;
  const set = (id, val) => {
    const el = document.getElementById(id);
    if (!el) return;
    if (onlyFillEmpty && cleanCaptureText(el.value)) return;
    el.value = cleanCaptureText(val);
  };
  set("fieldName", candidate.name);
  set("fieldPhone", candidate.phone);
  set("fieldCompany", candidate.currentCompany);
  set("fieldTitle", candidate.currentTitle);
  set("fieldSchool", candidate.educationSchool);
  set("fieldEdu", candidate.educationHighest);
  if (onlyFillEmpty) {
    if (!getResumeText()) setResumeText(candidate.resumeText || "");
  } else {
    setResumeText(candidate.resumeText || "");
  }
}

function readFormToCandidate(requireMandatory = true) {
  const val = (id) => (document.getElementById(id)?.value || "").trim();
  const name = val("fieldName");
  const phone = val("fieldPhone");
  const base = LAST_CANDIDATE && typeof LAST_CANDIDATE === "object" ? { ...LAST_CANDIDATE } : {};
  if (requireMandatory) {
    if (!name) throw new Error("请填写姓名");
    if (!phone) throw new Error("请填写手机号");
  } else if (!name && !phone && !base.name && !base.phone && !getResumeText()) {
    throw new Error("请先抓取简历或粘贴简历全文");
  }
  base.name = name;
  base.phone = phone;
  base.currentCompany = val("fieldCompany") || base.currentCompany || "";
  base.currentTitle = val("fieldTitle") || base.currentTitle || "";
  base.educationSchool = val("fieldSchool") || base.educationSchool || "";
  base.educationHighest = val("fieldEdu") || base.educationHighest || "";
  base.resumeText = getResumeText() || normalizeResumeText(base.resumeText || "");
  return base;
}

async function captureCandidate() {
  if (BUSY) return;
  resetRecommendState();
  resetReportState();
  setButtonsBusy(true);
  showInfo("正在抓取简历...");
  try {
    saveApiBase();
    const tab = await getCurrentTab();
    if (!tab?.id) { showErr("未获取到标签页"); return; }
    if (!isSupportedPage(tab.url)) { showErr("请在Boss/猎聘/51job候选人页面执行"); return; }
    const res = await requestCandidateFromTab(tab);
    if (!res?.ok || !res.candidate) {
      LAST_CANDIDATE = null;
      showErr(res?.error || "抓取失败");
      return;
    }
    LAST_CANDIDATE = res.candidate;
    populateForm(LAST_CANDIDATE);
    showOk("抓取完成，请确认信息后录入");
  } catch (e) {
    LAST_CANDIDATE = null;
    showErr(String(e?.message || e));
  } finally {
    setButtonsBusy(false);
  }
}

async function captureFromClipboard() {
  if (BUSY) return;
  resetRecommendState();
  resetReportState();
  setButtonsBusy(true);
  showInfo("正在读取剪贴板...");
  try {
    saveApiBase();
    let clipText = "";
    try { clipText = await navigator.clipboard.readText(); } catch (_) {
      showErr("无法读取剪贴板，请允许剪贴板权限");
      return;
    }
    if (!clipText || clipText.trim().length < 20) {
      showErr("剪贴板内容过少，请复制完整简历文本");
      return;
    }
    showInfo("正在解析简历...");
    const data = await callApi("/plugin/ocr/parse", {
      resumeText: clipText.trim(),
      sourceSite: "剪贴板",
      pageUrl: "",
    });
    if (!data?.ok || !data.candidate) {
      showErr(data?.error || "解析失败");
      return;
    }
    LAST_CANDIDATE = data.candidate;
    LAST_CANDIDATE.resumeText = normalizeResumeText(data.text || clipText);
    if (!LAST_CANDIDATE.sourceSite) LAST_CANDIDATE.sourceSite = "剪贴板";
    populateForm(LAST_CANDIDATE);
    showOk("解析完成，请确认信息后录入");
  } catch (e) {
    showErr(String(e?.message || e));
  } finally {
    setButtonsBusy(false);
  }
}

async function parseCandidateFromResumeText(resumeText, baseCandidate) {
  const text = normalizeResumeText(resumeText);
  if (!text || text.length < 20) return null;
  const sourceSite = cleanCaptureText(baseCandidate?.sourceSite) || "手动粘贴";
  const pageUrl = cleanCaptureText(baseCandidate?.pageUrl);
  const data = await callApi("/plugin/ocr/parse", { resumeText: text, sourceSite, pageUrl });
  if (!data?.ok || !data.candidate) throw new Error(data?.error || "简历文本解析失败");
  const parsed = data.candidate || {};
  if (!parsed.sourceSite) parsed.sourceSite = sourceSite;
  if (!parsed.pageUrl) parsed.pageUrl = pageUrl;
  parsed.resumeText = normalizeResumeText(data.text || text);
  return parsed;
}

async function doDedupeOnly() {
  if (BUSY) return;
  resetRecommendState();
  resetReportState();
  setButtonsBusy(true);
  try {
    saveApiBase();
    const resumeText = getResumeText();
    let parsedByText = null;
    if (resumeText && resumeText.length >= 20) {
      showInfo("正在解析简历文本...");
      parsedByText = await parseCandidateFromResumeText(resumeText, LAST_CANDIDATE || {});
      LAST_CANDIDATE = mergeCandidate(parsedByText, LAST_CANDIDATE);
      populateForm(parsedByText, true);
    }
    let candidate;
    try { candidate = readFormToCandidate(false); } catch (e) { showErr(e.message); return; }
    if (parsedByText) candidate = mergeCandidate(candidate, parsedByText);
    candidate.resumeText = resumeText || normalizeResumeText(parsedByText?.resumeText || candidate.resumeText || "");
    if (!candidate.sourceSite && candidate.resumeText) candidate.sourceSite = "手动粘贴";
    LAST_CANDIDATE = candidate;
    showInfo("正在查重...");
    const dedupeData = await callApi("/plugin/dedupe/check", { candidate });
    const levelMap = { strong: "强匹配", medium: "中匹配", weak: "弱匹配", none: "无重复" };
    const matchLevel = dedupeData?.matchLevel || "none";
    const matchIds = Array.isArray(dedupeData?.matchedTalentIds) ? dedupeData.matchedTalentIds : [];
    const lines = [{ text: `查重结果：${levelMap[matchLevel] || "无重复"}`, cls: matchLevel === "none" ? "r-ok" : "r-warn" }];
    if (matchIds.length) lines.push({ text: `已有人才ID：${matchIds.join(", ")}`, cls: "r-warn" });
    if (dedupeData?.mergeSuggestion) lines.push({ text: dedupeData.mergeSuggestion, cls: "r-info" });
    showResult(lines);
  } catch (e) {
    showErr(String(e?.message || e));
  } finally {
    setButtonsBusy(false);
  }
}

function openRecommendModal() {
  if (!LAST_IMPORTED_TALENT_ID) {
    showErr("请先录入人才库后再推荐");
    return;
  }
  const modal = document.getElementById("recommendModal");
  if (!modal) return;
  document.getElementById("recommendResumeId").value = String(LAST_IMPORTED_TALENT_ID);
  document.getElementById("recommendCaseId").value = "";
  document.getElementById("recommendCompanyInput").value = "";
  document.getElementById("recommendNote").value = "";
  const suggestions = document.getElementById("orderSuggestions");
  if (suggestions) suggestions.style.display = "none";
  setupOrderAutocomplete();
  modal.style.display = "flex";
  modal.classList.add("show");
}

function closeRecommendModal() {
  const modal = document.getElementById("recommendModal");
  if (!modal) return;
  modal.classList.remove("show");
  modal.style.display = "none";
  const suggestions = document.getElementById("orderSuggestions");
  if (suggestions) suggestions.style.display = "none";
}

function setupOrderAutocomplete() {
  const input = document.getElementById("recommendCompanyInput");
  const suggestions = document.getElementById("orderSuggestions");
  if (!input || !suggestions) return;
  input.oninput = () => {
    const keyword = String(input.value || "").trim();
    if (ORDER_SEARCH_TIMEOUT) clearTimeout(ORDER_SEARCH_TIMEOUT);
    if (!keyword) {
      suggestions.style.display = "none";
      document.getElementById("recommendCaseId").value = "";
      return;
    }
    ORDER_SEARCH_TIMEOUT = setTimeout(() => searchOrdersForRecommend(keyword), 300);
  };
  input.onfocus = () => {
    if (input.value.trim() && suggestions.innerHTML) suggestions.style.display = "block";
  };
}

async function searchOrdersForRecommend(keyword) {
  try {
    const data = await callApiGet(`/cases/search?q=${encodeURIComponent(keyword)}&limit=10`);
    showOrderSuggestions(Array.isArray(data?.cases) ? data.cases : []);
  } catch (_) {}
}

function showOrderSuggestions(cases) {
  const suggestions = document.getElementById("orderSuggestions");
  if (!suggestions) return;
  suggestions.innerHTML = "";
  if (!Array.isArray(cases) || !cases.length) {
    suggestions.style.display = "none";
    return;
  }
  for (const c of cases) {
    const companyName = cleanCaptureText(c?.company_name || c?.company || "未知");
    const position = cleanCaptureText(c?.position_title || c?.job_info || "");
    const item = document.createElement("div");
    item.className = "order-suggestion-item";
    item.innerHTML = `<div class="suggestion-company">${escapeHtml(companyName)}</div>${position ? `<div class="suggestion-position">${escapeHtml(position)}</div>` : ""}`;
    item.addEventListener("click", () => selectOrderSuggestion(c?.id, companyName));
    suggestions.appendChild(item);
  }
  suggestions.style.display = "block";
}

function selectOrderSuggestion(caseId, companyName) {
  document.getElementById("recommendCaseId").value = String(caseId || "");
  document.getElementById("recommendCompanyInput").value = cleanCaptureText(companyName);
  const suggestions = document.getElementById("orderSuggestions");
  if (suggestions) suggestions.style.display = "none";
}

async function submitResumeRecommend() {
  if (BUSY) return;
  const resumeId = Number(document.getElementById("recommendResumeId")?.value || LAST_IMPORTED_TALENT_ID || 0);
  if (!resumeId) {
    showErr("请先录入人才库后再推荐");
    return;
  }
  const caseId = String(document.getElementById("recommendCaseId")?.value || "").trim();
  const companyName = String(document.getElementById("recommendCompanyInput")?.value || "").trim();
  const note = String(document.getElementById("recommendNote")?.value || "").trim();
  if (!companyName) {
    showErr("请输入公司名");
    return;
  }
  setButtonsBusy(true);
  try {
    const form = new FormData();
    form.append("resume_id", String(resumeId));
    if (caseId) form.append("case_id", caseId);
    form.append("company_name", companyName);
    if (note) form.append("note", note);
    await callApiForm("/resume-recommend", form);
    closeRecommendModal();
    showOk("推荐成功");
  } catch (e) {
    showErr(String(e?.message || e));
  } finally {
    setButtonsBusy(false);
  }
}

async function doImportWithDedupe() {
  if (BUSY) return;
  resetRecommendState();
  resetReportState();
  setButtonsBusy(true);
  try {
    saveApiBase();
    const resumeText = getResumeText();
    let parsedByText = null;
    if (resumeText && resumeText.length >= 20) {
      showInfo("正在解析简历文本...");
      parsedByText = await parseCandidateFromResumeText(resumeText, LAST_CANDIDATE || {});
      LAST_CANDIDATE = mergeCandidate(parsedByText, LAST_CANDIDATE);
      populateForm(parsedByText, true);
    }
    let candidate;
    try { candidate = readFormToCandidate(); } catch (e) { showErr(e.message); return; }
    if (parsedByText) candidate = mergeCandidate(candidate, parsedByText);
    candidate.resumeText = resumeText || normalizeResumeText(parsedByText?.resumeText || candidate.resumeText || "");
    if (!candidate.sourceSite && candidate.resumeText) candidate.sourceSite = "手动粘贴";
    LAST_CANDIDATE = candidate;
    showInfo("正在查重...");
    const dedupeData = await callApi("/plugin/dedupe/check", { candidate });
    const levelMap = { strong: "强匹配", medium: "中匹配", weak: "弱匹配", none: "无重复" };
    const matchLevel = dedupeData?.matchLevel || "none";
    const matchIds = Array.isArray(dedupeData?.matchedTalentIds) ? dedupeData.matchedTalentIds : [];
    if (matchLevel === "strong" || matchLevel === "medium") {
      showResult([
        { text: `查重结果：${levelMap[matchLevel]}`, cls: "r-warn" },
        { text: `已有人才ID：${matchIds.join(", ")}`, cls: "r-warn" },
        { text: dedupeData?.mergeSuggestion || "", cls: "r-info" },
        { text: "继续录入中...", cls: "r-info" }
      ]);
    } else {
      showInfo("无重复，正在录入...");
    }
    const remark = (document.getElementById("remark")?.value || "").trim();
    const importData = await callApi("/plugin/talents/import", { candidate, remark });
    LAST_IMPORTED_TALENT_ID = Number(importData?.talentId || 0) || 0;
    setReportResumeId(importData?.talentId || 0);
    setRecommendEnabled(Boolean(LAST_IMPORTED_TALENT_ID));
    const actionMap = { new: "新建", merge: "合并", update: "更新" };
    const lines = [];
    if (matchLevel !== "none") {
      lines.push({ text: `查重：${levelMap[matchLevel]}${matchIds.length ? "（ID:" + matchIds.join(",") + "）" : ""}`, cls: "r-warn" });
    }
    lines.push({ text: `录入成功 - ${actionMap[importData?.importAction] || "完成"}`, cls: "r-ok" });
    if (importData?.talentId) lines.push({ text: `人才ID：${importData.talentId}`, cls: "r-ok" });
    showResult(lines);
    try {
      await callApi("/plugin/audit/log", {
        action: "plugin_import",
        sourceSite: candidate.sourceSite,
        sourceCandidateId: candidate.sourceCandidateId,
        candidateName: candidate.name,
        payload: { candidate, remark }
      });
    } catch (_) {}
  } catch (e) {
    showErr(String(e?.message || e));
  } finally {
    setButtonsBusy(false);
  }
}

function init() {
  chrome.storage.local.get(["apiBase"], (res) => {
    if (res.apiBase) document.getElementById("apiBase").value = String(res.apiBase);
  });
  resetRecommendState();
  resetReportState();
  setupPluginUploadDropzone();
  document.getElementById("btnCapture")?.addEventListener("click", captureCandidate);
  document.getElementById("btnClipboard")?.addEventListener("click", doDedupeOnly);
  document.getElementById("btnImport")?.addEventListener("click", doImportWithDedupe);
  document.getElementById("btnRecommend")?.addEventListener("click", openRecommendModal);
  document.getElementById("btnGenerateReport")?.addEventListener("click", showGenerateReportModal);
  document.getElementById("btnRecommendClose")?.addEventListener("click", closeRecommendModal);
  document.getElementById("btnRecommendCancel")?.addEventListener("click", closeRecommendModal);
  document.getElementById("btnRecommendSubmit")?.addEventListener("click", submitResumeRecommend);
  document.getElementById("btnGenerateReportClose")?.addEventListener("click", closeGenerateReportModal);
  document.getElementById("btnGenerateReportCancel")?.addEventListener("click", closeGenerateReportModal);
  document.getElementById("btnConfirmGenerateReport")?.addEventListener("click", confirmGenerateReport);
  document.getElementById("btnUploadReportTemplate")?.addEventListener("click", () => {
    if (BUSY) return;
    document.getElementById("reportTemplateFile")?.click();
  });
  document.getElementById("reportTemplateFile")?.addEventListener("change", (e) => {
    uploadReportTemplate(e?.target);
  });
  document.getElementById("recommendModal")?.addEventListener("click", (e) => {
    if (e.target && e.target.id === "recommendModal") closeRecommendModal();
  });
  document.getElementById("generateReportModal")?.addEventListener("click", (e) => {
    if (e.target && e.target.id === "generateReportModal") closeGenerateReportModal();
  });
  document.addEventListener("click", (e) => {
    if (e.target && e.target.closest && e.target.closest(".order-autocomplete-wrapper")) return;
    const suggestions = document.getElementById("orderSuggestions");
    if (suggestions) suggestions.style.display = "none";
  });
}

document.addEventListener("DOMContentLoaded", init);
