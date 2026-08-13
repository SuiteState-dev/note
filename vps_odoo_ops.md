# VPS 运维档案 · SuiteState-odoo

**文档版本**：v1
**最后核实**：2026-08-14
**核实方式**：本次会话逐条命令实测，非推测

---

## 1. 主机基本信息

| 项 | 值 |
|---|---|
| 供应商 | Vultr |
| 面板 Label | SuiteState-odoo |
| 位置 | Tokyo |
| IP | 45.76.51.62 |
| 规格 | 2 vCPU / 4096 MB RAM / 100 GB NVMe |
| 系统 | Ubuntu 24.04 LTS x64 |
| 内核 | 6.8.0-137-generic（2026-08-14 更新并重启） |
| 创建时间 | 2026 年 7 月中（前一台 4 月租用的小内存机器已弃用） |
| 月费 | 约 $11 起（当期账单口径） |

**磁盘占用**：约 31%（约 29 GB / 93.2 GB 可用），空间充裕。

**Swap**：8 GB，已配置在 `/etc/fstab`，重启保持。

---

## 2. 用途定位

| 阶段 | 定位 |
|---|---|
| 2026-08 之前 | 客户演示展厅 + SuiteState 内部系统 + 中国出口节点（闲置停用状态） |
| 2026-08-14 起 | **零售业务生产系统**（Odoo 19 Community） |
| 未来 | 业务量起来后迁移至企业版 |

**版本决策**：V19 起步，不等 V20。理由：Community 的会计功能边界由产品线策略决定，非版本迭代问题，V20 预计不会增加企业版会计功能；且当前不安装任何自建模块，升级面窄。

**模块策略**：暂不部署任何 `suite_*` 自建模块。企业版侧的开发工作量已饱和。

---

## 3. 访问方式

### 3.1 日常访问（SSH 密钥）

本地 `~/.ssh/config` 条目：

```
Host suitestate-vps
    HostName 45.76.51.62
    User safi
    IdentityFile ~/.ssh/id_ed25519
    ServerAliveInterval 60
    ServerAliveCountMax 3
    AddKeysToAgent yes
```

连接命令：`ssh suitestate-vps`

### 3.2 密钥分布

| 机器 | 私钥位置 | 公钥注释 | 用途 |
|---|---|---|---|
| 本地 Windows（ELKAF） | `C:\Users\ELKAF\.ssh\id_ed25519` | `safi-suitestate-vps` | 连 VPS |
| VPS | `/home/safi/.ssh/id_ed25519` | `vultr-vps` | VPS 连 GitHub（认证账号 `SuiteState-dev`） |

两把钥匙**互不相关**，各自独立，不要混用或覆盖。

### 3.3 权限模型

- root 的 SSH 登录已禁用（`PermitRootLogin no`）
- 日常用户 `safi`，拥有 sudo 权限
- 需要 root shell 时：登录后执行 `sudo -i`

### 3.4 应急通道

SSH 完全不可用时（配置改坏、防火墙锁死、sshd 崩溃）：

**Vultr 面板 → Compute → 实例 → View Console**

走虚拟串口，绕过 SSH 和 ufw。可用 root 或 safi 的密码登录（`PasswordAuthentication no` 只影响 SSH，不影响此通道）。

**密码存放**：root 与 safi 密码均存于密码管理器。
**注意**：Vultr 面板 Overview 页显示的 Password 是**实例创建时的初始密码**，不跟踪系统内的后续修改。root 密码已于 2026-08-14 在系统内重设，面板显示值已失效，以密码管理器为准。

---

## 4. 安全配置现状

| 项 | 状态 | 备注 |
|---|---|---|
| root SSH 登录 | 禁用 | |
| SSH 密码认证 | 禁用 | 见 §4.1 的坑 |
| ufw | active | 仅开放 22 / 80 / 443（含 v6） |
| fail2ban | enabled | |
| Swap | 8 GB | |
| unattended-upgrades | 已安装 | |
| Odoo 监听 | 127.0.0.1 | 外部仅经 nginx |
| Odoo `list_db` | False | 数据库列表不可枚举 |
| Odoo `admin_passwd` | pbkdf2 哈希存储 | 非明文 |

### 4.1 已踩坑：sshd 配置的"首次出现胜出"规则

