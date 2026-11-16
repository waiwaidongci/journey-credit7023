# 巡光展览传播归因席 · JOURNEY CREDIT

沿匿名触点路径计算吸收Markov归因，再在预算与渠道容量约束内生成关联得分情景，交由传播负责人复核。

## 真实工作流的模拟

巡光策展传播组有15位传播研究员。以往只看预约前最后一个触点，长路径与循环触点被压成渠道名单，归因数又被当作下一笔预算的因果回报。本应用把上游匿名预约路径转换为可复查的转移矩阵、移除效应和预算讨论底稿，下游为策展传播会议。没有真实投放或购买行为。

| 角色 | 页面与权限 | 典型动作 |
|---|---|---|
| admin / 传播负责人 | 六页读写、创建研究和情景、批准/退回 | 记录预算假设与批准范围 |
| analyst / 路径研究员 | 六页阅读、补路径备注、创建归因/情景；不能批准 | 比较末触点与归因，准备约束情景 |
| viewer / 策展阅读者 | 六页只读，仅获批完成情景可导出 | 阅读假设、矩阵与CSV |

批准是允许研究归档，不是授权真实支出。所有角色导出前都要求情景完成且review_status=approved。

## 启动

```bash
cp .env.example .env
docker compose up -d --build
docker compose ps
docker compose exec -T backend python -m scripts.seed_demo
```

