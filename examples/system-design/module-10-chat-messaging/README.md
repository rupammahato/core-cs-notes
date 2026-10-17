# S5: Chat and real-time messaging

Run `python verify.py` here with Python 3.12+. Recorded runtime: Python 3.12.10 / SQLite 3.49.1. `chat.py` implements durable room messages and bounded process-local hints using shared standard-library helpers from `../worked-systems-s4-s6/`.

59 named checks cover scoped send replay, sequence/message rollback, snapshot catchup, monotonic reported reads, hint loss/overflow, disconnect/restart, membership revocation, four independent competing calls and actual loopback HTTP. HTTP polling is executed; a WebSocket/SSE protocol and distributed gateway are discussed rather than implemented.

Current members can access retained room history; removed members cannot use new protected requests. A reported read cursor is not proof of human reading. Limits are 256 retained messages/room, 16 local sessions and two queued hints/session; no production retention/pruning service is implemented.

No external messages, Redis, production authentication/TLS, E2EE, multi-gateway sequencer, power-loss or throughput claim is included. `lesson.md` is the authored text; use the [batch instructions](../worked-systems-s4-s6/README.md) to regenerate/integrate/verify all three chapters. Owned resources close and temporary files are removed; port 3000 and Docker remain stopped.
