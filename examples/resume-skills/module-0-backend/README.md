# Module 0: How a Backend Works

Dependency-free Node.js learning example for the Resume Skills handbook.

From the repository root:

```powershell
node examples/resume-skills/module-0-backend/verify.mjs
node examples/resume-skills/module-0-backend/server.mjs
```

The verifier binds an available IPv4 loopback port, checks 13 HTTP cases, and closes the server. The manual server binds 127.0.0.1:3100; stop it with Ctrl+C. If that port is occupied, change the manual listen port in server.mjs.

Routes (GET only):

- /health
- /api/products/7
- /api/quote?productId=7&quantity=2

The quote uses the stored price, ignores a caller-supplied unitPricePaise, and does not reserve stock.

Verified on Node.js v22.14.0. verification-output.txt is the captured run output. The assertions cover statuses, JSON bodies/content type, Allow on 405, the quote trace and unchanged stock after a quote.

This is a public loopback demonstration with seeded process memory. It has no database, authentication, payment, order mutation, durable jobs or production hardening. No external services or packages are needed.
