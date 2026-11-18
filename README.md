# pfstack（potafree stack）

> potafree 的 agent 协作开发方法，2026-11-18 从 Shinphony（iOS/macOS/Windows 终端 App + Go 守护进程 + Cloudflare Worker）一路踩坑总结而来。
> 目标：换一个项目也能直接套用。例子里的工具名只是参考，见 `templates/`。
> 部分做法借鉴自 poteto 的 pstack（小步可验证、暂停可恢复、先解释数字），其余是我们自己的经验。

一句话：**一个人定方向，agent 做实事；每一步都有证据、能恢复、可回滚；踩过的坑变成规则和测试。**

---

## 1. 角色：一个协调者，多个实施者

| 角色 | 做什么 | 不做什么 |
|---|---|---|
| 协调者（主会话） | 和用户谈需求，写计划和验收标准，审 diff 和每张截图，合并，发布，独占共享资源（模拟器、真机、生产部署） | 实施者写代码时不同时改同一处 |
| 实施者（worker，终端里的独立 agent） | 一个任务、一个分支、一个 worktree，按计划写代码，自跑最低档验证，写实施说明 | 不嵌套启动 agent，不碰共享资源，不自行扩需求，不合并、不发布 |

- **按难度选模型：** 机械活（改名、文案、渲染、测试更新、验证运行）用便宜快的模型；跨模块设计、并发、协议、安全、原生平台用最强的模型。计划里写明选择。
- **机器负载有上限：** 同时最多 2 个 worker、1 个模拟器；重命令 `nice -n 10`；缓存和临时文件放大盘。
- **worker 的父地址用当前会话的真实地址**（`--parent "$HC_TERMINAL_ID"`），不要抄旧地址。

## 2. 不丢工作：小步、提交、推送、留状态

- **每个改动都走分支 + PR**，协调者审完合并；合并或自己提交后立即推送主线。
- **实施者每完成一个可验证的小单元：检查 → 提交 → 推送。** 超过几分钟的工作不允许只存在本机。
- **每次汇报和暂停都写 `STATE.md`**：已完成、进行中、下一步、待决问题、怎么验证。新会话（或机器重启后）读它就能接着做，不用重新推导。
- 远端用 SSH（HTTPS 钥匙串重启后可能被锁）。

## 3. 计划先行，轮次有上限

- 用户反馈 → 协调者写 plan + 验收标准 → **用户确认后才开工**。范围变化要重新确认。
- **最多 3 轮**「实施 → 验收 → 审查」。第 3 轮后还有 P0–P2 就停下交给用户裁决，不开第 4 轮，也不改名重置计数。
- 计划、实施说明、验收、审查都存进 `docs/iterations/<id>/round-NN/`，记录被测的确切源码版本。**agent 说「完成了」不算证据。**

## 4. 证据分档：用能证明它的最低档

| 档 | 什么时候 | 怎么做 |
|---|---|---|
| A（默认） | 颜色、间距、文案、布局、组件替换 | 本机渲染真实界面截图 + 静态检查 + lint + 测试差分，几秒到几分钟 |
| B | A 证明不了：键盘、时序、动画、WebView、手势、原生能力 | 一台设备、一个主题、相关场景，由协调者跑 |
| C | 提审 / 对外发版前一次 | 全设备 × 全主题矩阵 |

- 计划里写明本轮用哪档；用 B 必须说明 A 为什么不够。证明不了的项列为「待 C」，不得声称已验收。
- **时序问题录一次视频再抽帧**，不能凭操作后的一张截图判失败；场景脚本打 `PHASE` 标记，录完再按标记切帧，不重跑。
- **只用专用设备**（写死 UDID，永不用 `booted`），不碰别的项目的设备；开发版永不装在用户的正式/TF 版本上（用独立 bundle id）。

## 5. 设计有唯一真相

- `DESIGN.md` 是视觉和交互的唯一标准，只由协调者改。新 UI 用自己的组件层。
- **每张截图都审**（Impeccable / HIG 启发式），逐张记录结论：明显缺陷当轮修；和 DESIGN 冲突的建议不改，列成「设计冲突」表交用户裁决，裁决后写回 DESIGN。
- 用户的口头决定（例如「示意图可以，但不要装饰」）当场写进 DESIGN，附日期。

## 6. 踩过的坑变成规则

- 每个新坑 → `docs/review_rules.md` 加一条规则；能自动检查的 → 加进 `tool/review_lint.py`（每条可单独跑）。
- 每次审查都跑 lint + 人工规则清单。
- 例子：原生插件必须注册（R30）；测试数据里不许出现真实主机名和用户名（M84，公开导出前再扫一遍）；构建号替换不许盲目 `sed`（曾经改坏一个 id，于是写了专用脚本）。

## 7. 状态不变式 + 模型测试（时序 bug 的解法）

