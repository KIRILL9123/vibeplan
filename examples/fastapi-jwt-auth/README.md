# Example: Add JWT Auth to FastAPI

This example shows a vibeplan workflow for adding JWT authentication to a FastAPI project.

## Setup

```bash
cd examples/fastapi-jwt-auth
git init && git add . && git commit -m 'initial'
vibeplan init "add JWT authentication to FastAPI project"
```

## Expected Plan Output

```
Step 1: research   — Explore codebase, choose approach        [4,285 tokens]
Step 2: setup      — Install PyJWT dependency                 [2,857 tokens]
Step 3: implement  — JWT middleware + /login + /me endpoints  [7,142 tokens]
Step 4: test       — Unit tests + manual verification         [2,857 tokens]
Step 5: polish     — Docs, cleanup, error handling            [2,857 tokens]
```

## Running

```bash
vibeplan run
# After each step: paste the generated prompt into your AI agent
# Then press Enter and choose: continue / rollback / edit / quit
```
