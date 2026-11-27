# 曜尺仪器·日晷影线校订

为展教日晷的转台影线投影生成放样和返校清单。

## 业务背景

曜尺仪器展教装调组 · 6 人，维护馆内日晷演示台

装调员用可转动投影灯和转台走完一整天的模拟时间，再把测角仪的逐点读数录进电子表格，人工校订展台用的影线路径。

- 模拟时刻在 23:59 与 00:00 相邻，从分钟数直接拟合会跳变。
- 测角仪回到正北时从 359° 跳到 0°，普通角度相减会把微小修正当成一圈。
- 返校与直接放样的点混排，装调员容易把尚待复测的影线画上新底板。

- 上游输入为读取固定夹具编号下的转台角度、干涉仪参考角与灯臂俯仰测点。CSV 以各轮试样独立编号。
- 下游交付为获取跨正北的影线和超限点，交给展教装调组分批返校及放样。

## 算法与数据口径

**三角周期编码与双基准岭回归**

以 sin(2πm/1440)、cos(2πm/1440) 编码模拟分钟；同时以正弦和余弦编码转台方位角，并拼接灯臂俯仰。以参考角至刻度角的最短有符号差为目标，训练集拟合标准化及固定正则系数的岭回归。独立留出报告原始分钟/角度基线及周期模型的修正量 MAE。修正角归一至 [0,360)，跨正北两侧保持连续。

种子文件名为 `曜尺_三舱影线转台校订_2026-11-25.csv`。CSV 按下表顺序提供字段，最多 5,000 行。样本编号在同一数据版本内唯一。服务用规范化行内容的 SHA-256 对导入去重并保留实际计算所用的输入版本。

| 列 | 用途 | 类型 | 范围或选项 |
|---|---|---|---|
| `sample_id` | 影线测点 | text | 见业务口径 |
| `split` | 测次 | text | `标定`、`留出`、`待放样` |
| `minute` | 模拟分钟 | number | 0 至 1439 |
| `azimuth_deg` | 转台刻度角（°） | number | 0 至 360 |
| `pitch_deg` | 灯臂俯仰（°） | number | -8 至 8 |
| `reference_deg` | 参考方位角（°） | number | 0 至 360 |

计算参数为 **返校阈值（°）**，取值 0.2 至 10，默认 2.5。在 `POST /api/runs` 的 JSON 中使用 `parameter` 字段传入。

## 一次当班交接

1. 08:25 装调员导出曜尺_三舱影线转台校订_2026-11-25.csv。
2. 08:40 分析员核对 120 个标定点、48 个留出点与 6 个待放样点。
3. 09:00 输入 2.5° 返校阈值，提交周期校订单。
4. 09:05 核对留出误差及 23:59、00:01 两点的修正量。
5. 09:15 检查 YC-P01 经过正北、YC-P03 须返校，下载影线路径清单。
6. 09:28 复核员签发可放样点，装调组按签发记录划线。

## 快速启动

在本项目根目录执行。复制示例环境前先检查是否已有 `.env`。示例中的连接口令供本机演示，部署时为每个项目设置独立的 JWT 密钥和数据库口令。

```sh
test -e .env || cp .env.example .env
docker compose config --quiet
docker compose up -d --build --wait
docker compose exec -T backend python -m scripts.seed_demo
curl -fsS http://127.0.0.1:19450/healthz
```

API 使用 `http://127.0.0.1:19450`，接口定义为 `/openapi.json`。数据库端口为 `127.0.0.1:17950`。Nginx 网关、FastAPI、Python worker、PostgreSQL 16 和 Redis 组成完整服务。数据库、队列缓存和 CSV 文件使用各自的命名卷。

| 演示账号 | 权限 |
|---|---|
| `analyst@demo.local` | 读取，导入 CSV，提交计算 |
| `reviewer@demo.local` | 读取，签发或暂缓交接 |
| `viewer@demo.local` | 只读，下载结果和已签发的交接单 |

演示账号共用密码 `Yangfan-demo-2026`。关闭自动初始化可设 `SEED_DEMO=false`，也可以执行上述 seed 命令手动初始化。已有数据和账号保留原有内容。

## API 流程

| 操作 | 接口 | 要点 |
|---|---|---|
| 获取 JWT | `POST /api/auth/login` | JSON 包含 `email` 和 `password`。后续请求传 `Authorization: Bearer <token>` |
| 查看数据 | `GET /api/datasets` | 返回数据版本与校验和。附加 `/{dataset_id}/csv` 下载有效 CSV 样板 |
| 导入数据 | `POST /api/datasets` | JSON 包含 `name` 与完整 CSV 字符串 `csv` |
| 创建计算 | `POST /api/runs` | JSON 包含 `dataset_id`、`label`、`parameter`，返回计算 ID |
| 取结果 | `GET /api/runs/{run_id}` | 等待 `succeeded` 或 `failed`，完成后附加 `/csv` 下载结果 |
| 查业务交接建议 | `GET /api/domain/shadow-stencil/{run_id}` | 返回项目专用的工位、样本或处置摘要 |
| 签审 | `POST /api/runs/{run_id}/review` | JSON 包含 `decision`、`samples`、`note` |
| 下载交接单 | `GET /api/runs/{run_id}/handoff.csv` | 签发后可下载，包含选中样本与交接记录 |
| 查审计 | `GET /api/audit` | 最近 100 条业务变更 |

可用 Python 标准库解析登录返回的 JWT：

```sh
API=http://127.0.0.1:19450
TOKEN=$(curl -fsS "$API/api/auth/login" -H 'Content-Type: application/json' \
  -d '{"email":"analyst@demo.local","password":"Yangfan-demo-2026"}' \
  | python3 -c 'import json,sys; print(json.load(sys.stdin)["token"])')
curl -fsS "$API/api/datasets" -H "Authorization: Bearer $TOKEN"
```

## 开发与运行

- `backend/src/business` 实现本项目的输入、算法和业务交接，主要模块为 `algorithm.py`, `angles.py`, `calibration.py`, `demo.py`, `observations.py`, `profile.py`, `routes.py`, `stencil.py`。
- `backend/src/routes`、`controllers`、`services` 处理 HTTP、数据版本、异步执行、签审、导出和审计。
- `backend/src/models`、`schemas` 定义持久化和接口数据。角色 `analyst/reviewer/viewer`、任务状态 `queued/running/succeeded/failed`、决定 `approve/hold` 定义在 `backend/src/constants/workflow.py`，被路由、worker、请求模型和数据模型使用。
- `backend/migrations/bootstrap.py` 初始化数据库表。修改代码后可执行 `docker compose up -d --build --wait` 重新装载。
- 本地开发可以先用 Compose 单独启动 `db` 和 `redis`，再在 `backend` 中按 `requirements.txt` 安装 Python 3.11 依赖。通过 `DATABASE_URL`、`REDIS_URL`、`JWT_SECRET`、`JWT_ISSUER` 和可写的 `ARTIFACTS_DIR` 配置进程，运行 `uvicorn src.main:app --port 8000` 与 `python -m src.worker`。开发机的 Redis 可使用本地实例或为容器配置临时回环端口。
- `docker compose down` 停止本项目服务并保留数据卷。需要清空模拟数据时手动执行 `docker compose down -v --remove-orphans`。
- 业务示例均为模拟数据。模型输出供交接与现场复核。项目授权沿用工作区及交付方约定。

[验收记录](../../test-artifacts/yangfan-11-sundial-shadow/TESTING.md)
