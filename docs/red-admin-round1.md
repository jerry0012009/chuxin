# Chuxin 红色行政风格 · 第一轮预览

日期：2026-11-23。本轮用于确认信息结构和视觉方向，不是正式验收。系统展示名暂用 **高原人员身心调节系统**，待甲方确认；样稿不使用政府徽标或网站素材。

## 版本和环境

| 项目 | 核对结果 |
| --- | --- |
| 现网 | `/opt/chuxin/current` 仍指向 `9642faa-eu`，健康检查通过。目录名不是源码提交证明：制品未嵌入完整提交号。JAR 和首页 HTML 的 SHA-256 与冻结记录一致。 |
| 原始源码冻结 | `f3d5cb3`，本地标签 `baseline/pre-redesign-2026-11-22`。 |
| GitHub 源码冻结 | `fd88b00`，标签 `baseline/github-pre-redesign-2026-11-22`。 |
| 改前截图基线 | `06d9fa78f239e7e199af67b2486b9613de3d887c`：本地 `main` 与 GitHub `main` 一致，工作区干净，前端源码和静态素材与 GitHub 冻结标签一致。 |
| 改后 | `preview/red-admin-round1`，从 `06d9fa7` 建立的独立工作树。 |

改前 `chuxin-design-before`（`127.0.0.1:28110`）和改后 `chuxin-design-red1`（`127.0.0.1:28111`）分别使用独立 Compose 网络和 MySQL 卷。不使用现网库、账号或密钥。改后访问 `http://127.0.0.1:28111/chuxin-vue/login`；远程在有测试主机 SSH 权限的电脑上转发该端口：

```sh
ssh -N -L 28111:127.0.0.1:28111 <SSH用户>@31.220.80.196
```

普通测试账号 `preview_round1`，密码单独提供。预览未开公网入口。手机效果可查看图册，或在浏览器设备模式中交互。改前、改后截图均使用同样的测试事项和浏览器参数（Chromium 1440×900、iPhone 13 模拟 390×844，长页为全页截屏），不是直接在现网构造数据。

## 范围和修改文件

参考[西藏政务服务网](https://www.xzzwfw.gov.cn/index/)的个人服务和「一件事」组织方式：先显示个人待办及进度，再提供常用服务；详情以编号、状态和动作组织办理流程。采用深红主色 `#8d2028`、浅灰页面底、白色细边框卡片及 Lucide 线性图标。

| 文件 | 修改 |
| --- | --- |
| `frontend/src/pages/auth/LoginPage.vue` | 深红页眉、账号表单、角色和登录/注册切换；保留现有校验、部门与邀请码字段。 |
| `frontend/src/pages/user/HomePage.vue` | 工作台优先显示当前测评、今日干预、近期量表记录；保留常用服务入口。 |
| `frontend/src/pages/user/AssessmentTaskCenterPage.vue` | 任务摘要、必办进度、编号状态清单和继续入口；步骤由后台返回，不写死数量。 |
| `frontend/src/pages/user/ScaleAssessmentPage.vue` | 支持从主页直接打开已完成记录页签。 |
| `frontend/src/layouts/UserLayout.vue` | 仅工作台和测评任务页面使用本轮样稿导航。 |
| `frontend/src/components/ui/ServiceMasthead.vue`、`frontend/src/lib/service-preview.ts` | 共用样稿页眉和名称。 |
| `frontend/src/styles/service-preview.css`、`frontend/src/main.ts`、`frontend/index.html` | 共用样式、响应式布局、浏览器预览标题及禁止索引声明。 |
| `backend/src/main/java/chuxin/interventiontasks/InterventionTaskService.java` | 修复既有 500：同一素材跨计划合并时，先取得可变的记录 ID 列表。无数据库迁移和评分变更。 |
| `frontend/tests/red-admin-preview.mjs` | 隔离环境测试数据、对照截图及关键交互回归。 |
| `frontend/tests/record-and-doctor.smoke.spec.ts`、`frontend/tests/role-guard.smoke.spec.ts` | 更新与旧首页结构及旧登录标题绑定的断言。 |
| `docs/red-admin-round1.md` | 预览交付说明与基本测试记录。 |

## 基本测试结果

| 检查 | 结果 |
| --- | --- |
| 前端正式构建、类型检查 | 通过；构建仍提示既有的包体积警告。 |
| 前端单测 | 10 个文件、32 项通过。 |
| 改前浏览器对照 | 桌面和手机均完成登录、进入测试任务及截图。基线的重复素材故障保留在改前环境。 |
| 改后三页 | 桌面 1440px、手机 390px、窄屏 320px 通过；检查无横向页面溢出，步骤标题可正常换行。 |
| 创建测试事项 | 两套隔离环境均发布同样的五项任务（量表、神经心理、对话、语音、表情），并准备干预及 GAD-7 历史记录。 |
| 登录与入口 | 角色/注册表单切换、普通账号登录、进入详情、继续至正确量表、查看历史报告、打开已完成列表和疗愈计划均通过。 |
| 问卷回归 | 新账号注册后可见 90 套自由测评；完成 GAD-7 七题并生成报告，手机端可查看记录。 |
| 干预合并 | 复现基线 500；改后同一素材跨测试计划正确合并并保留记录关联。 |
| 后端单测 | 25 通过、1 失败。`NeuropsychMetricsCalculatorTest.calculatesStopSignalSsrt`（20 预期、0 实际），`06d9fa7` 基线复跑结果相同；本轮未改计分。 |

未进行五步完整提交、真实相机/麦克风、传感器或正式验收，本轮确认五项展示和量表继续入口。甲方本轮建议确认样稿名称、工作台三项排序与五步详情呈现，再排下一轮。
