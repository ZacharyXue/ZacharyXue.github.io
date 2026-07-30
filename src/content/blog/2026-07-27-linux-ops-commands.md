---
title: Linux 运维常用命令速查手册
date: 2026-07-27
tags: [Linux, 运维, Shell, grep, awk, 命令行]
description: 系统整理 Linux 运维中最常用的命令，涵盖网络、磁盘、进程、文件操作，并详细介绍 grep 和 awk 的实战用法。
---

## 文件与目录

| 命令 | 用途 | 常用示例 |
|------|------|----------|
| `ls -lah` | 列出文件（含隐藏、人类可读大小） | `ls -lah /var/log/` |
| `find` | 按条件搜索文件 | `find / -name "*.log" -mtime -7` |
| `du -sh` | 目录/文件占用空间 | `du -sh /home/* \| sort -h` |
| `df -h` | 磁盘分区使用情况 | `df -h` |
| `stat` | 文件详细属性（inode、时间戳） | `stat /etc/passwd` |
| `ln -s` | 创建软链接 | `ln -s /opt/app/bin/app /usr/local/bin/app` |
| `tree` | 树形显示目录结构 | `tree -L 2 /etc/nginx/` |

## 文本处理（重点）

### grep —— 文本搜索神器

```bash
grep [选项] '模式' 文件...
```

**核心选项：**

| 选项 | 含义 | 示例 |
|------|------|------|
| `-i` | 忽略大小写 | `grep -i error app.log` |
| `-v` | 反向匹配（排除） | `grep -v DEBUG app.log` |
| `-r` / `-R` | 递归搜索目录 | `grep -r "TODO" ./src/` |
| `-n` | 显示行号 | `grep -n "panic" app.log` |
| `-c` | 统计匹配行数 | `grep -c "ERROR" app.log` |
| `-l` | 只显示文件名 | `grep -rl "deprecated" ./src/` |
| `-w` | 全词匹配 | `grep -w "root" /etc/passwd` |
| `-A N` | 显示匹配行后 N 行 | `grep -A 3 "Exception" app.log` |
| `-B N` | 显示匹配行前 N 行 | `grep -B 2 "ERROR" app.log` |
| `-C N` | 显示匹配行前后各 N 行 | `grep -C 5 "panic" app.log` |
| `-E` | 扩展正则（同 egrep） | `grep -E "error\|warn\|fail" app.log` |
| `-P` | Perl 正则（支持更多语法） | `grep -P '\d{1,3}\.\d{1,3}'` |
| `--color` | 高亮匹配内容 | `grep --color "error" app.log` |

**实战组合：**

```bash
# 查最近的错误，带上下文
grep -n -C 3 "FATAL\|CRITICAL" app.log | tail -50

# 统计各接口 4xx/5xx 返回码分布
grep -oP 'HTTP/\d\.\d" \K\d{3}' access.log | sort | uniq -c | sort -rn

# 查找包含 TODO 且排除 node_modules 的文件名列表
grep -rl "TODO" . --exclude-dir=node_modules --exclude-dir=.git

# 从配置文件里提取非注释的有效行
grep -v '^\s*#' /etc/nginx/nginx.conf | grep -v '^\s*$'
```

### awk —— 文本处理「瑞士军刀」

awk 的基本流程：**逐行读取 → 按分隔符拆分 → 执行 pattern {action}**

```
awk 'pattern {action}' 文件
```

**内置变量：**

| 变量 | 含义 |
|------|------|
| `$0` | 整行内容 |
| `$1, $2, ...` | 第 1, 2, ... 列 |
| `NF` | 当前行的列数 |
| `$NF` | 最后一列 |
| `NR` | 当前行号（累计） |
| `FNR` | 当前文件内的行号 |
| `FS` | 输入分隔符（默认空白） |
| `OFS` | 输出分隔符 |
| `RS` | 输入记录分隔符 |

**实战场景：**

