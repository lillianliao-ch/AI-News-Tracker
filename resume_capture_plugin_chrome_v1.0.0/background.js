let popupWindowId = null;

function normalizeApiBase(v) {
  const raw = String(v || "").trim();
  if (!raw) return "";
  const withProtocol = /^https?:\/\//i.test(raw) ? raw : `http://${raw}`;
  return withProtocol.replace(/\/+$/, "");
}

function normalizeToken(v) {
  return String(v || "").trim().replace(/^Bearer\s+/i, "").replace(/^"+|"+$/g, "").trim();
}

function canonicalOrigin(url) {
  try {
    const normalized = normalizeApiBase(url);
    if (!normalized) return "";
    const parsed = new URL(normalized);
    let host = parsed.hostname.toLowerCase();
    if (host === "localhost") host = "127.0.0.1";
    const port = parsed.port || (parsed.protocol === "https:" ? "443" : "80");
    return `${parsed.protocol}//${host}:${port}`;
  } catch (_) {
    return "";
  }
}

function isSameOrigin(urlA, urlB) {
  return canonicalOrigin(urlA) !== "" && canonicalOrigin(urlA) === canonicalOrigin(urlB);
}

function extractOrigin(url) {
  try {
    return new URL(String(url || "")).origin;
  } catch (_) {
    return "";
  }
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

function isLoopbackApiBase(url) {
  try {
    const host = new URL(normalizeApiBase(url)).hostname.toLowerCase();
    return host === "127.0.0.1" || host === "localhost";
  } catch (_) {
    return false;
  }
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
          for (const v of direct) {
            if (typeof v === "string" && v.trim()) return v.trim();
          }
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
  } catch (_) {
    return "";
  }
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
    await chrome.storage.local.set({ apiBase: best.apiBase, token: best.token });
    return { apiBase: best.apiBase, token: best.token };
  }
  return { apiBase: preferredOrigin, token: "" };
}

async function resolveApiAuth(apiBase) {
  const base = normalizeApiBase(apiBase);
  const stored = await chrome.storage.local.get(["apiBase", "token"]);
  const storedBase = normalizeApiBase(stored?.apiBase || "");
  const cached = normalizeToken(stored?.token || "");
  const targetBase = storedBase || base;
  if (cached && targetBase && !isLoopbackApiBase(targetBase)) {
    return { apiBase: targetBase, token: cached };
  }
  if (!targetBase) {
    return await discoverApiAuth(base);
  }
  const tabs = await chrome.tabs.query({});
  for (const tab of tabs) {
    if (!tab?.id || !tab.url || !isSameOrigin(tab.url, targetBase)) continue;
    const token = await readTokenFromTab(tab.id);
    if (token) {
      await chrome.storage.local.set({ apiBase: targetBase, token });
      return { apiBase: targetBase, token };
    }
  }
  const discovered = await discoverApiAuth(targetBase);
  if (discovered?.apiBase && discovered?.token) {
    return discovered;
  }
  if (cached) {
    return { apiBase: targetBase, token: cached };
  }
  return discovered;
}

async function resolveApiToken(apiBase) {
  const auth = await resolveApiAuth(apiBase);
  return normalizeToken(auth?.token || "");
}

chrome.runtime.onInstalled.addListener(() => {
  chrome.storage.local.get(["apiBase", "bossAutomationEnabled"], (res) => {
    const next = {};
    if (!res.apiBase) next.apiBase = "http://127.0.0.1:8000";
    if (typeof res.bossAutomationEnabled !== "boolean") next.bossAutomationEnabled = true;
    if (Object.keys(next).length) chrome.storage.local.set(next);
  });
});

chrome.runtime.onStartup.addListener(() => {
  chrome.storage.local.get(["apiBase"], async (res) => {
    const apiBase = normalizeApiBase(res?.apiBase || "http://127.0.0.1:8000");
    if (!res?.apiBase) await chrome.storage.local.set({ apiBase });
  });
});

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (!message || !message.type) return false;
  if (message.type === "resolveApiToken") {
    resolveApiToken(message.apiBase).then((token) => {
      sendResponse({ ok: Boolean(token), token });
    }).catch((e) => {
      sendResponse({ ok: false, error: String(e?.message || e || "") });
    });
    return true;
  }
  if (message.type === "getBossRunnerConfig") {
    chrome.storage.local.get(["apiBase", "token", "bossAutomationEnabled"], async (res) => {
      try {
        const apiBase = normalizeApiBase(res?.apiBase || "http://127.0.0.1:8000");
        let token = normalizeToken(res?.token || "");
        let resolvedBase = apiBase;
        if (!token || !apiBase || isLoopbackApiBase(apiBase)) {
          const resolved = await resolveApiAuth(apiBase);
          resolvedBase = normalizeApiBase(resolved?.apiBase || apiBase || "http://127.0.0.1:8000");
          token = normalizeToken(resolved?.token || token);
        }
        sendResponse({
          ok: true,
          apiBase: resolvedBase,
          token,
          bossAutomationEnabled: res?.bossAutomationEnabled !== false
        });
      } catch (e) {
        sendResponse({ ok: false, error: String(e?.message || e || "") });
      }
    });
    return true;
  }
  if (message.type === "setBossRunnerEnabled") {
    chrome.storage.local.set({ bossAutomationEnabled: message.enabled !== false }).then(() => {
      sendResponse({ ok: true, bossAutomationEnabled: message.enabled !== false });
    }).catch((e) => {
      sendResponse({ ok: false, error: String(e?.message || e || "") });
    });
    return true;
  }
  return false;
});

chrome.action.onClicked.addListener(async () => {
  if (popupWindowId !== null) {
    try {
      const w = await chrome.windows.get(popupWindowId);
      if (w) {
        chrome.windows.update(popupWindowId, { focused: true });
        return;
      }
    } catch (_) {
      popupWindowId = null;
    }
  }
  const display = await chrome.system.display.getInfo();
  const primary = display && display[0] ? display[0] : null;
  const screenW = primary ? primary.workArea.width : 1920;
  const screenH = primary ? primary.workArea.height : 1080;
  const winW = 410;
  const top = 60;
  const preferredH = 900;
  const availableH = Math.max(1, screenH - top - 20);
  const winH = Math.min(preferredH, availableH);
  const left = Math.max(0, screenW - winW - 20);
  const win = await chrome.windows.create({
    url: chrome.runtime.getURL("popup.html"),
    type: "popup",
    width: winW,
    height: winH,
    left,
    top
  });
  popupWindowId = win.id;
});

chrome.windows.onRemoved.addListener((id) => {
  if (id === popupWindowId) popupWindowId = null;
});