`/etc/ssh/sshd_config.d/` 下两个文件同时定义了 `PasswordAuthentication`：

```
50-cloud-init.conf  →  yes    ← 曾经生效
99-hardening.conf   →  no     ← 曾被静默忽略
```

sshd 的规则是**首次出现的值胜出**，不是后者覆盖前者。文件按数字顺序加载，`50-` 先于 `99-`，因此自建的加固配置一直未生效。

**处理**：注释掉 `50-cloud-init.conf` 中的该行，使 `99-hardening.conf` 成为唯一定义。

**复发风险**：cloud-init 在重装系统或某些云端操作后可能重新生成 `50-cloud-init.conf`。若日后发现密码登录又可用，第一个排查此文件。

**验证命令**：
```bash
sudo sshd -T | grep -i -E "passwordauth|permitrootlogin"
```
预期输出 `permitrootlogin no` / `passwordauthentication no`。

### 4.2 待办安全项

| 项 | 优先级 | 说明 |
|---|---|---|
| **站外备份** | **最高** | 见 §7 |
| Vultr Auto Backups | 中 | 面板显示 Not Enabled，约 $2.4/月，整盘还原 |
| 出口节点代理审计 | 中 | 若仍运行 shadowsocks/xray 类服务，需确认非开放代理（有认证、强密码、非全网监听），否则有被扫描滥用导致 Vultr 冻结账号的风险 |
| Cloudflare 橙云代理 | 低 | 当前 DNS-only，源站 IP 暴露。开代理可隐藏源站，但会影响 Let's Encrypt HTTP-01 验证，需改 DNS-01 |
| `admin_passwd` 轮换 | 低 | 哈希值曾在截图中外泄。`list_db = False` 已挡住入口，风险有限 |

---

## 5. Odoo 配置

### 5.1 安装方式

**apt 包安装**（Odoo 官方 nightly deb），非 git 源码部署。

- 包名：`odoo`
- 当前版本：`19.0.20260813`
- 可执行：`/usr/bin/odoo`
- 服务单元：`/usr/lib/systemd/system/odoo.service`
- 配置文件：`/etc/odoo/odoo.conf`
- 日志：`/var/log/odoo/odoo-server.log`

**更新方式**：
```bash
sudo apt update && sudo apt list --upgradable | grep -i odoo
sudo apt install --only-upgrade odoo
```

更新中若弹出配置文件对话框，**选择保留本地版本**，避免 `admin_passwd` 等自定义配置被覆盖。

**更新纪律**：跑生产后应定期更新。Odoo 的安全修复直接进入版本分支，不单独发公告。

### 5.2 服务管理

```bash
sudo systemctl start odoo        # 启动
sudo systemctl stop odoo         # 停止
sudo systemctl restart odoo      # 重启
sudo systemctl enable --now odoo # 启用并立即启动（开机自启）
systemctl status odoo --no-pager # 查看状态
```

当前状态：`enabled` + `active (running)`，开机自启已验证。

### 5.3 odoo.conf 当前内容

```ini
[options]
db_host = False
db_port = False
db_user = odoo
db_password = False
default_productivity_apps = True
admin_passwd = <pbkdf2 哈希>

proxy_mode = True
list_db = False
http_interface = 127.0.0.1
workers = 2
max_cron_threads = 1
limit_memory_soft = 629145600
limit_memory_hard = 786432000
limit_time_cpu = 600
limit_time_real = 1200
```

**备份文件**：`/etc/odoo/odoo.conf.bak`（2026-08-14 修改前的版本）

**参数说明**：

| 参数 | 值 | 理由 |
|---|---|---|
| `workers` | 2 | 4 GB 机器 + 2 vCPU 的合理值。0 或缺省 = 单进程 threaded 模式，不适合生产 |
| `limit_memory_soft` | 600 MB | Odoo 默认约 2 GB，是给 8 GB+ 机器的值，在此机器上形同虚设 |
| `limit_memory_hard` | 750 MB | |
| `http_interface` | 127.0.0.1 | 仅本机监听，外部必须经 nginx |
| `max_cron_threads` | 1 | 小机器省资源 |

**尚未配置**：`dbfilter`（需先确定数据库名后再加，可防止多库串访问）

### 5.4 端口

