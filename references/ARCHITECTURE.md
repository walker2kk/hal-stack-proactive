# Hal Stack Proactive — Architecture

## 整体架构

Hal Stack Proactive 是一站式主动自我进化AI代理框架，整合了最佳实践开箱即用。

```
┌─────────────────────────────────────────────────────────┐
│                     用户交互层                            │
├─────────────────────────────────────────────────────────┤
│  • 上下文优化：根据对话复杂度懒加载                       │
│  • 智能模型路由：简单任务用便宜模型                       │
│  • 高置信度本能自动注入：ECC学到的模式                     │
└─────────────┬─────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────┐
│                      记忆层                               │
├─────────────────────────────────────────────────────────┤
│ 🔥 HOT  (memory/hot/)       - 当前会话、活跃任务          │
│ 🌡️ WARM (memory/warm/)      - 用户偏好、稳定配置          │
│ ❄️ COLD (MEMORY.md)         - 长期总结、历史决策          │
│ 📊 Ontology (memory/ontology/) - 结构化知识图谱           │
│ 🧠 ECC (instincts/)         - 持续学习的原子本能           │
└─────────────┬─────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────┐
│                    持续学习层                             │
├─────────────────────────────────────────────────────────┤
│  • .learnings/ - 分类日志（LEARNINGS.md/ERRORS.md/...）   │
│  • ECC 本能 - 自动检测模式，重复增加置信度                 │
│  • promote-learning - 高价值经验升级到系统提示文件         │
└─────────────┬─────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────┐
│                     心跳调度                              │
├─────────────────────────────────────────────────────────┤
│  • 按间隔检查，跳过安静时段                               │
│  • 缓存保温：55分钟间隔保持Anthropic缓存暖身                │
│  • Token预算检查，超预算提醒切模型                         │
└─────────────────────────────────────────────────────────┘
```

## 模块职责

| 模块 | 职责 | 入口 |
|------|------|------|
| `context-optimizer.py` | 推荐当前请求应该加载哪些文件，最小化上下文 | `hal-stack context-recommend` |
| `model-router.py` | 根据请求复杂度推荐模型，省钱 | `hal-stack route-model` |
| `heartbeat-optimizer.py` | 智能心跳调度，减少不必要检查 | `hal-stack heartbeat-check` |
| `token-tracker.py` | 跟踪每日Token使用，预算报警 | `hal-stack budget-check` |
| `memory-tiering.py` | 整理记忆到HOT/WARM/COLD三层 | `hal-stack organize-memory` |
| `ontology.py` | 知识图谱CRUD，关系约束验证 | `hal-stack ontology ...` |
| `ecc-observe.py` | ECC持续本能学习 | `hal-stack instincts ...` |
| `promote-learning.py` | 将learnings升级到系统文件 | `hal-stack promote-learning ...` |
| `hal-stack` | 统一CLI入口 | 直接用 `hal-stack <command>` |

## 整合点

### 钩子集成

OpenClaw钩子 `post-user-prompt` 每次用户消息后触发：
- 现在占位，保持钩子结构
- 未来可以开启自动模式检测

### 安全设计

- **绝不覆盖**已有用户文件，只创建不存在的
- 安装前自动备份到 `backups/`
- ECC本能存在 `instincts/` 不碰核心配置
- 所有操作都是纯本地，不联网

## 使用流程

1. **新装**：运行 `./install.sh` → 启用钩子 → 重启会话
2. **日常使用**：
   - 自动：上下文优化、ECC观察（手动学习）、心跳调度
   - 每周：`hal-stack organize-memory` → 整理记忆分层
   - 有了学到的经验：`hal-stack promote-learning --promote LRN-xxx` → 升级到系统文件

## 目录位置（安装后）

```
~/.openclaw/workspace/
├── AGENTS.md              # 优化后的上下文策略
├── HEARTBEAT.md          # 定期检查清单
├── SOUL.md               # 你的身份
├── IDENTITY.md           # 身份元数据
├── USER.md               # 用户信息
├── MEMORY.md             # 长期精选记忆
├── TOOLS.md              # 工具配置
├── scripts/
│   └── hal-stack         # 统一CLI入口（软链）
├── memory/
│   ├── hot/              # HOT 层级
│   ├── warm/             # WARM 层级
│   └── ontology/         # 知识图谱
├── .learnings/           # self-improvement 日志
└── instincts/
    ├── personal/         # 个人全局本能
    ├── project/          # 当前项目本能
    └── cache/            # 观察缓存
```
