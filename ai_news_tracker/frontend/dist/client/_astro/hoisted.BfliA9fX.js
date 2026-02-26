async function y(){try{const s=await(await fetch("http://localhost:8000/api/stats")).json(),t=document.getElementById("totalNews"),n=document.getElementById("todayNews");t&&(t.textContent=s.total_news||0),n&&(n.textContent=s.today_news||0)}catch(o){console.error("加载统计失败:",o)}}y();setInterval(y,3e4);window.addEventListener("news-updated",o=>{const i=document.getElementById("newsGrid");i&&o.detail&&(i.innerHTML="",o.detail.forEach(s=>{const t=document.createElement("div");t.className="news-card",t.style.cssText=`
        background: white;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
        transition: all 0.2s ease;
      `;const n=document.createElement("h3");n.textContent=s.title,n.style.cssText=`
        font-size: 16px;
        font-weight: 600;
        margin: 0 0 12px 0;
        color: #1a1a1a;
        line-height: 1.4;
      `;const a=document.createElement("p");a.textContent=s.summary?.substring(0,150)+"..."||"",a.style.cssText=`
        font-size: 14px;
        color: #666;
        line-height: 1.6;
        margin: 0;
      `;const e=document.createElement("div");e.style.cssText=`
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 16px;
        font-size: 12px;
        color: #999;
      `;const r=document.createElement("span");r.textContent=s.source||"";const d=document.createElement("span");d.textContent=s.category||"",d.style.cssText=`
        background: #f0f0f0;
        padding: 4px 12px;
        border-radius: 12px;
      `,e.appendChild(r),e.appendChild(d),t.appendChild(n),t.appendChild(a),t.appendChild(e),i.appendChild(t)}))});window.addEventListener("news-appended",o=>{const i=document.getElementById("newsGrid");i&&o.detail&&o.detail.forEach(s=>{const t=document.createElement("div");t.className="news-card",t.style.cssText=`
        background: white;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
        transition: all 0.2s ease;
      `;const n=document.createElement("h3");n.textContent=s.title,n.style.cssText=`
        font-size: 16px;
        font-weight: 600;
        margin: 0 0 12px 0;
        color: #1a1a1a;
        line-height: 1.4;
      `;const a=document.createElement("p");a.textContent=s.summary?.substring(0,150)+"..."||"",a.style.cssText=`
        font-size: 14px;
        color: #666;
        line-height: 1.6;
        margin: 0;
      `;const e=document.createElement("div");e.style.cssText=`
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 16px;
        font-size: 12px;
        color: #999;
      `;const r=document.createElement("span");r.textContent=s.source||"";const d=document.createElement("span");d.textContent=s.category||"",d.style.cssText=`
        background: #f0f0f0;
        padding: 4px 12px;
        border-radius: 12px;
      `,e.appendChild(r),e.appendChild(d),t.appendChild(n),t.appendChild(a),t.appendChild(e),i.appendChild(t)})});const p=document.getElementById("refreshBtn"),m=document.getElementById("lastUpdate");p.addEventListener("click",async()=>{p.disabled=!0,p.classList.add("spinning");try{const i=await(await fetch("http://localhost:8000/api/crawl",{method:"POST"})).json();setTimeout(()=>{window.location.reload()},3e3)}catch(o){console.error("刷新失败:",o),p.disabled=!1,p.classList.remove("spinning"),alert("刷新失败，请稍后重试")}});async function u(){try{const i=await(await fetch("http://localhost:8000/api/stats")).json();if(i.last_crawl){const s=new Date(i.last_crawl),n=Math.floor((new Date-s)/6e4);n<1?m.textContent="刚刚更新":n<60?m.textContent=`${n}分钟前更新`:m.textContent=s.toLocaleString("zh-CN",{month:"short",day:"numeric",hour:"2-digit",minute:"2-digit"})}}catch(o){console.error("获取更新时间失败:",o)}}u();setInterval(u,6e4);document.addEventListener("astro:page-load",()=>{document.querySelectorAll(".generate-btn").forEach(s=>{s.addEventListener("click",async t=>{const n=t.target.dataset.newsId;if(!n){alert("新闻 ID 不存在");return}if(t.target.disabled)return;const a=document.getElementById(`result-${n}`),e=document.getElementById(`result-content-${n}`),r=t.target.textContent;t.target.textContent="⏳ 生成中...",t.target.disabled=!0,t.target.style.cursor="not-allowed",t.target.style.opacity="0.6",a&&(a.style.display="block",e&&(e.innerHTML=`
            <div style="text-align: center; padding: 20px;">
              <div style="color: #667eea; font-size: 14px; margin-bottom: 8px;">
                ⏳ 正在调用 AI 生成文案...
              </div>
              <div style="color: #999; font-size: 12px;">
                这可能需要 10-30 秒，请耐心等待
              </div>
              <div style="margin-top: 12px;">
                <div style="display: inline-block; width: 20px; height: 20px; border: 2px solid #f3f3f3; border-top: 2px solid #667eea; border-radius: 50%; animation: spin 1s linear infinite;"></div>
              </div>
            </div>
            <style>
              @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
              }
            </style>
          `));try{const g=await fetch("http://localhost:8000/api/generate",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({news_id:n,versions:["A","B","C"]})});if(g.ok){const c=await g.json();if(c&&c.length>0){let x="";c.forEach((l,f)=>{const h={A:"硬核技术风",B:"轻松科普风",C:"热点观点风"};x+=`
                <div style="margin-bottom: 16px; padding-bottom: 16px; border-bottom: 1px dashed #ddd;">
                  <div class="title">版本 ${l.version} - ${h[l.version]}</div>
                  <div class="content">${l.content}</div>
                  <div class="hashtags">${l.hashtags?l.hashtags.join(" "):""}</div>
                </div>
              `}),e&&(e.innerHTML=x),t.target.textContent="✅ 生成成功",setTimeout(()=>{t.target.textContent=r,t.target.disabled=!1,t.target.style.cursor="pointer",t.target.style.opacity="1"},2e3)}else e&&(e.innerHTML='<p style="color: #dc3545;">❌ 生成失败：未返回内容</p>'),t.target.textContent=r,t.target.disabled=!1,t.target.style.cursor="pointer",t.target.style.opacity="1"}else{const c=await g.json();e&&(e.innerHTML=`<p style="color: #dc3545;">❌ 生成失败：${c.detail||"未知错误"}</p>`),t.target.textContent=r,t.target.disabled=!1,t.target.style.cursor="pointer",t.target.style.opacity="1"}}catch(d){console.error("生成错误:",d),e&&(e.innerHTML=`<p style="color: #dc3545;">❌ 生成失败：${d.message}</p>`),t.target.textContent=r,t.target.disabled=!1,t.target.style.cursor="pointer",t.target.style.opacity="1"}})}),document.querySelectorAll(".copy-btn").forEach(s=>{s.addEventListener("click",t=>{const n=t.target.dataset.target,a=document.getElementById(n);if(a){const e=a.innerText||a.textContent;navigator.clipboard.writeText(e).then(()=>{const r=t.target.textContent;t.target.textContent="✅ 已复制",t.target.classList.add("copied"),setTimeout(()=>{t.target.textContent=r,t.target.classList.remove("copied")},2e3)}).catch(r=>{console.error("复制失败:",r),alert("复制失败，请手动复制")})}})})});
