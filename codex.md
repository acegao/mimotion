# 项目工作约定

## 目录职责

- `.github/workflows/`：GitHub Actions 工作流；定时、补执行和权限配置只放这里。
- `runtime/execution_state.json`：当天执行时段的唯一状态账本；按北京时间覆盖，不保留每日历史文件。
- `main.py`：刷步业务入口。
- `util/`：可复用的 Python 支撑代码。
- `local/`：本地运行相关文件。
- 根目录脚本：仅保留项目级维护脚本，使用小写蛇形命名。

## 修改规则

- 工作流使用明确的北京时间，并为重复触发和并发执行设置保护。
- 自动补执行必须有每日上限，且每次运行最多补 1 个缺失时段，只统计成功完成的刷步任务。
- 正常执行与补执行必须共用同一个并发锁；每次执行前重新读取状态账本。
- 并发锁必须保留完整等待队列，避免被后续巡检替换。
- 密钥仅通过 GitHub Secrets 或 Variables 读取，不写入代码、提交和日志。
- 不修改 `.env`、密钥、CI/CD 权限或发布配置，除非获得明确授权。
- 先更新本约定，再实施与约定冲突的结构或流程变更。

## 验证

- Python：`python -m compileall main.py util execution_reconciler.py`
- Shell：`bash -n cron_convert.sh`
- 工作流：解析全部 `.github/workflows/*.yml`，并检查触发器、权限和并发配置。
- 提交前查看 `git diff --check` 和 `git status --short`。
