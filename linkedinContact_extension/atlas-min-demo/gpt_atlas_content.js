console.log("✅ Atlas content script loaded");

let lastText = "";
let stableTimer = null;

const observer = new MutationObserver(() => {
  const blocks = document.querySelectorAll(".markdown");
  if (!blocks.length) return;

  const latest = blocks[blocks.length - 1];
  const text = latest.innerText.trim();

  if (!text || text === lastText) return;

  lastText = text;

  clearTimeout(stableTimer);
  stableTimer = setTimeout(() => {
    chrome.runtime.sendMessage({
      type: "ATLAS_REPLY",
      text: lastText
    });
  }, 1000);
});

observer.observe(document.body, {
  childList: true,
  subtree: true
});

chrome.runtime.onMessage.addListener(msg => {
  if (msg.type !== "SEND_PROMPT") return;

  const textarea = document.querySelector("textarea");
  if (!textarea) {
    console.error("❌ 找不到 ChatGPT 输入框");
    return;
  }

  textarea.value = msg.prompt;
  textarea.dispatchEvent(new Event("input", { bubbles: true }));

  setTimeout(() => {
    const sendBtn = document.querySelector(
      'button[data-testid="send-button"]'
    );
    if (!sendBtn) {
      console.error("❌ 找不到发送按钮");
      return;
    }
    sendBtn.click();
  }, 200);
});