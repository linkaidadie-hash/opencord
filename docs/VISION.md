# OpenCord Vision

[English](./VISION.md) | [简体中文](./VISION.zh-CN.md)

> Why OpenCord exists. Where it's going. What we won't compromise on.

OpenCord is not a forum. It is not a chat app. It is not a "Discord alternative".

OpenCord is a foundation for communities that don't want to live inside someone else's walls.

---

## The Problem

We have many "communities" today. Almost none of them are actually communities.

A real community needs:
- Members who belong to it, not to a platform
- Conversations that the community owns
- Rules that the community makes and enforces
- Data the community can take with them
- Memory that survives platform shutdowns

What we have instead:
- Group chats where the chat platform owns the membership graph
- Forums where the forum software owns the data export
- Discord servers where Discord owns the moderation tools
- "AI features" that are actually surveillance wrapped in a chatbot

The platforms tell us: "We'll be your home. We'll be your audience. We'll be your AI."

And then they change the rules, raise the prices, or get acquired.

---

## What We Believe

### 1. Communities should own their substrate

A community's identity, data, and rules should be portable. If the platform dies, the community should not die with it.

This means: **self-hostable. open source. data export. no proprietary formats.**

### 2. AI should be a tool, not a landlord

A community's AI should be:
- **Swappable** — use OpenAI, DeepSeek, MiniMax, Ollama, or any OpenAI-compatible endpoint
- **Auditable** — log every call, every token, every cost
- **Replaceable** — the AI never becomes the lock-in

If a community wants to switch LLM providers next year, they switch. No data migration. No re-encoding. No API breakage.

### 3. Open by default, closed only by choice

Every feature should have an open API. Plugins should be a first-class extension mechanism. Federation should be a future option, not a forgotten roadmap item.

### 4. The skeleton must come first

We will not ship a thousand-feature "social platform MVP" that breaks under any real usage.

We will ship a small, working, well-architected foundation. v0.1 does very little on purpose. The shape matters more than the features.

### 5. v0.3 is federation, not just features

If OpenCord only becomes "another social platform", we failed.

The real north star: **a community running OpenCord should be able to talk to a community running Mastodon, or Discourse, or another OpenCord instance — without giving up their independence.**

That is what "open social layer" means. Not features. **Interoperability.**

---

## What We Won't Build

- **A walled garden.** No data lock-in, no API restrictions that don't have a self-hostable alternative.
- **A surveillance layer.** AI summaries are opt-in per post. AI profiles are opt-in per user.
- **A "platform" play.** We're not trying to host everyone's community. We provide the foundation; you deploy.
- **A feature treadmill.** We won't add features just because competitors have them. Each version ships a coherent, complete slice.

---

## What We Will Build

### v0.1 — Skeleton
A working, deployable, AI-summaryable, JSON-exportable community in 11 tables.

### v0.2 — Messaging
Real-time chat, bot APIs, webhooks. The community becomes a conversation.

### v0.3 — Federation
ActivityPub read/write. Migration tools. Plugin system alpha. **The community becomes a node.**

### v0.4 — Hosted
Multi-tenant. Optional billing. Plugin marketplace. People who can't deploy can still use it.

### v0.5+ — Sovereignty
DID. Federated AI. End-to-end encryption. The community becomes sovereign.

---

## Why v0.1 Ships a Skeleton (Not a "Complete MVP")

Most open-source projects fail this way:

1. Promise everything
2. Ship nothing
3. Apologize

Or:

1. Promise a "minimum viable social platform"
2. Ship a fragile mess of half-implemented features
3. Spend 2 years cleaning up

OpenCord's v0.1 instead:
1. Promise very little
2. Ship a small, working, well-architected foundation
3. Earn the right to ship more

The v0.1 list is **15 items**, not 100. The 15 items are chosen because:
- They are the smallest set that lets a community be a community
- Each one is the foundation for many v0.2+ features
- The architecture is more important than the feature count

When someone asks "where's the private message?", the answer is "v0.2". Not "soon". Not "in the next sprint". **v0.2**, with a date when we know it, in the roadmap, with the architectural decisions that prove we know how to build it.

---

## Who This Is For

- A developer community that doesn't want to live on Discord forever
- A trade association that wants its own forum with its own rules
- A factory that wants an internal community without buying a SaaS license
- A research lab that wants its discussions to be exportable and citable
- An interest group that wants to migrate off Reddit, off Facebook Groups, off QQ groups
- A solo founder who wants to build a community product without inheriting a platform's politics

---

## Who This Is NOT For

- People who want a "Discord clone" with all the bells and whistles
- Teams that need 100,000-message-per-second scale on day one
- Anyone who believes AI should be the community's moderator, not a tool the moderator uses
- Anyone looking for a hosted product to point users at (v0.4 will offer that)

---

## How To Read The Docs

- [README.md](../README.md) — what is it, how to install
- [ROADMAP.md](./ROADMAP.md) — version-by-version scope
- [ARCHITECTURE.md](./ARCHITECTURE.md) — how it's built
- [API.md](./API.md) — how to integrate

The roadmap is a direction, not a deadline. We ship when the slice is done, not when the calendar says so.

---

## Final Word

> Building a boat, not fishing in someone else's pond.

If you've ever felt "this community belongs to us, not to the platform" — OpenCord is for you.
