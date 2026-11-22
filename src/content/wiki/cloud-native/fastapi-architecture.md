---
title: "FastAPI 架构：类型驱动、DI 管道与异步模型"
domain: "cloud-native"
domainLabel: "云原生"
created: "2026-09-07"
updated: "2026-09-07"
type: "concept"
tags:
  - "架构"
  - "监控"
sources:
  - "https://zacharyxue.github.io/blog/fastapi-deep-dive/"
confidence: "high"
summary: "FastAPI 的本质是「类型标注即一切」——同一份类型标注同时是校验（Pydantic）、文档（OpenAPI）和编辑器提示；依赖注入不是简单的「注入数据库连接」而是可组合的请求处理管道（依赖图拓扑执行、请求内缓存、yield 清理）；性能与正确性的关键在 async def/def 决策规则和分层不越界。"
---
## 一句话本质
**FastAPI 的本质是「类型标注即一切」**——同一份类型标注同时是校验（Pydantic）、文档（OpenAPI）和编辑器提示；依赖注入不是简单的「注入数据库连接」而是可组合的请求处理管道（依赖图拓扑执行、请求内缓存、yield 清理）；性能与正确性的关键在 async def/def 决策规则和分层不越界。

## 方法要点

- **本质构成** = Starlette（ASGI 框架）+ Pydantic（类型即校验）+ 类型标注驱动的自动文档；定位不是替代 Flask/Django——只要几个简单 REST endpoint、不要异步不要文档时，Flask 更轻，选型拿场景说话。
- **参数三分类唯一规则**：路径模板 {} 中→路径参数；Pydantic BaseModel 类型→请求体；其余简单类型（str/int/float/bool）→查询参数。`response_model` 双重价值：文档生成 + 数据过滤器（只序列化声明字段，ORM 对象里的 password_hash 零成本防泄漏）。
- **DI 是可组合的管道**：依赖可以依赖其他依赖（解析依赖图按拓扑序执行）；同一请求内同一依赖只执行一次（结果缓存）；yield 依赖配合 try/finally 做资源清理；`dependencies=[...]` 只执行不取返回值→权限守卫，挂到 APIRouter 上整组路由统一生效。
- **请求生命周期**：中间件→异常 handler→路由匹配→依赖解析→路径操作→响应序列化/返回。**中间件 vs 依赖判据**：跨所有路由的逻辑（计时/CORS/链路追踪）用中间件；按路由/路由组隔离的逻辑（认证/权限/DB 连接）用依赖。
- **async def/def 决策规则**：异步 I/O（httpx/asyncpg/aioredis）用 async def 让出事件循环；同步 I/O 或 CPU 密集（pandas/PIL/requests）用 def，FastAPI 自动丢线程池（run_in_threadpool）不阻塞主循环；**反模式**：async def 里调同步阻塞（time.sleep）冻结整个事件循环——生产环境最常见的性能杀手。
- **BackgroundTasks 的真相**：不是另起线程并行，而是响应返回后、Starlette 关连接前在同一进程内顺序执行——适合发邮件/写日志等轻量操作；真正异步后台（30 秒报表）必须 Celery/ARQ 独立 worker+消息队列（可重试可持久化）。
- **分层架构原则**：Router 只做参数提取/调 service/返回响应，Service 只做业务逻辑/事务/权限，Repository 只做 SQL/持久化——每层只知道自己下面那一层（Router 不知 SQL，Service 不知 HTTP）；自定义异常体系（AppException + 全局 exception_handler）让业务层与 HTTP 解耦。
- **异步 SQLAlchemy 两大坑**：relationship 懒加载在 async 下报 MissingGreenlet，必须 selectinload()/joinedload() 显式预加载；commit 后必须 expire_on_commit=False，否则访问对象属性触发过期刷新，async 下直接炸。

## 记住点
类型即校验即文档；DI 是管道不是注入；async def 里睡一秒，全世界陪你等一秒；路由-服务-数据三层只知下一层。

## 相关
- [容器运行时链路](/wiki/cloud-native/container-runtime-chain)（服务部署运行的底座）
- [Linux 运维判据](/wiki/cloud-native/linux-ops-heuristics)（进程/端口/日志排障上下文）