# HTTPTests

> Automated HTTP integration testing for GitHub Actions with Docker isolation

Test your APIs, proxies, and microservices in CI/CD with zero configuration. HTTPTests spins up Docker environments and validates your HTTP services.

[![GitHub Action](https://img.shields.io/badge/GitHub-Action-blue?logo=github)](https://github.com/marketplace/actions/httptests-runner)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- **Zero Configuration** - Drop a `.httptests` folder in your repo and go
- **Docker Isolated** - Each test suite runs in its own isolated Docker environment
- **Multi-Service** - Test complex setups with proxies, APIs, and mock services
- **CI Ready** - Built specifically for GitHub Actions workflows
- **Detailed Output** - Clear test results with assertion counts and validation details
- **Automatic Upstream Tracking** - Auto-injects `X-Upstream-Target` headers for precise proxy validation

## Quick Start

### 1. Add a test suite to your repository

Create a `.httptests` directory with two files:

**`.httptests/config.yml`**
```yaml
mock:
  network_aliases:
    - backend

nginx:
  environment:
    ENV_VAR: value
```

**`.httptests/test.json`**
```json
{
  "hosts": {
    "api.example.com": [
      {
        "paths": ["/health"],
        "method": "GET",
        "expectedStatus": 200,
        "expectedResponseHeaders": [
          ["Content-Type", "application/json"]
        ]
      }
    ]
  }
}
```

### 2. Add a Dockerfile for your service

Place a `Dockerfile` in the same directory as `.httptests`:

```dockerfile
FROM nginx:alpine
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### 3. Add GitHub Action workflow

**`.github/workflows/test.yml`**
```yaml
name: HTTPTests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: serviceguards-com/httptests-action@latest1
        with:
          httptests-directory: .
```

That's it! Your HTTP integration tests will now run on every push and pull request.

## Use Cases

### API Testing
Test REST APIs, GraphQL endpoints, and webhooks with comprehensive assertions on status codes, headers, and response bodies.

### Nginx/Proxy Validation
Validate reverse proxy configurations, header transformations, routing rules, and upstream forwarding behavior.

### Microservices Testing
Test service-to-service communication, load balancing, service discovery, and API gateway configurations.

### Load Balancer Testing
Verify load balancer behavior, health checks, failover scenarios, and request distribution.

## Why HTTPTests?

| Feature | HTTPTests | curl scripts | Postman/Newman | Custom Framework |
|---------|-----------|--------------|----------------|------------------|
| **Setup Time** | < 5 minutes | Manual | 15-30 minutes | Hours |
| **Docker Isolation** | ✅ Built-in | ❌ Manual | ❌ Manual | ❌ Manual |
| **Multi-Service** | ✅ Yes | ⚠️ Complex | ⚠️ Limited | ⚠️ Custom |
| **CI Integration** | ✅ Native | ⚠️ Manual | ✅ Yes | ⚠️ Custom |
| **Learning Curve** | Low | Low | Medium | High |

## Real-World Example

```
=== Processing suite: ./api-service/.httptests ===
📦 Starting Docker services...
🧪 Running tests for httptests-api-service

🔍 Waiting for service to be ready (max 60s)...
  Attempt 1: Service not ready yet (2.0s elapsed)...
  Attempt 2: Service not ready yet (4.1s elapsed)...
✓ Service is ready! (took 5.2s)

test_endpoints (__main__.IntegrationTests.test_endpoints) ... ok
  → Testing: GET api.example.com/health
    ✓ Status code: 200 (expected 200)
    ✓ Response header: content-type = application/json
  → Testing: GET api.example.com/users
    ✓ Status code: 200 (expected 200)
    ✓ Request header forwarded: x-forwarded-for
    ✓ Request header: x-api-version = v1
============================================================
Total assertions passed: 5
============================================================
🧹 Cleaning up Docker services...
```

## Documentation

- **[Official Documentation](https://www.httptests.com)** - Complete setup, configuration, and reference
- **[Examples Repository](https://github.com/serviceguards-com/httptests-example)** - Real-world examples for different use cases

## Examples

Explore real-world examples in the [httptests-example repository](https://github.com/serviceguards-com/httptests-example):

- **[API Testing](https://github.com/serviceguards-com/httptests-example/tree/main/api-testing)** - REST API with CRUD operations
- **[Nginx Proxy](https://github.com/serviceguards-com/httptests-example/tree/main/nginx-proxy)** - Reverse proxy with header transformation
- **[Microservices](https://github.com/serviceguards-com/httptests-example/tree/main/microservices)** - Multi-service communication testing
- **[API Gateway](https://github.com/serviceguards-com/httptests-example/tree/main/api-gateway)** - Auth, rate limiting, and routing

## Advanced Features

### Collection Headers
Define headers once, use them in all tests:

```json
{
  "collectionHeaders": [
    ["X-Request-Id"],
    ["Authorization"]
  ],
  "hosts": {
    "api.example.com": [...]
  }
}
```

### Request/Response Validation
Test status codes, response headers, and upstream request headers:

```json
{
  "paths": ["/api/users"],
  "expectedStatus": 200,
  "expectedResponseHeaders": [
    ["Content-Type", "application/json"]
  ],
  "expectedRequestHeadersToUpstream": [
    ["X-Forwarded-For"],
    ["X-Real-IP"]
  ]
}
```

### Automatic Upstream Target Tracking

HTTPTests automatically adds `X-Upstream-Target` headers to your nginx configurations during test runs. This enables precise validation of proxy destinations.

**What it does:**
- Scans all `.conf` files in your test directory
- Detects `proxy_pass` directives
- Adds `proxy_set_header X-Upstream-Target "<upstream-url>";` after each one
- Preserves indentation and formatting
- Skips if header already exists (idempotent)

**Example transformation:**

Before:
```nginx
location /api/ {
    proxy_pass http://backend:5001/;
    proxy_set_header Host $host;
}
```

After (automatic):
```nginx
location /api/ {
    proxy_pass http://backend:5001/;
    proxy_set_header X-Upstream-Target "backend:5001";
    proxy_set_header Host $host;
}
```

**Test validation:**
```json
{
  "paths": ["/api/users"],
  "expectedRequestHeadersToUpstream": [
    ["X-Upstream-Target", "backend:5001"]
  ]
}
```

This ensures your proxy connects to the **exact correct upstream**, even when multiple similar services exist (e.g., `backend:5001`, `backend:9999`, `different-host:5001`).

## Configuration

### Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `httptests-directory` | Path to directory containing `.httptests` folder | Yes | - |
| `python-version` | Python version for test runner | No | `3.x` |

### Example with options

```yaml
- uses: serviceguards-com/httptests-action@latest1
  with:
    httptests-directory: ./services/api-gateway
    python-version: '3.11'
```

### Testing Multiple Suites

To test multiple `.httptests` directories, use a matrix strategy:

```yaml
name: HTTPTests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        test-suite:
          - ./service-a
          - ./service-b
          - ./service-c
    steps:
      - uses: actions/checkout@v4
      - uses: serviceguards-com/httptests-action@latest1
        with:
          httptests-directory: ${{ matrix.test-suite }}
```

Each test suite will run in parallel as a separate job with its own isolated Docker environment.

## Requirements

- **GitHub Actions runner**: `ubuntu-latest` recommended
- **Docker**: Available on GitHub's Ubuntu runners by default
- **Services**: Must have a `Dockerfile` in the parent directory of `.httptests`

## Contributing

Contributions are welcome! Please check out our [Contributing Guide](CONTRIBUTING.md).

## License

MIT License - see [LICENSE](LICENSE) for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/serviceguards-com/httptests-action/issues)
- **Documentation**: [https://www.httptests.com](https://www.httptests.com)
- **Examples**: [httptests-example repository](https://github.com/serviceguards-com/httptests-example)

---

Made with ❤️ for developers who value automated testing
