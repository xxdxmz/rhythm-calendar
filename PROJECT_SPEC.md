# Rhythm Calendar - 音乐游戏更新日历项目说明

## 1. 项目简介

这是一个面向音乐游戏玩家的更新日历网站。

目标：自动获取指定音乐游戏官方账号在 Bilibili 发布的动态，分析公告内容，提取版本更新、曲包、新曲、联动等事件，并以日历形式展示。

网站不需要用户登录，游戏列表固定，由后台维护。

## 2. 支持游戏

第一阶段支持 Arcaea、maimai でらっくす、范式：起源、Muse Dash、Phigros、Rotaeno 和 Lanota。

## 3. 核心功能

- 定时获取官方账号最新动态、保存原始动态、自动去重并更新数据库。
- 从公告文本提取日期、事件类型和标题。
- 以月历、周历、游戏筛选和最新动态列表展示结果。

## 4. 技术栈

- 前端：Vue 3、TypeScript、Vite、Pinia、Axios、FullCalendar、Element Plus
- 后端：Python、FastAPI、SQLAlchemy、APScheduler
- 数据库：开发使用 SQLite，生产使用 PostgreSQL
- 部署：Docker、Nginx、PostgreSQL、Redis

## 5. 后端结构

```text
backend/
├── main.py
├── bilibili/
│   ├── client.py
│   ├── parser.py
│   └── models.py
├── fetchers/
│   └── arcaea.py
├── parser/
│   ├── event_parser.py
│   └── rules/
├── models/
└── scheduler/
```

## 6. 数据库设计

- `games`：id, name, display_name, icon, theme_color, enabled
- `official_accounts`：id, game_id, platform, uid, name, enabled, last_dynamic_id
- `dynamics`：id, account_id, dynamic_id, title, content, dynamic_type, publish_time, url, created_at；dynamic_id 唯一
- `events`：id, game_id, dynamic_id, title, description, event_type, event_date, status, created_at

事件类型：`VERSION_UPDATE`、`PACK_RELEASE`、`SONG_ADD`、`COLLABORATION`、`EVENT`、`MAINTENANCE`。

## 7. Bilibili 模块

`BilibiliClient.get_user_dynamic(uid)` 请求 Bilibili 接口、保存原始 JSON，并转换为统一 `Dynamic` 对象。

统一模型字段：dynamic_id、uid、text、publish_time、url、dynamic_type。

## 8. 解析原则

动态文本依次经过日期提取、关键词匹配、事件类型判断，最终生成 GameEvent。Bilibili 获取模块与游戏解析模块分离；原始动态必须保存；不直接依赖单一接口；解析失败的数据进入人工审核；先完成 Arcaea 闭环，再扩展其他游戏。

## 9. API

- `GET /api/games`
- `GET /api/events?start=&end=&game_id=`
- `GET /api/dynamics/latest`

## 10. 当前第一任务

实现 Arcaea 官方 Bilibili 动态获取，保存原始 JSON，并输出最近 10 条动态文本。不要先做前端，先验证数据来源。