| 端口 | 用途 | 监听地址 |
|---|---|---|
| 8069 | HTTP 主服务 | 127.0.0.1 |
| 8072 | websocket / longpolling（仅多进程模式下存在） | 127.0.0.1 |

多进程模式启用后 8072 才出现。若日后把 `workers` 改回 0，8072 会消失，nginx 的 `/websocket` 转发会失效。

### 5.5 资源占用参考（实测）

| 场景 | 内存 |
|---|---|
| Odoo 停止 | 系统约 836 Mi |
| Odoo 单进程（workers 缺省） | Odoo 约 94 M |
| Odoo 多进程（workers = 2） | Odoo 约 201 M |

系统总内存 3.8 Gi，另有 8 GB swap。当前配置余量充足。

---

## 6. Nginx 反向代理

- 配置文件：`/etc/nginx/sites-available/odoo`
- 软链接：`/etc/nginx/sites-enabled/odoo`
- 备份：`/etc/nginx/sites-available/odoo.bak`
- 域名：`erp.suitestate.com`
- 证书：Let's Encrypt，`/etc/letsencrypt/live/erp.suitestate.com/`
- DNS：Cloudflare，**DNS-only**（未开橙云代理）

**配置要点**（已验证完整，无需改动）：

- `upstream odoo` → 127.0.0.1:8069
- `upstream odoochat` → 127.0.0.1:8072
- 80 端口 301 跳转至 443
- `location /` → odoo
- `location /websocket` → odoochat，带 `Upgrade` / `Connection "upgrade"` 头
- `client_max_body_size 100M`
- 转发头齐全：`X-Forwarded-Host` / `X-Forwarded-For` / `X-Forwarded-Proto` / `X-Real-IP`

**排查提示**：`grep -r` 默认不跟随软链接，直接 grep `sites-enabled/` 会得到空结果，应查 `sites-available/`。

**常规操作**：
```bash
sudo nginx -t                    # 语法检查
sudo systemctl reload nginx      # 重载
```

**502 判读**：Odoo 停止时访问域名返回 502 属预期行为，非故障。

---

## 7. 备份（未实施 · 最高优先级待办）

跑真实零售数据后，备份是唯一无法事后补救的环节。自建 Community 意味着备份 100% 由自己负责。

### 7.1 两层备份的分工

| 层 | 工具 | 救什么 | 状态 |
|---|---|---|---|
| 整机快照 | Vultr Auto Backups / Snapshots | 系统坏了、误删文件 | 未启用 |
| 数据库逻辑备份 | `pg_dump` + filestore + 站外存储 | 数据错了、误删记录、要回到某一天 | 未实施 |

**关键区别**：Vultr 快照**不是数据库一致性备份** —— 快照瞬间 Postgres 可能正在写入，恢复出的库状态不保证干净。快照是补充，不能替代 `pg_dump`。

### 7.2 计划方案

```bash
# 数据库
pg_dump -Fc -d <dbname> > /backup/db_$(date +%F).dump
# filestore（附件、图片）
tar czf /backup/fs_$(date +%F).tar.gz ~/.local/share/Odoo/filestore/<dbname>
```

**站外目标：Cloudflare R2**

选择理由不是单价便宜，而是**无下载流量费** —— B2、S3 恢复时按下载量计费，R2 不计。且 Cloudflare 账号已有（域名在此）。

**待办清单**：
1. 开 R2 bucket
2. VPS 装 rclone 并配置凭据
3. 写备份脚本（pg_dump + filestore + 上传 + 保留策略）
4. 配 cron 定时
5. **实际恢复一次做验证** —— 未验证过的备份等于没有备份

### 7.3 临时措施

正式方案落地前，若已开始录入真实数据：Vultr 面板 Snapshots 页手动打快照。不是长久之计，但优于裸奔。

---

## 8. 开发环境

### 8.1 VS Code Remote-SSH

本地 VS Code 通过 Remote-SSH 扩展连接，主机名 `suitestate-vps`。

服务器端会自动安装 VS Code Server（约 200 MB 磁盘，运行时 200–400 MB 内存）。

**远程设置**（`Preferences: Open Remote Settings (JSON) (suitestate-vps)`）：

```json
{
  "files.watcherExclude": {
    "**/odoo/**": true,
    "**/.git/objects/**": true,
    "**/node_modules/**": true,
    "**/*.po": true,
    "**/static/lib/**": true
  },
  "search.followSymlinks": false,
  "files.exclude": {
    "**/*.pyc": true,
    "**/__pycache__": true
  }
}
```

