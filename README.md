# Hey, I'm Fred

AI Infrastructure Architect building **PAI**, a Personal AI Infrastructure system that turns Claude Code into a persistent, self-improving development environment.

## PAI — Personal AI Infrastructure

PAI is an open architecture that wraps Claude Code with skills, hooks, memory, and a continuously upgrading algorithm. It's not a chatbot — it's scaffolding that makes AI reliable, repeatable, and personal.

Built on [Daniel Miessler's](https://github.com/danielmiessler) [Personal AI Infrastructure](https://github.com/danielmiessler/Personal_AI_Infrastructure) framework and [Fabric](https://github.com/danielmiessler/fabric) pattern system.

**Current state (v4.0.3):**

| Component | Count | What it does |
|-----------|-------|-------------|
| **Skills** | 86 | Self-activating domain expertise — security, research, creative writing, OSINT, video production, and more |
| **Hooks** | 37 | Event lifecycle handlers — session start/stop, tool validation, memory capture, security scanning |
| **Algorithm** | v3.7.0 | 7-phase execution engine (Observe → Think → Plan → Build → Execute → Verify → Learn) |
| **Memory** | 16,700+ sessions | SQLite + FTS5 + embeddings — persistent context across every conversation |
| **Agents** | 14 types | Specialized sub-agents for engineering, architecture, research, security, design |
| **Fabric Patterns** | 240+ | Content analysis, extraction, and transformation templates |

### Core Design Principles

1. **Scaffolding > Model** — Architecture matters more than which LLM you use
2. **Code Before Prompts** — If code can solve it, don't prompt for it
3. **As Deterministic As Possible** — Same input, same output, always
4. **The Algorithm Is The Centerpiece** — Everything else exists to feed Current State → Ideal State
5. **Memory Makes Intelligence Compound** — Without persistence, every session starts from zero

### The Algorithm

Every non-trivial task runs through a 7-phase loop that transitions from **Current State** to **Ideal State** via verifiable criteria:

```
OBSERVE → THINK → PLAN → BUILD → EXECUTE → VERIFY → LEARN
   ↑                                                    │
   └────────────────────────────────────────────────────┘
```

Each phase has explicit gates. The algorithm self-improves from accumulated evidence across sessions.

## Infrastructure

| Component | Details |
|-----------|---------|
| **Hosts** | Multi-node homelab — Docker, K3s, Incus, Tailscale mesh |
| **GPUs** | NVIDIA GPU compute (CUDA, vLLM inference) |
| **Networking** | Tailscale overlay, Traefik reverse proxy, auto-TLS |
| **Observability** | Prometheus, Grafana, structured logging |
| **Backups** | Restic to B2, systemd timers, K3s + Incus state included |

## Tech Stack

- **AI/ML:** Claude Code, vLLM, RAG pipelines, embeddings, NVIDIA CUDA/DCGM
- **Runtime:** TypeScript/Bun, Python, Bash
- **Infra:** Docker, Kubernetes (K3s), Incus containers, Cloudflare Workers
- **Ops:** Prometheus/Grafana, systemd, Traefik, Tailscale, restic

## Philosophy

```
Complexity is borrowed — every layer added is future time invested.
Record your dead ends — failed approaches prevent wasted future effort.
Silent failures are worst — if it can fail, make it fail loud.
Spec/Test/Evals first — if you can't specify it, you can't trust it.
```

## Connect

- **GitHub:** [@nixfred](https://github.com/nixfred)
- **LinkedIn:** [nixfred](https://www.linkedin.com/in/frednix/)
- **Site:** [nixfred.com](https://nixfred.com)

---

*Building compounding AI infrastructure, one session at a time.*