```bash
# 1. 打印第2列和第最后一列
awk '{print $2, $NF}' data.txt

# 2. 按冒号分隔，打印 /etc/passwd 的用户名和 shell
awk -F: '{print $1, $NF}' /etc/passwd

# 3. 过滤：第3列大于 100 的行
awk '$3 > 100' data.txt

# 4. 统计累加：计算所有进程的内存总和
ps aux | awk '{sum+=$6} END {print "Total RSS:", sum, "KB"}'

# 5. 分组统计：按 HTTP 状态码统计
awk '{count[$9]++} END {for(code in count) print code, count[code]}' access.log

# 6. 按分隔符提取字段——分析 nginx access.log
# 日志格式: $remote_addr - [$time_local] "$request" $status $body_bytes_sent
awk '{print $1, $7, $9}' access.log | head

# 7. 去重计数
awk '!seen[$1]++' data.txt                    # 按第1列去重
awk '{arr[$1]++} END {for(k in arr) print k, arr[k]}' data.txt   # 按第1列计数

# 8. 条件 + 格式化输出
df -h | awk '$5+0 > 80 {printf "WARNING: %s usage=%s\n", $6, $5}'

# 9. 处理 CSV（逗号分隔 + 引号内逗号不拆分）
awk -F',' '{gsub(/"/, ""); print $1, $3}' data.csv

# 10. 复杂统计：计算平均值、最大值、最小值
ps aux | awk '{cpu=$3; sum+=cpu; if(cpu>max) max=cpu; if(NR==1 || cpu<min) min=cpu}
              END {printf "avg=%.1f max=%.1f min=%.1f\n", sum/NR, max, min}'
```

### sed —— 流编辑器

```bash
# 替换（最常用）
sed 's/old/new/g' file.txt           # 全局替换（只输出，不修改文件）
sed -i 's/old/new/g' file.txt        # 直接修改文件
sed -i.bak 's/old/new/g' file.txt    # 修改前备份

# 删除行
sed '/^$/d' file.txt                  # 删除空行
sed '2,5d' file.txt                   # 删除第 2-5 行
sed '/^#/d' file.txt                  # 删除注释行

# 提取行
sed -n '10,20p' file.txt              # 打印第 10-20 行
sed -n '/ERROR/p' app.log             # 打印匹配行

# 插入/追加
sed '2i\新行内容' file.txt            # 第2行之前插入
sed '2a\新行内容' file.txt            # 第2行之后追加
```

### 其他常用文本工具

| 命令 | 用途 | 示例 |
|------|------|------|
| `cut` | 按列提取 | `cut -d: -f1,3 /etc/passwd` |
| `sort` | 排序 | `sort -n -k2 -t, data.csv` |
| `uniq` | 去重（需先排序） | `sort data.txt \| uniq -c \| sort -rn` |
| `wc` | 计数 | `wc -l file.txt`（行数）|
| `tr` | 字符替换/删除 | `echo "A,B,C" \| tr ',' '\n'` |
| `xargs` | 将标准输入转为参数 | `find . -name "*.log" \| xargs rm` |
| `tee` | 同时输出到文件和屏幕 | `./app 2>&1 \| tee app.log` |
| `head` / `tail` | 取头/尾 N 行 | `tail -f app.log`（实时追踪）|

---

## 进程管理

| 命令 | 用途 | 常用示例 |
|------|------|----------|
| `ps aux` | 列出所有进程 | `ps aux \| grep nginx` |
| `top` / `htop` | 实时进程监控 | `htop`（更友好） |
| `kill` | 发送信号 | `kill -9 PID`（强制终止） |
| `killall` | 按名称杀进程 | `killall -9 nginx` |
| `pkill` | 按模式杀进程 | `pkill -f "python app.py"` |
| `nice` / `renice` | 调整进程优先级 | `nice -n 10 ./cpu_task` |
| `nohup` | 后台运行（忽略 HUP） | `nohup ./app > app.log 2>&1 &` |
| `jobs` / `fg` / `bg` | 作业控制 | `bg %1`（后台继续运行作业 1） |
| `lsof` | 列出打开的文件 | `lsof -i :8080`（查看占用端口） |
| `pgrep` | 按名称查找 PID | `pgrep -f nginx` |
| `strace` | 跟踪系统调用 | `strace -p PID` |
| `pidstat` | 进程资源统计 | `pidstat 1`（每秒刷新） |

