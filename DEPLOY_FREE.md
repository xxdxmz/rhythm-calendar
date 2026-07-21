# 免费公开部署

推荐架构：Netlify 只部署 Vue 前端，GitHub Actions 每 6 小时匿名抓取一次，最新 JSON 由 GitHub Pages 托管。采集不会提交代码，因此不会反复触发 Netlify 生产部署，也不需要 Cookie、在线数据库或常驻服务器。

## GitHub 数据服务

1. 将项目放入一个公开 GitHub 仓库。
2. 在 `Settings → Pages → Build and deployment → Source` 选择 `GitHub Actions`。
3. 在 `Actions` 中手动运行一次 `Update public dynamics data`。
4. 本项目的数据地址为 `https://xxdxmz.github.io/rhythm-calendar/data/snapshot.json`。

若 GitHub 公共 Runner 被 Bilibili 风控，工作流会发布仓库内最后一份非空快照，
并在 `status` 中标记 `stale: true` 和错误原因，不会发布空数据或伪造更新时间。
GitHub 机房 IP 是否可访问 Bilibili 并不稳定；要稳定自动更新，需要使用家庭网络中的
自托管 Runner，或者后续接入另一个合法公开数据源。

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
