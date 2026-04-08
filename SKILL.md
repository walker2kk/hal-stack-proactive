# Hal Stack Proactive 🦞

一站式主动自我进化技能栈 — 开箱即用的完整Agent操作系统。

整合了最佳实践：
- 上下文优化（节省50-80% Token）
- 主动记忆架构（WAL协议 + 工作缓冲区）
- 三级记忆分层（HOT/WARM/COLD）
- ECC持续本能学习（自动从交互学习模式）
- 持续学习日志（.learnings/）
- 类型化知识图谱（ontology）
- 安全护栏（符合Hal Stack准则）

## 安装

```bash
# 解压到你的OpenClaw工作区技能目录
cd ~/.openclaw/workspace/skills
unzip hal-stack-proactive.zip
cd hal-stack-proactive
./install.sh [目标工作区路径]
```

如果不传目标工作区，默认安装到 `~/.openclaw/workspace`。

## 安装后

重启OpenClaw会话生效。技能会自动：
1. 按优化策略加载上下文
2. 钩子自动启动本能学习
3. 按WAL协议记录关键信息

## 常用命令

```bash
# 整理记忆到三级分层
hal-stack organize-memory

# 检查Token预算
hal-stack budget-check

# 验证安装
hal-stack doctor

# 查看已学习的本能
hal-stack instincts list
```

## 架构

详见 `references/ARCHITECTURE.md`

## 授权

MIT
