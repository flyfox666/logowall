# Docker 部署版

**English** | **简体中文**

适合长期运行在服务器 / NAS 上，数据持久化在 Docker volume。

## 启动

```bash
docker compose up -d --build
```

访问 http://localhost:8080/ ，后台 http://localhost:8080/admin 。

首次启动会自动创建默认管理员 `admin / admin123`，登录后请在「用户管理」中修改密码、按需新增 viewer 只读账号。`ADMIN_TOKEN` 仍作为主令牌兜底。

前台与管理后台右上角均有「EN / 中文」按钮，可一键切换中英文界面（各自独立记忆）。

## 配置

编辑 `docker-compose.yml` 的 environment，或创建 `.env`：

```
ADMIN_TOKEN=your-secret-token
```

| 变量 | 默认值 | 说明 |
|---|---|---|
| `ADMIN_TOKEN` | admin123 | 主令牌（写操作兜底认证，生产环境务必修改） |
| `AUTH_ENABLED` | true | 登录页开关（admin / viewer 多用户） |
| `JWT_SECRET` | 自动派生 | 登录会话密钥；固定后重启不掉登录态 |
| `JWT_EXPIRE_DAYS` | 7 | 登录会话有效期（天） |
| `DATA_DIR` | /data | 容器内数据目录（挂载到 volume） |
| `BACKUP_MAX_MB` | 200 | 导入备份 zip 的大小上限 |

端口映射在 `docker-compose.yml` 的 `ports` 修改（默认 `8080:8080`）。

## 数据

- 客户数据与上传的 Logo 保存在 `logo-wall-data` volume（`data.json` + `logos/` + `users.json`）。
- 首次启动会自动把镜像内置的演示数据 seed 到 volume。
- **推荐备份方式**：管理后台工具栏「导出备份 / 导入备份」一键下载或恢复 zip（客户 + Logo 文件 + 用户账户），适合跨环境迁移与定期备份。
- 命令行冷备份（服务停止时）：
  `docker run --rm -v logo-wall-data:/data -v $PWD:/backup alpine tar czf /backup/logo-wall-backup.tgz -C /data .`

## 多环境部署（可选）

同一份镜像可服务多个数据环境：在 compose 中把宿主机任意目录挂载到 `/data`
并保持 `DATA_DIR=/data`，即可让每个团队/业务线拥有独立数据，代码升级只需
重新 pull 镜像、数据不受影响。详见仓库根目录 README 的
「架构：代码与数据分离」章节。

## 公网访问（可选）

如需通过 Cloudflare Tunnel 暴露公网，可在 `docker-compose.yml` 中追加
cloudflared 服务（参考官方镜像 `cloudflare/cloudflared:latest`），
或使用 `cloudflared tunnel` 命令行指向本服务端口。
