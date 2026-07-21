# Rhythm Calendar

当前里程碑只实现 Arcaea 官方 Bilibili 动态采集，不包含前端。

## 运行

```powershell
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python -m backend.fetchers.arcaea --limit 10
```

未配置密钥时，采集器只建立匿名访客会话。成功响应保存在 `data/raw/arcaea/` 并写入 SQLite；命令行输出最近 10 条动态文本。风控响应也会以 `*.error.json` 保存，已有缓存时自动退回上次成功数据。

## 专用低权限采集账号

不要使用个人主账号。注册一个不投稿、不充值、不私信的专用账号，在浏览器登录后复制请求中的完整 Cookie，并只写入本地密钥文件：

```powershell
New-Item -ItemType Directory -Force secrets
notepad secrets\bilibili_cookie.txt
```

文件内容格式类似 `SESSDATA=...; bili_jct=...; DedeUserID=...`，不要加引号。然后设置：

```powershell
$env:BILIBILI_COOKIE_FILE = 'secrets/bilibili_cookie.txt'
.venv\Scripts\python -m backend.fetchers.arcaea --limit 10
```

`secrets/`、`.env` 和数据库均已被 Git 忽略。Cookie 只由后端读取，不会通过 API、日志或错误响应输出。生产环境应使用 Docker/Kubernetes/托管平台的 Secret 文件挂载，并定期轮换凭证。退出该账号或在 Bilibili 安全设置中撤销会话即可使旧 Cookie 失效。

启动 API：

```powershell
.venv\Scripts\uvicorn backend.main:app --reload
```

`GET /api/dynamics/latest?limit=10` 只读取 SQLite 缓存，不会让网站访客触发 Bilibili 请求。后台默认每小时匿名更新一次，`GET /api/dynamics/status` 可检查数据是否过期。官方账号 UID 为 `404145357`。

当轻量 API 返回空正文或触发风控时，采集器会自动启动无登录 Chromium，从渲染后的动态卡片补全正文。Windows 会自动发现 Chrome 或 Edge；Linux/Docker 环境设置 `BILIBILI_BROWSER_EXECUTABLE` 指向已安装的 Chromium。浏览器采集结果保存在 `data/raw/arcaea/browser/`。

## 网站与部署

本地同时启动前后端：

```powershell
.venv\Scripts\uvicorn backend.main:app --reload
cd frontend
npm install
npm run dev
```

前端可部署到 Netlify，根目录的 `netlify.toml` 已配置 `frontend` 为构建目录。在 Netlify 设置环境变量：

```text
VITE_API_BASE_URL=https://你的后端域名
```

后端必须部署到支持长期运行 Docker 和持久卷的平台，使用根目录 `Dockerfile`。同时设置：

```text
CORS_ORIGINS=https://你的站点.netlify.app
```

SQLite 版本要求把 `/app/data` 挂载为持久卷。正式扩展到多实例前应迁移至 PostgreSQL，并确保只有一个调度器实例执行采集。
