# Demo Kit

| File | Purpose |
|------|---------|
| `demo.sh` | Full API walkthrough (health → keys → seal → unseal → audit → metrics) |
| `2-minute-demo.md` | CTO presentation script |
| `curl-examples.md` | Copy-paste curl commands |
| `swagger-walkthrough.md` | OpenAPI /docs tour |

## Quick start

```bash
chmod +x demo/quickstart.sh demo/demo.sh
./demo/quickstart.sh
```

Or step-by-step:

```bash
cp .env.example .env   # replace REPLACE_WITH_* placeholders
docker compose up --build -d
export API_KEY_OPERATOR="your-operator-key"
./demo/demo.sh
```

Override base URL: `BASE_URL=https://pqc.example.com ./demo/demo.sh`
