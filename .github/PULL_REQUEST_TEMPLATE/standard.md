# Pull Request Template

## 📋 Summary
Brief description of the changes made in this PR.

## 🎯 Issue Reference
**REQUIRED for auto-closing:** Use one of these formats:
- `Closes #XXX` - Use this to automatically close the issue when PR is merged
- `Fixes #XXX` - Alternative for bug fixes
- `Resolves #XXX` - Alternative for feature completion

**Example:** `Closes #004` (This will auto-close issue #004 when merged)

**Multiple issues:** `Closes #004, Fixes #005, Resolves #006`

## ✅ Implementation Checklist
- [ ] All acceptance criteria from the issue are implemented
- [ ] Code follows project conventions and patterns
- [ ] Comprehensive error handling is included
- [ ] OpenTelemetry tracing spans are added
- [ ] Structured logging with correlation IDs
- [ ] Input validation using Pydantic models
- [ ] OAuth2 scope verification (if applicable)
- [ ] Idempotency support for mutations (if applicable)
- [ ] Comprehensive type hints

## 🧪 Testing
- [ ] Unit tests written and passing (≥95% coverage)
- [ ] Integration tests added (if applicable)
- [ ] API contracts match OpenAPI specification
- [ ] Performance requirements met
- [ ] Security requirements validated

## 📚 Documentation
- [ ] Code comments added for complex logic
- [ ] API documentation updated (if applicable)
- [ ] Architecture documentation updated (if needed)
- [ ] Database migrations included (if applicable)

## 🚀 Quality Validation
Before merging, ensure:
- [ ] All validation errors are resolved
- [ ] Quality score ≥80% (will be automatically checked)
- [ ] No blocking security issues
- [ ] Performance regression tests pass

## 💡 Additional Notes
Any additional context, implementation decisions, or notes for reviewers.

---

**⚠️ Important:** This PR will only auto-close issues if:
1. Issue references are properly formatted above
2. Quality validation passes (≥80% score)
3. All tests pass

For questions about the auto-close workflow, see the development documentation.