---

## 网络

| 命令 | 用途 | 常用示例 |
|------|------|----------|
| `curl` | HTTP 请求 | `curl -v -X POST -H 'Content-Type: application/json' -d '{}' http://api/`|
| `wget` | 下载文件 | `wget -c https://example.com/file.tar.gz` |
| `ping` | 连通性测试 | `ping -c 4 google.com` |
| `traceroute` | 路由追踪 | `traceroute google.com` |
| `mtr` | 综合 ping + traceroute | `mtr google.com` |
| `ss` | Socket 统计（替代 netstat） | `ss -tlnp`（查看监听端口） |
| `netstat` | 网络连接（旧） | `netstat -anp \| grep 8080` |
| `nslookup` / `dig` | DNS 查询 | `dig +short A example.com` |
| `iptables` / `nft` | 防火墙规则 | `iptables -L -n` |
| `tcpdump` | 抓包 | `tcpdump -i eth0 port 80 -w capture.pcap` |
| `nc` | 网络调试瑞士军刀 | `nc -zv 192.168.1.1 22`（端口测试） |
| `telnet` | 端口连通性 | `telnet 10.0.0.1 3306` |
| `ip` | 网络配置（替代 ifconfig） | `ip addr show` / `ip route show` |
| `ss -tlnp` | 查看所有监听端口 | `ss -tlnp` |

**SSH 相关：**

| 命令 | 用途 |
|------|------|
| `ssh user@host` | 远程登录 |
| `ssh -L 3306:localhost:3306 user@host` | 本地端口转发 |
| `ssh -R 8080:localhost:3000 user@host` | 远程端口转发 |
| `scp file user@host:/path/` | 远程拷贝文件 |
| `rsync -avz src/ user@host:dst/` | 增量同步 |

---

## 磁盘与存储

| 命令 | 用途 | 常用示例 |
|------|------|----------|
| `df -h` | 查看分区使用情况 | `df -h /` |
| `du -sh *` | 目录大小 | `du -sh /var/* \| sort -h` |
| `lsblk` | 列出块设备 | `lsblk -f`（含文件系统类型） |
| `fdisk -l` | 查看磁盘分区表 | `fdisk -l /dev/sda` |
| `mount` / `umount` | 挂载/卸载 | `mount /dev/sdb1 /mnt/data` |
| `iostat` | 磁盘 I/O 统计 | `iostat -x 1` |
| `iotop` | 实时磁盘 I/O 排行 | `iotop -o` |
| `dd` | 磁盘读写（备份/克隆） | `dd if=/dev/sda of=/backup/disk.img bs=4M` |
| `fsck` | 文件系统检查修复 | `fsck /dev/sda1`（需卸载） |
| `badblocks` | 坏道检测 | `badblocks -sv /dev/sda` |

**逻辑卷管理 (LVM)：**

| 命令 | 用途 |
|------|------|
| `pvcreate` / `pvdisplay` | 创建/显示物理卷 |
| `vgcreate` / `vgextend` | 创建/扩展卷组 |
| `lvcreate` / `lvextend` | 创建/扩展逻辑卷 |
| `resize2fs` | 扩展文件系统 |

---

## 系统监控与性能

| 命令 | 用途 |
|------|------|
| `uptime` | 系统运行时间 + 平均负载 |
| `free -h` | 内存使用情况 |
| `vmstat 1` | 虚拟内存统计（每秒） |
| `sar` | 系统活动报告（CPU、内存、I/O） |
| `dmesg` | 内核日志（驱动、硬件错误） |
| `journalctl` | systemd 日志 |
| `uname -a` | 系统信息（内核版本、架构） |
| `lscpu` | CPU 详情 |
| `lsmem` | 内存详情 |
| `dmidecode` | 硬件信息（BIOS、主板） |