**系统参数**（已写入 `/etc/sysctl.conf`）：
```
fs.inotify.max_user_watches=262144
```

**理由**：VS Code 递归监视目录树，Odoo 源码数万文件会耗尽 inotify 配额（Ubuntu 默认约 8192），触发 `ENOSPC: System limit for number of file watchers reached`，并造成 CPU 空转与内存上涨。

**纪律**：远程扩展装最少的几个。每个远程扩展都在服务器上跑独立进程，4 GB 机器上会积少成多。

### 8.2 Odoo 源码仓库

VPS 上另有一份手动 clone 的 Odoo 源码（与 apt 安装的运行本体无关）。

- 占约 1.5–2 GB 磁盘，**不占内存**（被读取时进 page cache，属可回收内存）
- 100 GB 盘，占比约 2%，保留无碍
- **不要在 VS Code 中直接打开该目录作为工作区**，参见 §8.1

### 8.3 Claude Code 使用场景

VPS 上的 Claude Code 平时不使用，仅在两种场景登录：

1. 写微信小程序时
2. 人在中国时

**VPS 侧的独有优势**：能直接写入自己的仓库（Odoo.sh 的 shell 只能只读查看源码）。

**注意**：不同环境的 Claude 记忆不共享。

---

## 9. 未决事项与判断依据

| 事项 | 当前决定 | 触发重新评估的条件 |
|---|---|---|
| Community vs Enterprise | 暂用 Community | 需要完整会计（银行对账、资产、递延）时。Community 的 `account` 仅有开票功能 |
| V19 vs V20 | 锁定 V19 | 无。V20 预计不增加企业版会计功能 |
| 自建模块部署 | 不部署 | 企业版侧开发工作量饱和，暂无余力 |
| 迁移至 Odoo.sh | 未定 | Community → Enterprise 本身简单（加 enterprise addons path + 装 `web_enterprise`，数据不迁）。真正复杂的是自建 → Odoo.sh（dump/restore + 版本对齐 + `suite_*` 模块部署方式），届时单独规划 |

**若日后部署自建模块**，建议目录：
```bash
sudo mkdir -p /opt/suitestate-addons
sudo chown safi:odoo /opt/suitestate-addons
sudo chmod 775 /opt/suitestate-addons
```
再加入 `odoo.conf` 的 `addons_path`。此方式使 safi 可在 VS Code 中直接读写，无需每次 sudo。

`/etc/odoo/odoo.conf` 建议保持 root 属主不变 —— 内含 `admin_passwd`，为迁就 GUI 保存而放宽权限不划算。改配置用终端 `sudo nano` 即可。

---

## 10. 常用命令速查

```bash
# 连接
ssh suitestate-vps

# 服务
systemctl status odoo --no-pager
sudo systemctl restart odoo
sudo journalctl -u odoo -n 50 --no-pager     # 看最近日志

# 资源
free -h
df -h /
ss -tlnp | grep -E "8069|8072"

# 安全核查
sudo sshd -T | grep -i -E "passwordauth|permitrootlogin"
sudo ufw status
systemctl is-enabled fail2ban

# 配置
sudo nano /etc/odoo/odoo.conf
sudo nano /etc/nginx/sites-available/odoo
sudo nginx -t && sudo systemctl reload nginx

# 更新
sudo apt update && sudo apt list --upgradable
sudo apt install --only-upgrade odoo
```

---

## 11. 变更日志

| 日期 | 变更 |
|---|---|
| 2026-04 | 首台 VPS 租用（内存过小，后弃用） |
| 2026-07 中 | 当前实例创建 |
| 2026-07-01 | root 密码设置（继承自旧机快照） |
| 2026-08-13 前 | Odoo 主动 `systemctl disable` 停用，nginx 配置保留 |
| 2026-08-14 | 关闭 SSH 密码认证（修复 cloud-init 覆盖问题）；重设 root 密码；VS Code Remote 接入；Odoo 更新 `19.0.20260701` → `19.0.20260813`；内核更新至 6.8.0-137 并重启；odoo.conf 增加 workers / http_interface 等 7 项；验证 nginx websocket 链路 |
