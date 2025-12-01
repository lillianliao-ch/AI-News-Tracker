import os
import io
import time
import json
import tempfile
from typing import List, Tuple

import gradio as gr
import requests
import pandas as pd


SERVICE_BASE = os.getenv("LINKEDIN_SERVICE_BASE", "http://127.0.0.1:8001")


def parse_one(url: str, provider: str = "contactout") -> Tuple[dict, str]:
    endpoint = f"{SERVICE_BASE}/parse/pretty"
    payload = {"url": url}
    if provider:
        payload["provider"] = provider
    r = requests.post(endpoint, json=payload, timeout=90)
    if r.status_code != 200:
        try:
            detail = r.json().get("detail")
        except Exception:
            detail = r.text
        return {}, f"ERROR: {detail}"
    return r.json(), "OK"


def run_batch(urls_text: str, provider: str) -> Tuple[str, str]:
    urls = [u.strip() for u in urls_text.splitlines() if u.strip()]
    profiles, exps, edus, errors = [], [], [], []

    for u in urls:
        res, status = parse_one(u, provider)
        if status != "OK":
            errors.append({"url": u, "error": status})
            continue
        name = res.get("name")
        headline = res.get("headline")
        location = res.get("location")
        profiles.append({"url": u, "name": name, "headline": headline, "location": location})
        for e in res.get("text", "").splitlines()[:1]:
            _ = e  # keep
        for exp in res.get("experiences", []) if False else []:
            exps.append({"url": u, **exp})
        # 从服务的 pretty 接口没有直接带 experiences 列表，改从 /parse 拿一次结构化
        r2 = requests.post(f"{SERVICE_BASE}/parse", json={"url": u, "provider": provider}, timeout=90)
        if r2.status_code == 200:
            data = r2.json()
            for exp in data.get("experiences", []) or []:
                exps.append({"url": u, **exp})
            for edu in data.get("educations", []) or []:
                edus.append({"url": u, **edu})
        else:
            errors.append({"url": u, "error": f"parse structure failed: {r2.text}"})

    # 写 Excel 到内存
    with io.BytesIO() as bio:
        with pd.ExcelWriter(bio, engine="openpyxl") as writer:
            pd.DataFrame(profiles or [{"url": "", "name": "", "headline": "", "location": ""}]).to_excel(writer, index=False, sheet_name="Profile")
            pd.DataFrame(exps or [{"url": "", "company": "", "title": "", "start_date": "", "end_date": "", "is_current": "", "location": "", "summary": ""}]).to_excel(writer, index=False, sheet_name="Experiences")
            pd.DataFrame(edus or [{"url": "", "school": "", "degree": "", "field_of_study": "", "start_year": "", "end_year": "", "description": ""}]).to_excel(writer, index=False, sheet_name="Educations")
            if errors:
                pd.DataFrame(errors).to_excel(writer, index=False, sheet_name="Errors")
        bio.seek(0)
        data = bio.getvalue()
    # 写入临时文件并返回路径
    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
        tmp.write(data)
        temp_path = tmp.name
    return "批处理完成", temp_path


with gr.Blocks(title="LinkedIn Batch Parser (DeepAgents style)") as demo:
    gr.Markdown("# LinkedIn Batch Parser\n输入多条 LinkedIn /in/ 链接，每行一条。选择数据源后开始批处理。")
    with gr.Row():
        urls = gr.Textbox(label="LinkedIn URLs", lines=10, placeholder="https://www.linkedin.com/in/xxx\nhttps://www.linkedin.com/in/yyy")
        provider = gr.Dropdown(choices=["contactout", "serpapi", "browser"], value="contactout", label="Provider")
    run_btn = gr.Button("Run Batch")
    status = gr.Textbox(label="Status")
    file = gr.File(label="Excel")

    run_btn.click(run_batch, inputs=[urls, provider], outputs=[status, file])


if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)


