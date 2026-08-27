# 客户品牌墙 Logo Wall

本项目包含两部分：**opensource/**（开源版代码，同步到 GitHub）与 **posdemo/**（内部演示环境，仅数据与配置，不上传 GitHub）。

## 核心设计：代码与数据分离

```
                ┌──────────────────┐
                │   opensource/    │  代码（唯一来源，改代码只改这里）
                │  local + docker │
                └────────┬─────────┘
              DATA_DIR 环境变量 / Docker 卷挂载
                ┌────────┴─────────┐
                │    posdemo/data/ │  业务数据（真实客户数据）
                └──────────────────┘
```

- `opensource` 是代码的唯一维护入口
- `posdemo` 只存业务数据（`data/`）和部署配置，**代码更新后无需同步 posdemo**
- 备份/迁移用管理后台的「导出备份 / 导入备份」一键完成（zip 含客户数据 + Logo + 用户账户）

## 目录结构

```
cwpos/
├── opensource/     # 开源版（同步到 GitHub，虚构演示数据）
│   ├── local/           # 本地部署版（start.bat / start.sh）
│   ├── docker/          # Docker 部署版
│   ├── tools/           # anonymize.py 脱敏脚本
│   ├── docs/screenshots/
│   └── README.md / LICENSE / .gitignore
│
└── posdemo/        # 内部演示环境（纯数据目录，不同步到 GitHub）
    ├── data/            # ★ 业务数据：data.json / logos/ / users.json
    ├── docker/           # 部署配置：docker-compose + .env（代码引用 opensource）
    ├── 原始资料/         # 原始 Excel 数据和 PPTX 参考（不参与部署）
    ├── build_data.py / update_data.py   # 数据工具（Excel → data.json）
    ├── 启动演示环境.bat   # 本地一键启动
    └── README.md
```

## 同步说明

| 文件夹 | 是否同步 GitHub | 说明 |
|--------|:---------------:|------|
| `opensource/` | ✅ | 开源版：local + docker 双部署、虚构演示数据、脱敏脚本 |
| `posdemo/` | ❌ | 内部演示环境：真实客户数据与原始资料，已在 `.gitignore` 中排除 |

## 各版本启动方法

### posdemo — 本地启动（数据 = 真实业务数据）

双击 `posdemo/启动演示环境.bat`。原理：调用 opensource 的启动脚本，`DATA_DIR` 指向 `posdemo/data`。

### opensource — 本地启动（数据 = 虚构演示数据）

双击 `opensource/local/start.bat`。

前台 http://localhost:8080/ ，后台 http://localhost:8080/admin ，令牌 `admin123`。

### posdemo — Docker 启动

```bash
cd posdemo/docker
cp .env.example .env      # 修改 ADMIN_TOKEN
docker compose up -d --build
```

镜像从 `opensource/docker` 构建，数据挂载宿主机 `posdemo/data`，容器重建数据不丢失。

### opensource — Docker 启动

```bash
cd opensource/docker
cp .env.example .env
docker compose up -d --build
```

Cloudflare Tunnel 公网部署详见 `posdemo/docker/Docker部署指南.md`。

## 功能概览

| 功能 | local | docker |
|------|:-----:|:------:|
| 品牌墙展示 | ✅ | ✅ |
| 区域 / 城市 / 业务线 / 负责人筛选（各占一行） | ✅ | ✅ |
| 搜索 | ✅ | ✅ |
| 头部 / 筛选栏折叠 | ✅ | ✅ |
| 主题换肤（5 主题 × 4 背景） | ✅ | ✅ |
| 导出 PNG 海报（竖版/大屏/A4） | ✅ | ✅ |
| 管理后台（增删改客户） | ✅ | ✅ |
| 每页显示数量可调 | ✅ | ✅ |
| 未配 Logo 查找 | ✅ | ✅ |
| 站点设置（标题/标语/页脚/默认主题） | ✅ | ✅ |
| Logo 上传 / 替换 / 自动抓取 | ✅ | ✅ |
| Excel 导入 / 导出 | ✅ | ✅ |
| Logo 库（文件管理） | ✅ | ✅ |
| 全量备份导出 / 导入（zip） | ✅ | ✅ |
| config.env / .env 配置端口等 | ✅ | ✅ |
| 数据存储 | 本地文件 | 卷挂载 / bind mount |
| 静态 data.json 兜底 | ✅ | ✅ |

## 数据说明

两套环境共享相同的数据结构（按城市/区域/业务线/负责人组织）：
- 区域划分：华北 / 华东 / 华南 / 华西 / 台湾
- 业务线：OOSG / OPLS / OPCS
- Logo 全部本地化存储，不依赖外部 URL

- **posdemo**：真实客户数据（约 202 条记录），存放在 `posdemo/data/`
- **opensource**：完全虚构的演示数据；如需从真实数据重新生成安全的演示数据集，使用 `opensource/tools/anonymize.py` 脱敏脚本
- 两套环境之间迁移数据：管理后台「导出备份 → 导入备份」一键完成

更多开源版详情见 [opensource/README.md](opensource/README.md)。