[前端](http://localhost:18216)，[接口文档](http://localhost:19216/docs)。Nginx把`/api/`前缀去掉后代理到FastAPI，直接后端接口不加`/api`。

| 账号 | 密码 | 角色 |
|---|---|---|
| admin@xunguang.demo | Xunguang2026! | admin |
| analyst@xunguang.demo | Xunguang2026! | analyst |
| viewer@xunguang.demo | Xunguang2026! | viewer |

恰好frontend/backend/worker/db/redis五服务，全部有healthcheck和健康依赖；PostgreSQL16、Redis7分别命名卷，backend/worker共享JSON产物卷。worker每2秒刷新心跳，分别执行run和scenario两种Redis任务。ORM metadata首次建表，迁移目录为索引示例；后续结构变化需审查迁移。

## 数据与一天剧本

`xg-exhibition-paths.json`为seed89的1100条合成匿名路径，首周700、第二周400。六渠道为城市海报、策展通讯、创作者推荐、主动检索、社群分享、合作场馆。触点可重复和循环，终点包含CONVERSION/NULL；没有个人标识。模拟成本和容量只用于研究，非真实报价。首周700条中161个转化终点，基准吸收概率23%。预置首周归因和一份获批5000元讨论情景均由真实算法计算。

seed以邮箱、渠道code、批次name、路径code和基准研究名查重；只补缺失，不覆盖已有路径备注。`SEED_DEMO=true`启动自动seed，失败记录日志而不阻塞服务。

1. 08:00 许晴以analyst登录，核对首周700条路径和6个渠道，保留循环顺序。
2. 在路径页补一条匿名路径备注，确认NULL表示未转化观察终点。
3. 创建“首周路径复核”，固定移除口径为指向被移除渠道的概率流量转NULL。
4. worker建立转移计数与行归一概率，求START到CONVERSION的吸收概率，逐渠道重新求解。
5. 阅读相对移除效应、归一份额、历史归因转化数，与末触点数对照。
6. 创建5000元预算情景，将社群分享容量调为300，其余不超过渠道快照上限。
7. worker用LP求连续非负分配，检查模拟支出、剩余预算、容量和关联得分。
8. 陈照以admin复核并写明非因果、线性假设及容量边界，批准或退回。
9. 闻溪以viewer下载获批6渠道CSV；不发送投放指令、不购买广告。

## 算法与假设

**吸收链**：每条路径补START和CONVERSION/NULL，保留所有重复触点。计数按来源状态行归一。吸收终点自身概率1，未访问渠道转NULL。对START可达的暂态集合建立Q及到CONVERSION向量r，解`(I-Q)u=r`。先检查每行概率非负有限且和1、吸收终点定义，以及是否存在START可达而无路到终点的非吸收闭类；不可解/病态矩阵明确失败。不可达闭类不影响START结果，求解时排除。

**渠道移除口径**：对被移除渠道c，把所有`P[i,c]`加到`P[i,NULL]`并清零c列；c行本身转NULL。不会把前后触点跨接。每行和仍为1。相对移除效应为`(base-removed)/base`；非负数值截断只处理舍入。份额为该效应除以全渠道效应和，历史归因转化数=份额×观察转化总数。零基准转化或全零效应明确失败，不能编造等分归因。

直接路径也可以被算法表示；若包含直接转化，当前归一会把全部观察转化分配给有移除效应的渠道，结果返回direct_paths和这一说明，需业务单独审阅。种子路径均至少一个渠道。

**约束预算情景**：以每渠道`association_score=历史归因转化数/该渠道触点次数`作固定目标系数，最大化`Σscore_i*x_i`，约束`Σunit_cost_i*x_i<=budget`、`0<=x_i<=情景容量_i<=归因运行保存的渠道容量`。SciPy HiGHS求连续LP，小数触达单元允许；预算不必花完，结果报告余额。成本为正、容量/得分非负且有限；未知渠道、超容量、负/非有限预算、全零目标明确拒绝，求解后再次检查可行性。

目标只是关联指数：假设历史得分可线性延用、边际得分不随投入改变、无渠道交互和时间漂移。它不预测真实预约、增量转化或因果ROI，不自动投放。相同观测条件下的路径关联也不等于真实停用渠道的实验效果。

归因输入SHA256按路径code、渠道code稳定排序，包含批次元信息、全部路径顺序/终点/备注、渠道成本容量和方法版本；不排序路径内部触点。情景hash包含完整归因结果快照、预算、容量覆盖与LP版本，另保存attribution_hash用于追溯。各运行参数与结果持久化。

线性代数与求解器接口参考：[NumPy solve](https://numpy.org/doc/2.2/reference/generated/numpy.linalg.solve.html)、[SciPy linprog](https://docs.scipy.org/doc/scipy-1.15.1/reference/generated/scipy.optimize.linprog.html)。移除策略和归一方式是本项目明确固定的模型选择，不宣称唯一归因标准。

## 工程与页面

六页为传播总览、路径与渠道、研究配置、归因结果、预算情景、研究留痕。JourneyBatch/Journey/Channel/AttributionRun/BudgetScenario五实体各有模型、schema、service、route、前端API/store与页面。User/Audit是横切实体。

| 部分 | 技术 |
|---|---|
| 后端 | Python3.11 / FastAPI / SQLAlchemy / NumPy / SciPy HiGHS |
| 前端 | React18 / TypeScript / Vite6.4.6 / Lucide |
| 数据 | PostgreSQL16 / Redis7 AOF |
| UI | 展览横向折页、沙色/深橄榄/朱红；Noto Serif SC + Noto Sans SC |

```
backend/src/{models,schemas,services,controllers,routes,middlewares,utils,constants,config}
backend/src/{main.py,worker.py}
backend/scripts/seed_demo.py
backend/migrations/001_initial.sql
frontend/src/{api,stores,types,components,hooks,pages,router,utils,constants}
```

AttributionSummary跨首页/结果/情景共用，CreditBars跨首页/结果共用，BatchSelector跨来源/配置共用；通用DataTable/StatusBadge/Notice、useAction/useResearchData及format独立。角色枚举`backend/src/constants/roles.py`与运行枚举`status.py`对应`frontend/src/constants/enums.ts`，权限路由和worker真实使用。JWT8小时、PBKDF2-SHA256、每次查数据库角色；审计覆盖登录、路径备注、任务完成和情景复核。错误、登录限流是两个独立中间件。

## 配置和开发

| 变量 | 默认 | 用途 |
|---|---|---|
| COMPOSE_PROJECT_NAME | journey-credit | 命名空间 |
| FRONTEND_PORT | 18216 | 前端 |
| BACKEND_PORT | 19216 | 后端 |
| DB_PORT | 17716 | PostgreSQL宿主映射 |
| JWT_SECRET | local-journey-credit-change-this-key | 本地演示值，部署前更换 |
| SEED_DEMO | true | 启动自动seed |

本地Python3.11安装requirements，设置DATABASE_URL/REDIS_URL；`cd backend && uvicorn src.main:app --reload`，另起`python -m src.worker`。前端`npm install && npm run dev`，本地为`/api`配置后端代理。标准演示以Compose为准。

```bash
docker compose down -v --remove-orphans
```

真实测试、截图和TESTING在项目外`../../test-artifacts/gb-0012/`。源码不含截图/日志/测试报告，.env和缓存不提交。

## 已知边界

合成冻结匿名路径，无上传或实际投放；仅可补备注，渠道配置当前只读。观察路径的一阶Markov及转NULL策略有偏差，未做因果识别、时间归因窗或高阶路径。LP无收益递减/协同/整数约束，不把指数解读为真实ROI。单worker无running自动恢复、事务outbox或分布式锁，中断需重提；登录限流仅进程内。首次建表不是完整迁移链；网络字体失效时回退。

## License

MIT，见LICENSE。
