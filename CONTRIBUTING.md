# Contributing to Chip Quality Platform

Thank you for your interest in contributing! This document provides guidelines for contributing to this project.

## 🤝 Code of Conduct

This project adheres to a code of conduct. By participating, you agree to uphold this code.

## 🚀 Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR-USERNAME/chip-quality-platform.git`
3. Create a feature branch: `git checkout -b feature/your-feature-name`
4. Set up development environment: `make setup-dev`

## 📝 Development Workflow

### Branch Strategy
- `main` - Production-ready code
- `develop` - Integration branch for features
- `feature/*` - Feature development
- `hotfix/*` - Emergency fixes
- `release/*` - Release preparation

### Commit Convention
We use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Types:**
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation changes
- `style` - Code style changes (formatting, etc.)
- `refactor` - Code refactoring
- `test` - Adding or modifying tests
- `chore` - Maintenance tasks
- `ci` - CI/CD changes
- `perf` - Performance improvements

**Examples:**
```
feat(api-gateway): add rate limiting middleware
fix(inference-svc): handle triton connection errors gracefully
docs(api): update OpenAPI schema for reports endpoint
```

### Pull Request Process

1. **Before creating PR:**
   - Ensure tests pass: `make test`
   - Run linting: `make lint`
   - Update documentation if needed
   - Add/update tests for new functionality

2. **PR Requirements:**
   - Clear, descriptive title following conventional commits
   - Description explaining the change and reasoning
   - Link to related issues
   - Tests included and passing
   - Documentation updated
   - Breaking changes noted

3. **Review Process:**
   - At least one approving review required
   - All CI checks must pass
   - No merge conflicts
   - Up-to-date with target branch

## 🧪 Testing Guidelines

### Test Structure
```
tests/
├── unit/           # Unit tests for individual components
├── integration/    # Integration tests across services
├── e2e/           # End-to-end workflow tests
├── load/          # Performance and load tests
└── fixtures/      # Test data and fixtures
```

### Test Requirements
- **Unit Tests**: Cover all business logic, aim for >90% coverage
- **Integration Tests**: Test service interactions
- **E2E Tests**: Test complete user workflows
- **Performance Tests**: Ensure SLA compliance

### Running Tests
```bash
# All tests
make test

# Specific test types
make test-unit
make test-integration
make test-e2e
make test-load

# With coverage
make test-coverage

# Watch mode for development
make test-watch
```

## 🏗️ Architecture Guidelines

### Service Design Principles
1. **Single Responsibility**: Each service owns one business domain
2. **API-First**: Design APIs before implementation
3. **Async Communication**: Use events for loose coupling
4. **Idempotency**: All mutations must be idempotent
5. **Observability**: Include metrics, logs, and traces

### Code Standards
- **Python**: Follow PEP 8, use type hints
- **FastAPI**: Leverage dependency injection
- **Database**: Use migrations, avoid N+1 queries
- **Async**: Prefer async/await for I/O operations
- **Error Handling**: Use proper HTTP status codes

### API Design
- Follow REST principles
- Use OpenAPI 3.1 specifications
- Implement proper pagination (cursor-based)
- Include comprehensive error responses
- Version APIs appropriately

## 📦 Service Development

### Adding a New Service

1. **Create service structure:**
   ```bash
   make new-service name=my-service
   ```

2. **Required files:**
   - `app/main.py` - FastAPI application
   - `app/routers/` - API endpoints
   - `app/schemas/` - Pydantic models
   - `app/core/config.py` - Configuration
   - `tests/` - Test suite
   - `Dockerfile` - Container definition
   - `pyproject.toml` - Dependencies

3. **Integration checklist:**
   - [ ] Health endpoint (`/healthz`)
   - [ ] Metrics endpoint (`/metrics`)
   - [ ] OpenTelemetry tracing
   - [ ] Structured logging
   - [ ] Error handling middleware
   - [ ] Authentication (if needed)
   - [ ] Rate limiting (if public)

### Database Changes

1. **Create migration:**
   ```bash
   cd services/metadata-svc
   alembic revision --autogenerate -m "description"
   ```

2. **Review migration:**
   - Check generated SQL
   - Ensure backward compatibility
   - Test on sample data

3. **Apply migration:**
   ```bash
   alembic upgrade head
   ```

## 🔒 Security Guidelines

### Authentication & Authorization
- Use JWT with appropriate expiration
- Implement proper scope checking
- Validate all inputs
- Use parameterized queries

### Data Protection
- Encrypt sensitive data at rest
- Use TLS for all communications
- Implement proper access controls
- Log security events

### Vulnerability Management
- Keep dependencies updated
- Run security scans: `make security-scan`
- Report vulnerabilities via [SECURITY.md](SECURITY.md)

## 📊 Performance Guidelines

### Optimization Targets
- API latency: p95 < 200ms
- Inference latency: p95 < 2s
- Throughput: 100 inspections/minute
- Availability: 99.9%

### Best Practices
- Use connection pooling
- Implement caching strategically
- Monitor resource usage
- Profile critical paths

## 📚 Documentation

### Required Documentation
- **ADRs**: Document significant decisions in `adr/`
- **API Docs**: Keep OpenAPI specs current
- **README**: Update for new features
- **Runbooks**: Document operational procedures

### Writing Guidelines
- Use clear, concise language
- Include code examples
- Add diagrams for complex concepts
- Keep documentation DRY

## 🐛 Issue Reporting

### Bug Reports
Include:
- Clear description of the issue
- Steps to reproduce
- Expected vs actual behavior
- Environment details
- Logs/screenshots if applicable

### Feature Requests
Include:
- Use case description
- Proposed solution
- Alternative solutions considered
- Impact assessment

## 🚢 Release Process

### Version Strategy
We use [Semantic Versioning](https://semver.org/):
- MAJOR: Breaking changes
- MINOR: New features (backward compatible)
- PATCH: Bug fixes

### Release Checklist
- [ ] All tests passing
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Security scan clean
- [ ] Performance benchmarks met
- [ ] Staged deployment tested
- [ ] Release notes prepared

## 🛠️ Development Tools

### Required Tools
- Python 3.11+
- Docker & Docker Compose
- kubectl & helm
- git with commit signing

### Recommended IDE Setup
- VS Code with Python extension
- Pre-commit hooks: `pre-commit install`
- Type checking: Enable mypy
- Formatting: Use ruff

### Makefile Targets
```bash
make help              # Show all available targets
make setup-dev         # Setup development environment
make dev-gateway       # Run API gateway locally
make dev-inference     # Run inference service locally
make lint              # Run code linting
make format            # Format code
make test              # Run all tests
make docker-build      # Build all Docker images
make k8s-deploy        # Deploy to local Kubernetes
```

## 📞 Getting Help

- **Questions**: Use GitHub Discussions
- **Bugs**: Create GitHub Issues
- **Security**: Follow [SECURITY.md](SECURITY.md)
- **Architecture**: Review [ADRs](adr/)

## ✅ Contributor Recognition

Contributors are recognized in:
- CONTRIBUTORS.md file
- Release notes
- Project documentation

Thank you for contributing to the Chip Quality Platform! 🙏