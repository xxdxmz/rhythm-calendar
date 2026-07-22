# 免费公开部署

推荐架构：Netlify 只部署 Vue 前端，本地 Windows 计划任务每 6 小时匿名抓取一次并提交快照，最新 JSON 由 GitHub Pages 托管。纯数据提交不会触发 Netlify 生产部署，不需要 Cookie或在线数据库。

## GitHub 数据服务

1. 将项目放入一个公开 GitHub 仓库。
2. 在 `Settings → Pages → Build and deployment → Source` 选择 `GitHub Actions`。
3. 在 `Actions` 中手动运行一次 `Update public dynamics data`。
4. 本项目的数据地址为 `https://xxdxmz.github.io/rhythm-calendar/data/snapshot.json`。

GitHub Actions 不再访问 Bilibili，只发布本地采集器提交的非空快照，避免 GitHub
机房 IP 的 `412` 风控。采集失败时本地任务不会提交空数据，线上继续保留上次成功结果。

## Netlify 前端

从该 GitHub 仓库导入站点，根目录的 `netlify.toml` 已包含构建配置。添加环境变量：

```text
VITE_STATIC_DATA_URL=https://xxdxmz.github.io/rhythm-calendar/data/snapshot.json
```

该变量已经写入 `netlify.toml`，通常不需要在 Netlify 后台重复填写。部署一次后，动态数据更新不会触发 Netlify 部署；只有前端代码变化时才需要重新部署。

## 本地静态兜底

```powershell
.venv\Scripts\python -m backend.export_static --from-cache --output frontend/public/data/snapshot.json
```

未设置 `VITE_STATIC_DATA_URL` 时，前端会先尝试本地 API，失败后读取该文件。
