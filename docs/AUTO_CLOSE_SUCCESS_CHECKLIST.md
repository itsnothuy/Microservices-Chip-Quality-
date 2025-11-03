# ✅ Auto-Close Success Checklist for Coding Agent

## 🎯 **Pre-Implementation Checklist**

### **Environment Setup** ✅ **COMPLETED**
- [x] Validation dependencies fixed
- [x] Unicode character issue resolved  
- [x] PR templates created
- [x] Documentation completed

### **Before Starting Each Issue:**
- [ ] Read the complete issue markdown file
- [ ] Understand all acceptance criteria  
- [ ] Review implementation structure
- [ ] Check dependencies and references
- [ ] Note the issue number (e.g., #005, #006, #007, #008)

---

## 🤖 **Implementation Requirements**

### ⚠️ **CRITICAL: Auto-Close Triggers**
- [ ] **Issue Reference**: Include `Closes #XXX` in PR title or description
- [ ] **Quality Score**: Achieve ≥80% in validation
- [ ] **All Files**: Implement complete file structure from issue

### **Code Quality Standards:**
- [ ] Type hints on all functions
- [ ] Comprehensive error handling  
- [ ] Structured logging with correlation IDs
- [ ] Pydantic models for validation
- [ ] Dependency injection pattern
- [ ] Absolute import paths

### **Testing Requirements:**
- [ ] Unit tests with ≥95% coverage
- [ ] Integration tests for external services
- [ ] Performance tests where applicable
- [ ] Mock external dependencies
- [ ] Test error conditions

---

## 📋 **Issue-Specific Success Criteria**

### **Issue #005: Event Streaming with Kafka**
- [ ] Kafka producer/consumer implementation
- [ ] Avro schema definitions (.avsc files)
- [ ] Event publishing for all platform activities
- [ ] Stream processing for analytics
- [ ] Dead letter queue handling
- [ ] Real-time dashboard updates

**Key Validation Points:**
```python
# Must exist:
services/shared/events/schemas/inspection.avsc
services/shared/events/producers/base_producer.py
services/shared/events/consumers/analytics_consumer.py
services/event-processor/app/main.py
```

### **Issue #006: Observability & Monitoring**  
- [ ] OpenTelemetry distributed tracing
- [ ] Prometheus metrics collection
- [ ] Structured logging implementation
- [ ] Health check endpoints
- [ ] Grafana dashboard configurations
- [ ] Alert rule definitions

**Key Validation Points:**
```python
# Must exist:
services/shared/observability/tracing/tracer.py
services/shared/observability/metrics/business_metrics.py
monitoring/grafana/dashboards/quality.json
monitoring/prometheus/alerts/quality.yml
```

### **Issue #007: Artifact Management**
- [ ] MinIO object storage integration
- [ ] File upload/download endpoints
- [ ] Image processing pipelines
- [ ] Metadata extraction
- [ ] Search and discovery
- [ ] Version control system

**Key Validation Points:**
```python
# Must exist:
services/artifact-svc/app/services/artifact_service.py
services/artifact-svc/app/services/storage_service.py
services/artifact-svc/app/routers/artifacts.py
services/artifact-svc/app/routers/upload.py
```

### **Issue #008: Quality Reporting & Analytics**
- [ ] PDF/Excel report generation
- [ ] Statistical process control (SPC)
- [ ] Real-time dashboard APIs
- [ ] FDA 21 CFR Part 11 compliance
- [ ] Scheduled report automation
- [ ] Analytics engine implementation

**Key Validation Points:**
```python
# Must exist:
services/report-svc/app/services/report_service.py
services/report-svc/app/services/analytics_service.py
services/report-svc/app/generators/pdf_generator.py
services/report-svc/app/routers/reports.py
```

---

## 🚀 **PR Creation Checklist**

### **PR Title Format:**
```markdown
feat: Implement [feature name] - Closes #XXX

Examples:
✅ "feat: Implement Event Streaming with Kafka - Closes #005"
✅ "feat: Implement Observability & Monitoring - Closes #006"  
✅ "feat: Implement Artifact Management Service - Closes #007"
✅ "feat: Implement Quality Reporting & Analytics - Closes #008"
```

### **PR Description Must Include:**
- [ ] `Closes #XXX` reference
- [ ] Implementation summary
- [ ] Completed acceptance criteria
- [ ] Testing coverage report
- [ ] Any design decisions made

### **Use PR Template:**
- [ ] Use `.github/PULL_REQUEST_TEMPLATE/issue-implementation.md`
- [ ] Fill in all required sections
- [ ] Update issue reference line
- [ ] Complete implementation checklist

---

## 🔍 **Validation Success Criteria**

### **Before Creating PR - Run Local Validation:**
```bash
source venv/bin/activate
python tools/quality/validate-implementation.py \
  --issue issues/XXX-[issue-name].md \
  --output validation-XXX.json
```

### **Expected Validation Results:**
```json
{
  "validation_summary": {
    "is_complete": true,
    "total_errors": 0,
    "total_warnings": 0,
    "test_coverage_percentage": 95.0
  },
  "quality_score": 85.0,  // Must be ≥80%
  "recommendation": "✅ Implementation is complete"
}
```

### **Common Validation Failures to Avoid:**
- [ ] ❌ Missing required files from implementation structure
- [ ] ❌ Import resolution errors (use absolute imports)
- [ ] ❌ Syntax errors or Unicode characters
- [ ] ❌ Missing type hints
- [ ] ❌ No FastAPI routers found
- [ ] ❌ Test execution failures

---

## 📊 **Auto-Close Workflow Verification**

### **After PR Creation:**
- [ ] GitHub Actions workflow runs
- [ ] "Enhanced Issue Auto-Close with Validation" shows ✅
- [ ] Quality validation passes
- [ ] Issue reference detected in PR

### **After PR Merge:**
- [ ] Auto-close workflow triggers
- [ ] Quality score ≥80% achieved
- [ ] Issue automatically closes
- [ ] Success notification received

---

## ⚠️ **Troubleshooting Common Issues**

### **If Auto-Close Doesn't Work:**

1. **Check Issue Reference:**
   ```bash
   # Verify PR contains one of these:
   "Closes #005" ✅
   "Fixes #005"  ✅
   "Resolves #005" ✅
   
   # Not these:
   "Close #005" ❌
   "Issue #005" ❌
   "#005" ❌
   ```

2. **Check Quality Score:**
   ```bash
   # Must be ≥80%
   "quality_score": 85.0 ✅
   "quality_score": 75.0 ❌
   ```

3. **Check Validation Errors:**
   ```bash
   # Must have no errors
   "total_errors": 0 ✅
   "total_errors": 3 ❌
   ```

### **Common Fixes:**
- **Missing Files**: Create all files from issue structure
- **Import Errors**: Use absolute imports (`from services.shared...`)
- **Test Failures**: Fix syntax errors and missing dependencies
- **Type Hints**: Add type hints to all functions
- **Error Handling**: Add try/catch blocks

---

## 🎯 **Success Metrics**

### **Target Outcomes:**
- **Quality Score**: ≥80% (Target: 85-95%)
- **Test Coverage**: ≥95% 
- **Validation Errors**: 0
- **Auto-Close Rate**: 100%

### **Quality Indicators:**
- ✅ All acceptance criteria implemented
- ✅ Complete file structure created
- ✅ Comprehensive error handling
- ✅ Production-ready code quality
- ✅ Full test coverage
- ✅ Documentation complete

---

## 🎉 **Final Success Verification**

### **Complete Success Checklist:**
- [ ] Issue fully implemented per specification
- [ ] PR created with proper issue reference
- [ ] Quality validation passes (≥80%)
- [ ] GitHub Actions workflow succeeds
- [ ] PR merged to main branch
- [ ] Issue automatically closes
- [ ] Implementation is production-ready

### **Success Confirmation:**
When all requirements are met:
1. **PR Creation** → Contains `Closes #XXX`
2. **Validation** → Achieves ≥80% quality score  
3. **PR Merge** → Triggers auto-close workflow
4. **Issue Closure** → Issue automatically closes
5. **Success** → Implementation complete! 🎉

---

**Follow this checklist exactly for guaranteed auto-close success!**