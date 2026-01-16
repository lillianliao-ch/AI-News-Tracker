console.log("✅ Atlas Min Demo background loaded");

function sendPromptToAtlas(prompt) {
  chrome.tabs.query(
    {
      url: [
        "https://chat.openai.com/*",
        "https://chatgpt.com/*"
      ]
    },
    tabs => {
      if (!tabs.length) {
        console.error("❌ 请先打开 ChatGPT Atlas 页面");
        return;
      }

      chrome.tabs.sendMessage(tabs[0].id, {
        type: "SEND_PROMPT",
        prompt
      });
    }
  );
}

setTimeout(() => {
  sendPromptToAtlas("请只回复一句话：Atlas demo OK");
}, 2000);

chrome.runtime.onMessage.addListener(msg => {
  if (msg.type === "ATLAS_REPLY") {
    console.log("🎉 收到 ChatGPT 回复：");
    console.log(msg.text);
  }
});