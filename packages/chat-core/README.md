# @screenpipe/chat-core

The parts of a chat that are true of any chat.

A conversation with a streaming, tool-using agent has a shape that does not
depend on where the agent runs, who is paying for it, or what product it is
embedded in: messages and content blocks, a turn that moves through phases,
tool calls that start and finish, plans, citations, and a transcript that two
clients can hold at once and have to reconcile.

This package is that shape and nothing else.

## Constraints

Zero dependencies. No DOM at import time. Nothing from Tauri, React, Next or
screenpipe. `tsconfig.json` sets `lib: ["ES2022"]` with no `DOM`, so reaching
for a browser global is a compile error rather than a runtime fault in whichever
host got unlucky, and `src/globals.d.ts` declares the entire platform surface
the package is allowed to assume.

These are checked, not just documented. See `src/__tests__/portability.test.ts`,
which reads the source tree for banned imports, unguarded `process`, and proves
that importing the barrel does no work at module scope. The suite runs in plain
node with no DOM shim, so the day the package needs one, it fails.

## What lives here

| Area | Modules |
|---|---|
| Domain model | `types`, `source-citations` |
| Turn lifecycle | `turn-phase` |
| Reading a transcript | `message-rendering`, `markdown-export`, `search-tool-results` |
| Naming a conversation | `conversation-title`, `fallback-title`, `injected-prompts` |
| Agent protocol | `events`, `acp-plan`, `acp-spawn-signature`, `agent-action-card`, `connect-card`, `conversation-history`, `image-content`, `auth-errors`, `model-allowance-cost` |
| Two clients, one transcript | `transcript-merge`, `dedup` |
| The backend seam | `transport` |

## What deliberately does not

screenpipe's tool vocabulary (`tool-presentation`), its system prompt, and its
gateway error dialect (`provider-errors`, `quota-errors`, with branded copy and
a `screenpi.pe` host allowlist) stay in the app. A package that absorbed them
would be screenpipe's chat wearing a package's clothes.

Rendering stays in the app too. The desktop chat and a web chat should not look
the same, and the reusable part was never the interface.

## The transport seam

`ChatTransport` is the boundary between a chat UI and whatever is actually
running the agent. One decision shapes it:

```ts
send(input: TurnInput): Promise<TurnHandle>;
attach(sessionId: SessionId, options?: AttachOptions): AsyncIterable<AgentEventEnvelope>;
```

**Starting a turn and watching a turn are separate operations.** `send` returns
a handle, not a stream.

Coupling them is what makes the usual `useChat` shape unable to resume. If the
stream is the response body of the request that started it, then closing the tab
ends the turn, a second window cannot watch, and a reload loses everything in
flight. Splitting them costs nothing on a simple backend and is the only thing
that works when the agent runs somewhere the client cannot hold a socket open
to: a local sidecar the UI reconnects to, a cloud runner whose job outlives the
browser, a second desktop window hydrating a turn it did not send.

`capabilities()` is a method rather than a constant because the answer varies
per deployment and not only per adapter: an enterprise policy can disable
attachments on a transport whose code supports them. `toolExecution` is
load-bearing for the UI, not bookkeeping. When it reads `"remote"` the
transcript must stop offering to open local files, because a citation points at
a machine the user is not sitting at.

This package ships the contract. Adapters live with the host that implements
them.

## Adding to this package

Ask whether the thing would still make sense in a chat that had never heard of
screenpipe. If the answer needs a "well, for us…", it belongs in the app.

Adding to `src/globals.d.ts` is a real decision, not a formality: anything
declared there must exist in a browser, a desktop webview, a server render and
node.

## Development

```bash
bun install
bun run typecheck   # src (no DOM, no node) and tests (node) separately
bunx vitest run     # 176 tests, plain node
```
