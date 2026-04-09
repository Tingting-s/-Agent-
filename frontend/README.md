# Frontend Demo

这是一个基于 React + Vite 的单页前端演示页面，用来调用当前 FastAPI 后端的 `POST /tasks/execute` 接口。

## 安装

```bash
cd frontend
npm install
```

## 运行

```bash
npm run dev
```

默认会启动 Vite 开发服务器，通常访问地址为 `http://127.0.0.1:5173`。

## 构建

```bash
npm run build
```

## 代理说明

前端不会在组件里写死完整后端地址。

页面实际请求地址是：

```text
/api/tasks/execute
```

在 `vite.config.js` 中，`/api` 前缀会统一代理到：

```text
http://127.0.0.1:8000
```

所以这条请求最终会被转发到：

```text
http://127.0.0.1:8000/tasks/execute
```

所以请先确保后端已经通过下面方式启动：

```bash
python run.py
```

## 支持的 4 类任务

1. `email_draft`
2. `meeting_extraction`
3. `document_summary`
4. `weather_query`

## 最简使用说明

1. 启动后端：`python run.py`
2. 进入前端目录：`cd frontend`
3. 安装依赖：`npm install`
4. 启动前端：`npm run dev`
5. 打开页面后，在左侧切换任务类型
6. 直接使用表单内默认演示值，点击“提交请求”
7. 在右侧查看友好展示结果，并可展开“查看原始 JSON”

## 说明

- `document_summary` 的默认演示值使用 `data/sample_doc.md`，实际调用时请确保这个路径在后端运行目录下可读取。
- 页面会分别处理 `success`、`error`、`need_more_info` 三种状态。
- 天气查询仍然依赖后端现有天气工具逻辑，不会在前端伪造数据。