**日志查看：**

```bash
# systemd 日志
journalctl -u nginx -f                  # 实时追踪
journalctl -u nginx --since "1 hour ago"
journalctl -u nginx -p err              # 只看错误

# 传统日志
tail -f /var/log/syslog
tail -n 100 /var/log/nginx/error.log
less /var/log/messages                  # 按 / 搜索，按 n 下一个
```

---

## 用户与权限

| 命令 | 用途 |
|------|------|
| `whoami` / `id` | 当前用户/用户组信息 |
| `useradd` / `userdel` | 创建/删除用户 |
| `passwd` | 改密码 |
| `su - user` | 切换用户 |
| `sudo` | 提权执行 |
| `chmod` | 改权限（`chmod 755 file` 或 `chmod +x`） |
| `chown` | 改所有者（`chown user:group file`） |
| `umask` | 默认权限掩码 |
| `groups user` | 查看用户所属组 |

---

## 压缩与打包

| 命令 | 用途 |
|------|------|
| `tar -czvf file.tar.gz dir/` | 打包并 gzip 压缩 |
| `tar -xzvf file.tar.gz` | 解压 |
| `gzip` / `gunzip` | 压缩/解压 .gz |
| `zip` / `unzip` | 压缩/解压 .zip |
| `zcat file.gz` | 不解压直接查看 |

---

## 软件包管理

| 系统 | 安装 | 搜索 | 卸载 |
|------|------|------|------|
| Debian/Ubuntu | `apt install pkg` | `apt search keyword` | `apt remove pkg` |
| RHEL/CentOS | `yum install pkg` | `yum search keyword` | `yum remove pkg` |
| Alpine | `apk add pkg` | `apk search keyword` | `apk del pkg` |

---

## 定时任务

```bash
# 编辑当前用户的 crontab
crontab -e

# 格式：分 时 日 月 周 命令
# 每天凌晨 2 点执行备份
0 2 * * * /opt/scripts/backup.sh
# 每 5 分钟
*/5 * * * * /opt/scripts/healthcheck.sh
# 每周日 3:30
30 3 * * 0 /opt/scripts/weekly.sh

# 查看
crontab -l
```

---

## Shell 快捷键

| 快捷键 | 作用 |
|--------|------|
| `Ctrl+R` | 搜索历史命令 |
| `Ctrl+A` / `Ctrl+E` | 跳到行首/行尾 |
| `Ctrl+U` / `Ctrl+K` | 删除光标前/后所有内容 |
| `Ctrl+W` | 删除前一个单词 |
| `Ctrl+L` | 清屏 |
| `!!` | 重复上一条命令 |
| `!$` | 上一条命令的最后一个参数 |
| `Ctrl+Z` | 暂停进程（`bg` 恢复后台，`fg` 恢复前台） |

---

## 快速诊断套路

```bash
# 1. 系统整体状况
uptime && free -h && df -h

# 2. CPU 占用 TOP 5
ps aux --sort=-%cpu | head -6

# 3. 内存占用 TOP 5
ps aux --sort=-%rss | head -6

# 4. 哪个进程在占用 8080 端口
ss -tlnp | grep 8080
lsof -i :8080

# 5. 磁盘写入最猛的进程
iotop -obn1 | head -10

# 6. 最近 10 分钟的系统错误
journalctl -p err --since "10 min ago" --no-pager
```

---

## 总结

grep、awk、sed 是 Linux 文本处理三剑客，分工明确：

| 工具 | 类比 | 核心用途 |
|------|------|----------|
| `grep` | 筛子 | 过滤和搜索文本行 |
| `awk` | 计算器 | 按列提取 + 统计计算 |
| `sed` | 编辑器 | 批量替换和行操作 |

每天写一行 Shell，日积月累就是生产力。
