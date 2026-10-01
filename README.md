# 20-giftwrap（礼品包装纸）

Giftwrap — 盒体展开近似面积（含重叠余量系数）

## 启动

```bash
docker compose up --build
```

| 入口 | 地址 |
| --- | --- |
| 前端 | http://localhost:4900 |
| API | http://localhost:9900 |

## 主链

选盒 + 选纸卷 → 包装纸面积 paper_m² → 卷宽下料（sheet_len = paper_m² ÷ roll_width，sheets = ⌈sheet_len⌉，单张长按 1m）→ 展开示意 → 写入用纸档

- 算纸必须绑定纸卷 id；未选卷或卷宽 ≤ 0 直接校验失败，不写入 calc_runs。
- 落库 result_json 钉住写入时的 paper_id / paper_name / roll_width / sheet_len / sheets；事后在纸张页改卷宽，用纸档列表与详情仍按写入值回看，不重切。
- 用纸档详情以「同卷同盒再干算」与落库互证；切换卷材后算纸台新单的张数随新卷宽变化。

## 技术栈

Python 3.12 + FastAPI + SQLite；Vue 3 + Vite + Nginx。
