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
- [安全与生产部署](#安全与生产部署)
- [新业务线接入指南](#新业务线接入指南)
- [演示数据生成器](#演示数据生成器)
- [目录结构](#目录结构)
- [开发与测试](#开发与测试)
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
  管理员可维护数据。修改密码、修改角色或删除用户后，该账户在所有设备上的
  登录会立即失效；连续登录失败会被限流。可选配置 `ADMIN_TOKEN`，作为 API
  脚本使用的主令牌。
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

启动后打开 http://localhost:8080/ （管理后台 http://localhost:8080/admin）。

首次启动会创建 `admin` 账户，**随机密码只在控制台打印一次**，请务必记下。
也可以在启动前于 `config.env` 中设置 `ADMIN_PASSWORD`，自行指定密码。

### Docker 运行

```bash
cd opensource/docker
docker compose up -d --build
```

首个管理员密码会打印在容器日志里（`docker compose logs logo-wall | grep password`），
也可以在首次启动前于 `.env` 中设置 `ADMIN_PASSWORD`。客户数据与上传的 Logo
持久化在 `logo-wall-data` 卷中。公网部署（Cloudflare
Tunnel）见 [opensource/docker/README.zh-CN.md](opensource/docker/README.zh-CN.md)。

## 架构：代码与数据分离

所有运行时数据都存放在 `DATA_DIR` 指向的单一目录中：

```
DATA_DIR/
├── data.json     # 客户、站点设置、筛选项缓存
├── logos/        # 上传的 Logo 文件
├── users.json    # 登录账户（admin / viewer 角色，bcrypt 哈希）
├── .jwt_secret   # 自动生成的会话签名密钥（勿外泄）
├── audit.log     # 操作与登录审计日志（JSON 行）
└── backups/      # 每次导入备份前自动保存的快照
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

`DATA_DIR` 为空时应用会自动初始化：创建空的 `data.json`，生成随机会话密钥，
并创建 `admin` 用户。密码取自 `ADMIN_PASSWORD`；未设置时随机生成，并在控制台
打印一次。

## 全量备份导出/导入

管理后台工具栏提供「导出备份 / 导入备份」按钮（API：`GET /api/backup/export`、
`POST /api/backup/import`）。

- **导出**：下载 `logo-wall-backup-年月日-时分秒.zip`，内含 `data.json` +
  `logos/` + `users.json` + 记录了条数与时间戳的 `manifest.json`。
- **导入**：先完整校验 zip，校验通过前不改动任何文件。校验内容包括路径、
  文件数量、真实解压大小（`BACKUP_MAX_UNCOMPRESSED_MB`，防 zip 炸弹）、Logo
  文件名与内容，以及 `data.json` / `users.json` 的结构。校验通过后，先把当前
  数据快照保存到 `DATA_DIR/backups/`（保留最近 `AUTO_SNAPSHOTS_KEEP` 份），
  再替换客户数据并合并 Logo 文件。**用户账户只有在你确认后才会恢复**，API
  调用时需传 `restore_users=true`。不含管理员的账户文件会被拒绝，避免导入后
  把自己锁在外面。

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
2. **本地上传** — 选择本地图片文件（PNG / JPG / GIF / WebP / SVG / ICO）。
   文件类型根据内容识别，而不是文件名。超过 `LOGO_MAX_PX`（800 像素）的位图
   会自动缩小，品牌墙和海报加载更快。
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
| `ADMIN_PASSWORD` | 随机 | 首次启动创建的 `admin` 账户密码（未设置时随机生成并打印） |
| `ADMIN_TOKEN` | *（禁用）* | 可选，API 脚本用的主令牌；少于 12 位或已知默认值（如 `admin123`）会被拒绝 |
| `AUTH_ENABLED` | `true`   | 查看品牌墙是否需要登录（管理后台始终需要登录） |
| `JWT_SECRET` | 随机 | 会话签名密钥；未设置时随机生成并保存在 `DATA_DIR/.jwt_secret` |
| `JWT_EXPIRE_DAYS` | `7`   | 登录会话有效期（天） |
| `MIN_PASSWORD_LEN` | `8`  | 新建或修改密码的最小长度 |
| `LOGIN_MAX_FAILURES` | `5` | 同一 IP + 用户名允许的连续失败次数，超过后临时锁定 |
| `LOGIN_LOCK_MINUTES` | `15` | 登录失败锁定时长（分钟） |
| `DATA_DIR`  | 应用目录 | `data.json` / `logos/` / `users.json` 的位置 |
| `MAX_UPLOAD_MB` | `5`    | Logo 上传大小上限 |
| `LOGO_MAX_PX` | `800`    | 位图 Logo 最长边超过该值时自动缩小（0 = 保留原图） |
| `MAX_EXCEL_MB` | `20`    | Excel 导入大小上限 |
| `BACKUP_MAX_MB` | `200`  | 导入备份 zip 的大小上限 |
| `BACKUP_MAX_UNCOMPRESSED_MB` | `1024` | 备份解压后的总大小上限（防 zip 炸弹） |
| `AUTO_SNAPSHOTS_KEEP` | `5` | `DATA_DIR/backups/` 中保留的导入前快照数量（0 = 关闭） |
| `IMGPROXY_MAX_MB` | `8`  | 海报抓图代理单张上限 |
| `IMGPROXY_TIMEOUT` | `10`| 海报抓图代理超时（秒） |
| `FETCH_ALLOW_PRIVATE` | `false` | 允许抓图代理和 Logo 下载访问内网地址（见下文） |
| `CORS_ORIGINS` | *（空）* | 允许跨域调用 API 的来源，逗号分隔 |
| `LOG_LEVEL` | `info`     | info / warning / error / debug |

比环境变量更简单的方式：
- **本地**：把 `opensource/local/config.env.example` 复制为
  `opensource/local/config.env`，直接改 `PORT` / `ADMIN_PASSWORD` 等。
- **Docker**：在 `docker-compose.yml` 旁创建 `.env`，写入 `PORT=8081` 等。

## 安全与生产部署

- **超出可信局域网时必须启用 HTTPS。** 应用本身只提供 HTTP，不加 HTTPS 的话，
  密码和会话令牌会以明文传输。请放在负责 TLS 的反向代理后面，例如 Caddy、
  Nginx、Traefik 或 Cloudflare Tunnel。最简 Caddy 配置：

  ```
  wall.example.com {
      reverse_proxy 127.0.0.1:8080
  }
  ```

  代理与应用在同一台机器时，设置 `HOST=127.0.0.1`。应用只信任来自
  `FORWARDED_ALLOW_IPS`（默认 `127.0.0.1`）的 `X-Forwarded-For` / `-Proto`
  头。如果代理在别处，例如另一个容器，请把它设为代理的地址，这样登录限流能
  看到真实客户端 IP，会话 cookie 也会带上 `Secure` 标记。应用端口还能被直接
  访问时，不要设为 `*`，否则客户端可以伪造 IP。
- **会话**：API 调用通过 `Authorization: Bearer` 携带 JWT。HttpOnly、
  `SameSite=Lax` 的 cookie 只用于授权 `<img>` 加载受保护的 Logo，不能用于写
  操作；令牌不会出现在 URL 中。
- **服务端外发请求**（海报抓图代理、「从 URL 抓取 Logo」、Logo 自动发现）会
  拒绝内网、回环、链路本地和云元数据地址，并在每次重定向后重新检查，防止
  服务器被用来探测内网。如果 Logo 托管在内网服务器上，可以设置
  `FETCH_ALLOW_PRIVATE=true`，仅限可信部署。
- **上传的图片**按内容校验。SVG 和代理返回的图片带有沙箱化的
  `Content-Security-Policy`，恶意 SVG 无法执行脚本。
- **审计日志**：登录（包括失败的尝试）和所有写操作都会追加到
  `DATA_DIR/audit.log`，超过 5 MB 自动轮转。管理员可通过
  `GET /api/audit?limit=200` 查看最近记录。
- **定时备份**：备份接口可以用主令牌（`ADMIN_TOKEN`，至少 12 位）或登录令牌
  调用，例如用 cron 每晚备份：

  ```bash
  0 3 * * * curl -fsS -H "Authorization: Bearer $LOGO_WALL_TOKEN" \
    http://127.0.0.1:8080/api/backup/export \
    -o /backups/logo-wall-$(date +\%F).zip && find /backups -name 'logo-wall-*.zip' -mtime +30 -delete
  ```

- **只运行单个工作进程。** 数据存放在 JSON 文件中，由进程内锁保护，
  不要用 `--workers > 1` 启动 uvicorn。

### 从旧版本升级

- 众所周知的默认值已移除：`ADMIN_TOKEN=admin123` 会被忽略，会话密钥也不再从
  它派生，所以**升级后所有人需要重新登录一次**。已有账户的密码不变。如果某个
  管理员仍在用 `admin123`，启动时会打印警告，管理后台也会显示横幅，直到改掉
  为止。
- 不再接受旧的 `?token=` 图片地址，自带的页面已改用会话 cookie。
- Docker 镜像改为以非特权用户运行。entrypoint 启动时会自动接管已有数据卷的
  属主，无需手动处理，执行 `docker compose up -d --build` 重建即可。
- 去掉了 `pandas` 依赖，Excel 改由 `openpyxl` 处理，新增了 `Pillow`。
  `start.sh` / `start.bat` 会自动重新安装依赖。

## 新业务线接入指南

新团队只需要两样东西：

1. **代码** —— clone 本仓库即可（内置纯虚构演示数据，可放心分享）。
2. **一个空数据目录** —— 无需准备任何东西；首次启动会自动创建 `data.json`
   和 `admin` 用户（随机密码打印一次，或用 `ADMIN_PASSWORD` 预设）。

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
opensource/            开源项目
├── local/             应用本体（唯一源码）
│   ├── index.html     品牌墙页面
│   ├── server/
│   │   ├── app.py     FastAPI 路由
│   │   ├── logowall/  配置、认证、存储、备份、Excel、图片、外发请求、审计
│   │   └── templates/ admin.html、login.html
│   └── tests/         pytest 测试
├── docker/            Dockerfile + Compose（从 local/ 构建镜像）
├── tools/             anonymize.py —— 演示数据生成器
└── docs/              截图
```

## 开发与测试

```bash
cd opensource/local
python -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
python -m pytest tests -q
```

GitHub Actions（`.github/workflows/tests.yml`）会在 Python 3.9 / 3.11 / 3.13
上运行测试，并构建 Docker 镜像做冒烟测试。

## 开源协议

MIT —— 见 [LICENSE](LICENSE)。
