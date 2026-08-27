# 本地部署版（Local）

**English** | **简体中文**

直接用 Python 运行，适合个人电脑 / 活动现场笔记本。

## 启动

- Windows：双击 `start.bat`
- macOS / Linux：`./start.sh`（首次运行自动创建虚拟环境并安装依赖）

启动后终端会打印所有可访问地址：

```
On this computer:
  Brand wall :  http://localhost:8080/
  Admin panel:  http://localhost:8080/admin
From other phones/computers on the same Wi-Fi/LAN:
  Brand wall :  http://<本机局域网IP>:8080/
```

## 配置

最简单：把 `config.env.example` 复制为 `config.env`，在里面改 `PORT` / `ADMIN_TOKEN`，重启即生效。
也可以用环境变量：

| 变量 | 默认值 | 说明 |
|---|---|---|
| `PORT` | 8080 | 服务端口 |
| `HOST` | 0.0.0.0 | 监听地址，仅本机用可改 127.0.0.1 |
| `ADMIN_TOKEN` | admin123 | 主令牌（写操作兜底认证） |
| `AUTH_ENABLED` | true | 登录页开关（admin / viewer 多用户） |
| `JWT_SECRET` | 自动派生 | 登录会话密钥；固定后重启不掉登录态 |
| `JWT_EXPIRE_DAYS` | 7 | 登录会话有效期（天） |
| `DATA_DIR` | 本目录 | data.json / logos/ / users.json 的位置 |
| `MAX_UPLOAD_MB` | 5 | Logo 上传大小上限 |
| `BACKUP_MAX_MB` | 200 | 导入备份 zip 的大小上限 |
| `IMGPROXY_MAX_MB` | 8 | 海报抓图代理单张上限 |
| `IMGPROXY_TIMEOUT` | 10 | 海报抓图代理超时（秒） |
| `LOG_LEVEL` | info | info / warning / error / debug |

## 使用提示

- 前台筛选按 区域 → 城市 → 业务线 → 负责人 排列、各占一行；头部与筛选栏均可一键折叠（状态记忆），大屏展示更沉浸。
- 管理后台 `/admin`：新增 / 编辑 / 删除客户、Excel 导入导出、Logo 自动抓取与上传、Logo 库；分页每页 15–200 条可调；「Logo：未配」筛选或点击「已配Logo」统计卡可快速找出缺 Logo 的客户。
- 「站点设置」：修改标题 / 英文副标题 / 标语 / 页脚、默认主题与背景、自定义配色。
- 前台右上「导出海报」：把当前筛选结果导出为 PNG 海报（竖版 / 大屏 / A4）。
- 前台调色盘按钮：访客个人预览主题，不影响他人；「恢复站点默认」清除预览。
- **登录与多用户**：访问前台会先进入登录页；首次启动自动创建默认管理员 `admin / admin123`（登录后请在「用户管理」中修改密码、按需新增 viewer 只读账号）。`AUTH_ENABLED=false` 可关闭登录页。
- **全量备份**：管理后台工具栏「导出备份 / 导入备份」一键下载或恢复 zip（客户 + Logo 文件 + 用户账户），适合跨环境迁移与定期备份。
- **中英文切换**：前台与管理后台右上角均有「EN / 中文」按钮，一键切换整站语言（各自独立记忆）。英文模式下标题、筛选、统计、客户卡片、后台表格与弹窗等全部文案切换为英文；站点设置中的「英文副标题 / 英文标语 / 英文页脚」在英文模式下显示。
- 数据保存在 `DATA_DIR`（默认本目录）：`data.json`（客户与站点设置）、`logos/`（Logo 文件）、`users.json`（登录账户）；用管理后台的备份导出/导入即可整体迁移，无需手工拷贝。