- 时序类问题（推送 vs 快照 vs 点击 vs 时钟、通知、试用节奏…）**先写规则再写测试**：每条规则一个编号（A1、LA3、ON7…）。
- 测试 = 一个小的参考模型 + 带种子的随机事件序列 + 每个事件后检查全部规则。种子在 CI 固定；失败的序列自动缩短，保存成命名回归用例。
- 三层：纯逻辑模型测试 → 真实界面驱动测试（假时钟、假支付、假网络）→ 模拟器场景脚本（命名场景 + PHASE 标记，用来录屏）。
- 现场发现的回归：新规则编号 → 生成器里加用例 → 审查规则里加一行。

## 8. 先解释数字，再相信数字

- 测试只看**相对基线的新失败**（测试差分脚本），不被历史失败淹没。
- 计时类基准在全量里失败，**先单独重跑**；单独也失败或 profile 说明了变慢原因才算回归，并写进验收。
- 外部服务报错先判断是不是对方故障（例如 App Store Connect 500/404），不要据此去「修」自己的东西。

## 9. 授权分层

- **常驻授权**（用户一次说清，记进 memory）：审过的安全更新发布、测试版上传、某个服务的部署。
- **每次询问：** 提审 / 上架、其他线上服务部署、任何对外可见或难撤销的动作。
- 一次授权不外推到别的场景。自动模式拒绝了就问用户，不绕。

## 10. 安全卫生（硬规则）

- 不打印 token、密码、审核账号；凭据只在脚本内部读取。
- 仓库里的副本隐去主机名和用户名；测试数据只用 `example-*` 主机。
- 删除目录一律 `rm -rf "${D:?}"`；删除或覆盖前先看目标。
- 不改全局工具链和共享 SDK；需要打补丁的让用户执行。
- 临时预览服务（局域网 http）只暴露一个复制出来的目录，看完就关；生成的 HTML 一律带 `<meta charset="utf-8">`。

## 11. 发布流水线脚本化

- 每个对外步骤都是脚本，默认只读预检，显式参数才写：`准备（dry-run）→ --submit → --submit --final`。
- 构建号递增用专用脚本（只替换独立出现的数字，不碰 hex id），并处理网络重试。
- 官网和 App 版本用门控变量切换（「App Store 显示新版后才露出新文案」），可以先合并、后上线。
- 发布后核对：线上地址、校验和、可复现构建、公开导出的脱敏扫描。

## 12. 和用户沟通

- 回复短，**行动项在前**，中文 TLDR。
- 后台任务没结果前不预测结果；需要用户做的事明确列出，并写清要测什么。
- 需要用户在终端执行的命令，让用户用 `! <命令>` 在会话里跑。

---

### 新项目起步清单（模板在 `templates/`）

1. 建 `AGENTS.md`（入口）、`DESIGN.md`（唯一设计标准）、`docs/review_rules.md` + `tool/review_lint.py`、`docs/design/state_invariants.md`。
2. 建测试差分基线脚本和本机渲染脚本（A 档）。
3. 写死专用设备 / 环境的标识；开发版独立 bundle id。
4. 定下常驻授权和必须询问的动作，记进 memory。
5. 第一个迭代就按 plan → 确认 → worker → A 档 → 审查 → PR 合并 → STATE.md 跑一遍。

## 仓库结构

```
README.md                         本文
templates/AGENTS.md               项目入口：角色、流程、硬规则（复制后改项目名和路径）
templates/DESIGN.md               设计唯一真相的骨架
templates/docs/review_rules.md    审查规则（人工 + 自动）
templates/docs/design/state_invariants.md   状态不变式模板（规则编号 + 事件表）
templates/docs/iterations/_example/         plan / implementation / acceptance / STATE 模板
templates/tool/review_lint.py     规则注册式 lint 骨架（每条规则可单独跑）
templates/tool/test_diff.sh       测试差分：只报相对基线的新失败
templates/tool/next_build.py      构建号递增（只换独立出现的数字，不碰 hex id）
templates/tool/model_check.py     模型测试小框架：种子、事件生成、每步检查、失败缩短
templates/tool/spawn_worker.sh    在 hc 里启动一个实施者 worker
skill/pfstack/                    Claude Code skill（init / check / update）+ CLI 脚本
```

## 用法

**推荐：Claude Code skill。** 装一次，所有项目可用：

```sh
gh repo clone chux0519/pfstack ~/repos/pfstack
ln -sfn ~/repos/pfstack/skill/pfstack ~/.claude/skills/pfstack
```

然后在新项目里对 Claude 说 `/pfstack`（或「用 pfstack 初始化这个项目」）。它会：列出要加的文件 → 一次问清项目名、设备、
授权、禁用名字、测试命令 → 复制模板并填好占位 → 建 `CLAUDE.md`（`@AGENTS.md`）→ 跑 lint、记测试基线 → 在 `pfstack-init`
分支提交，问你要不要推送。已有项目说 `/pfstack check` 看缺什么，`/pfstack update` 拉新模板（不覆盖你的改动）。

**也可以直接用 CLI：**

```sh
python3 ~/repos/pfstack/skill/pfstack/scripts/pfstack.py init <dir> [--dry-run]
python3 ~/repos/pfstack/skill/pfstack/scripts/pfstack.py check <dir>
python3 ~/repos/pfstack/skill/pfstack/scripts/pfstack.py update <dir>
```
