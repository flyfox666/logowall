# Logo Wall · 客户品牌墙

[English](README.md) | **简体中文**

展示客户品牌墙的自托管小产品：前台品牌墙 + 管理后台 + 海报导出 + 全量备份 +
多用户登录 + 主题换肤。适合活动现场大屏、办公室展示与团队 Demo。

---

## 目录

- [截图](#截图)
- [功能](#功能)
- [快速开始](#快速开始)
  - [本地运行（Python 3.9+）](#本地运行python-39)
  - [Docker 运行](#docker-运行)
- [架构：代码与数据分离](#架构代码与数据分离)
- [全量备份导出/导入](#全量备份导出导入)
- [批量导入数据（Excel）](#批量导入数据excel)
- [Logo 获取与匹配](#logo-获取与匹配)
- [配置](#配置)
- [新业务线接入指南](#新业务线接入指南)
- [演示数据生成器](#演示数据生成器)
- [目录结构](#目录结构)
- [开源协议](#开源协议)

---

## 截图

| 品牌墙 | 海报导出 |
|---|---|
| ![前台](opensource/docs/screenshots/front.png) | ![海报](opensource/docs/screenshots/poster-export.png) |

| 管理后台 |
|---|
| ![管理后台](opensource/docs/screenshots/admin.png) |

## 功能

- **品牌墙前台** — 响应式客户网格，按分公司、业务线、区域、负责人、合作年份
  分组展示，支持实时搜索。筛选维度可**自由组合**：同一维度内多选为「或」
  （OR），不同维度之间为「与」（AND），并提供一键「清除筛选」。负责人采用
  **可搜索的多选下拉框**，即便几十人也不会让工具栏臃肿。
- **合作时间** — 每个客户可记录开始/成交合作时间。它会显示在品牌墙卡片上、
  打印到导出的海报中、可按「合作年份」筛选，并能通过 Excel 导入导出完整往返。
- **管理后台**（`/admin`）— 客户新增 / 编辑 / 删除、Excel 导入导出、Logo 自动
  抓取（Clearbit / Google favicon / DuckDuckGo）、Logo 上传与公共 Logo 库。
- **海报导出** — 把当前筛选结果一键导出为 PNG 海报（竖版 3:4 / 大屏 16:9 /
  A4 @300dpi）。
- **全量备份** — 一键导出 / 导入全部数据（客户 + Logo 文件 + 用户账户）为单个
  zip，跨环境迁移无需手工操作数据库。
- **多用户登录** — 登录页支持 `admin` / `viewer` 两种角色；访客只能浏览，
  管理员可维护数据。原 `ADMIN_TOKEN` 仍作为 API 调用的主令牌兜底。
- **主题换肤** — 5 套预置配色 × 4 种背景纹理，访客可在工具栏调色盘预览，
  管理后台「站点设置」可配置全站默认主题与自定义配色。
- **站点配置** — 标题、英文副标题、标语、页脚均可在管理后台修改。
- **中英文切换** — 前台与管理后台右上角一键切换整站语言（各自独立记忆）。
- **缺 Logo 提醒** — 管理后台统计卡展示未配置 Logo 的客户数量，点击即可列出。

## 快速开始

### 本地运行（Python 3.9+）

```bash
cd opensource/local
# Windows
start.bat
# macOS / Linux
./start.sh
```

启动后打开 http://localhost:8080/ （管理后台 http://localhost:8080/admin，
默认账户 `admin / admin123`，登录后请在「用户管理」中修改密码；`ADMIN_TOKEN`
仅用于 API 调用）。

### Docker 运行

```bash
cd opensource/docker
docker compose up -d --build
```

客户数据与上传的 Logo 持久化在 `logo-wall-data` 卷中。公网部署（Cloudflare
Tunnel）见 [opensource/docker/README.zh-CN.md](opensource/docker/README.zh-CN.md)。

## 架构：代码与数据分离

所有运行时数据都存放在 `DATA_DIR` 指向的单一目录中：

```
DATA_DIR/
├── data.json     # 客户、站点设置、筛选项缓存
├── logos/        # 上传的 Logo 文件
└── users.json    # 登录账户（admin / viewer 角色）
```

代码与数据彻底分离。把 `DATA_DIR` 指向任意目录，同一份代码即可服务另一套
数据 —— 无需复制代码、无需同步脚本：

```bash
# 同一份代码，环境 A
DATA_DIR=/srv/logo-wall-a ./start.sh
# 同一份代码，环境 B
DATA_DIR=/srv/logo-wall-b ./start.sh
```

Docker 同理：把宿主机任意目录挂载到 `/data` 并设置 `DATA_DIR=/data`
（见 `opensource/docker/docker-compose.yml`）。

`DATA_DIR` 为空时应用会自动初始化：创建空的 `data.json`，并在首次运行时生成
默认管理员（`admin / admin123`）。

## 全量备份导出/导入

管理后台工具栏提供「导出备份 / 导入备份」按钮（API：`GET /api/backup/export`、
`POST /api/backup/import`）。

- **导出**：下载 `logo-wall-backup-年月日-时分秒.zip`，内含 `data.json` +
  `logos/` + `users.json` + 记录了条数与时间戳的 `manifest.json`。
- **导入**：校验 zip 后替换客户数据与用户账户、合并 Logo 文件（防 zip-slip
  攻击，大小受 `BACKUP_MAX_MB` 限制）。

典型用途：本地 ↔ Docker 迁移、向新团队移交数据、定期离线备份。

## 批量导入数据（Excel）

无需逐条录入——在 Excel 里整理好客户清单，管理后台工具栏点「导入Excel」
一次性导入。

导出文件包含以下列（**导入时按表头名称识别，列的先后顺序无关**，并兼容常见
别名）：

| 表头 | 必填 | 内容 |
|---|---|---|
| `租客/买方`（公司 / 客户 / 品牌） | 是 | 公司名称（初始同时作为品牌名） |
| `办公室（城市）`（办公室 / 城市代码） | 否 | 办公室代码（如 `SHA`，城市 / 区域自动推导） |
| `区域` | 否 | 区域（通常由办公室代码推导） |
| `申报部门（合并）`（业务线 / 部门） | 否 | 业务线（分号/逗号分隔） |
| `业务负责人（合并）`（负责人） | 否 | 负责人（分号/逗号分隔） |
| `合作时间`（开始合作时间 / 成交时间） | 否 | 合作日期，尽量规范化为 `YYYY-MM-DD` |

- 导入按表头**名称**而非位置识别列，并接受多种常见叫法（例如公司列兼容
  「公司」「客户」「品牌」；日期列兼容「开始合作时间」「成交时间」
  `cooperation_date`）；表头无法识别时回退到按位置读取。
- 日期兼容多种格式（Excel 日期序列号、`2024/1/2`、`2024-01-02`、
  `2024年1月2日` 等），统一规范化为 `YYYY-MM-DD`。
- 导入时会自动从内置品牌关键词库匹配 Logo，未匹配的客户可后续补配。
- 「导出Excel」生成同样格式的文件，编辑后再导入，形成可靠的往返闭环。
- 也可脚本调用：`POST /api/import-excel`（Bearer 令牌认证）。

## Logo 获取与匹配

在客户编辑弹窗里有三种方式配置 Logo：

1. **自动发现** — 填写公司网址（或仅公司名）后点「自动发现Logo」。应用会
   依次查询 Clearbit、Google favicon、DuckDuckGo 图标服务及内置品牌库，
   校验候选图标可访问后，以缩略图预览供选择。
2. **本地上传** — 选择本地图片文件（PNG / JPG / GIF / WebP / SVG）。
3. **粘贴 URL** — 直接填入图片地址。

**Logo 库** — 所有 Logo（上传或抓取）都进入共享 Logo 库：支持批量上传多个
文件，相同内容的文件自动去重，每个 Logo 显示被哪些客户使用，使用中的 Logo
不可删除；编辑客户时可从库中直接选用。

**缺 Logo 提醒** — 管理后台统计卡显示未配 Logo 的客户数量，点击即可列出，
也可在客户表格用「Logo：未配」筛选。

## 配置

| 环境变量 | 默认值 | 说明 |
|-------------|------------|----------------------------------|
| `PORT`      | `8080`     | HTTP 端口 |
| `HOST`      | `0.0.0.0`  | 监听地址（`127.0.0.1` = 仅本机） |
| `ADMIN_TOKEN` | `admin123` | API 调用主令牌（页面登录请用账号） |
| `AUTH_ENABLED` | `true`   | 登录页开关（多用户认证） |
| `JWT_SECRET` | 自动派生 | 登录会话密钥；设置固定值后重启不掉登录态 |
| `JWT_EXPIRE_DAYS` | `7`   | 登录会话有效期（天） |
| `DATA_DIR`  | 应用目录 | `data.json` / `logos/` / `users.json` 的位置 |
| `MAX_UPLOAD_MB` | `5`    | Logo 上传大小上限 |
| `BACKUP_MAX_MB` | `200`  | 导入备份 zip 的大小上限 |
| `IMGPROXY_MAX_MB` | `8`  | 海报抓图代理单张上限 |
| `IMGPROXY_TIMEOUT` | `10`| 海报抓图代理超时（秒） |
| `LOG_LEVEL` | `info`     | info / warning / error / debug |

比环境变量更简单的方式：
- **本地**：把 `opensource/local/config.env.example` 复制为
  `opensource/local/config.env`，直接改 `PORT` / `ADMIN_TOKEN`。
- **Docker**：在 `docker-compose.yml` 旁创建 `.env`，写入 `PORT=8081` 等。

## 新业务线接入指南

新团队只需要两样东西：

1. **代码** —— clone 本仓库即可（内置纯虚构演示数据，可放心分享）。
2. **一个空数据目录** —— 无需准备任何东西；首次启动会自动创建 `data.json`
   和默认 `admin` 用户。

然后运行：

```bash
# 本地
git clone <this-repo> && cd opensource/local && ./start.sh

# Docker
cd opensource/docker && cp .env.example .env && docker compose up -d --build
```

一套代码服务多个环境：把 `DATA_DIR` 分别指向各团队自己的目录即可。移交现成
数据：在管理后台导出备份 zip，对方在自己的后台导入即可。代码升级只需
`git pull` + 重启 —— 数据目录永不被动。

## 演示数据生成器

内置的 `data.json` 为纯虚构数据。`opensource/tools/anonymize.py` 可把任意一份
data.json 洗牌成全新的虚构数据——公司名、品牌、负责人、分公司/城市/区域、
业务线、Logo 与网址全部替换为虚构值：

```bash
python opensource/tools/anonymize.py --src opensource/local/data.json --out opensource/local/data.json
```

城市、区域与业务线按合理权重重新洗牌（确定性随机、带种子 —— 每次输出
完全一致）。

## 目录结构

```
opensource/   开源项目（本仓库跟踪的全部内容）
├── local/    直接用 Python 运行（自动创建虚拟环境）
├── docker/   Docker Compose 部署（数据持久化卷）
├── tools/    anonymize.py —— 演示数据生成器
└── docs/     截图
```

## 开源协议

MIT —— 见 [LICENSE](LICENSE)。
