# Astro Dev Server 启动问题

## 问题现象

在 bash 工具中通过 `npm run dev -- --host 0.0.0.0 &` 启动 Astro 开发服务器时，服务器无法正常监听端口，进程被提前终止。

## 根因

bash 工具的 **timeout 机制**与后台进程的交互问题：

1. `&` 将进程放入后台，但 bash 工具在超时后会**杀死整个进程组**
2. Astro dev server 启动需要约 2-3 秒（类型生成 + content sync + vite 优化），在完成初始化前超时即被 kill
3. bash 工具的超时是针对整个 shell session 的，不是针对单个命令的

## 解决方案

使用 `nohup` 解耦进程与当前 shell session：

```bash
nohup npx astro dev --host 0.0.0.0 > /tmp/astro-dev.log 2>&1 &
```

- `nohup`：忽略 SIGHUP，进程不受终端关闭影响
- `> /tmp/astro-dev.log 2>&1`：重定向输出，方便查看启动日志

## 验证

```bash
# 查看启动日志
cat /tmp/astro-dev.log

# 确认端口监听
ss -tlnp | grep 4321

# 验证可访问
curl -s -o /dev/null -w "%{http_code}" http://localhost:4321
```
