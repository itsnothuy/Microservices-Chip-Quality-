# 🔄 Issue Auto-Close Workflow Guide

## 🎯 Overview
This document explains how to properly reference issues in PRs to enable automatic issue closure when PRs are merged to the `main` branch.

## ✅ Auto-Close Requirements

Your PR must meet **BOTH** conditions for issues to auto-close:

### 1. **Proper Issue References** 
Use these keywords in your PR title or description:
```markdown
Closes #XXX
Fixes #XXX  
Resolves #XXX
```

### 2. **Quality Validation**
- Quality score must be ≥80%
- All validation checks must pass
- No blocking errors in implementation

## 📝 How to Reference Issues

### ✅ Correct Formats

**Single Issue:**
```markdown
Closes #004
```

**Multiple Issues:**
```markdown
Closes #004, Fixes #005, Resolves #006
```

**In PR Title:**
```
feat: Implement ML inference pipeline - Closes #004
```

**In PR Description:**
```markdown
This PR implements the complete ML inference pipeline.

Closes #004
```

### ❌ Incorrect Formats (Won't Work)

```markdown
# These WON'T trigger auto-close:
- Close #004 (missing 's')
- Closing #004 (wrong form)
- Issue #004 (no keyword)
- #004 (no keyword)
- Closes issue #004 (extra word)
```

## 🔧 Workflow Process

### Step 1: Create Feature Branch
```bash
git checkout -b feature/004-ml-inference-pipeline
```

### Step 2: Implement Issue Requirements
Follow the implementation structure from the issue markdown file.

### Step 3: Create PR with Proper References
Use the PR templates in `.github/PULL_REQUEST_TEMPLATE/`:
- `issue-implementation.md` for major issue implementations
- `standard.md` for smaller changes

### Step 4: Ensure Quality Validation Passes
The workflow automatically runs these checks:
- File structure completeness
- Python syntax validation  
- Import resolution
- Database model validation
- Test execution and coverage
- API contract compliance

### Step 5: Merge to Main
Once approved and all checks pass, merge the PR. The issue will automatically close.

## 🧪 Quality Validation Details

### Validation Checks
The workflow validates your implementation against:

1. **File Structure:** All required files from issue specification
2. **Python Syntax:** No syntax errors in Python files
3. **Import Resolution:** All imports can be resolved
4. **Database Models:** Proper model definitions and relationships
5. **Test Execution:** Tests run successfully with adequate coverage
6. **API Contracts:** Endpoints match OpenAPI specification

### Quality Score Calculation
```
Quality Score = (Passed Validations / Total Validations) × 100
Minimum Required: 80%
```

### Common Validation Failures

**❌ Missing Dependencies:**
```bash
# Fix by installing required packages
source venv/bin/activate
pip install fastapi sqlalchemy pydantic structlog pytest-mock
```

**❌ Import Errors:**
```python
# Fix import paths in your code
from services.shared.models import Part, Lot  # ✅ Correct
from models import Part, Lot  # ❌ Wrong
```

**❌ Missing Test Files:**
```bash
# Ensure test files exist and are properly structured
tests/unit/test_[feature].py
tests/integration/test_[feature]_integration.py
```

## 🛠️ Troubleshooting

### Issue Didn't Auto-Close?

**Check 1: Issue Reference Format**
```bash
# Search your PR for issue references
git log --grep="Closes #XXX" --grep="Fixes #XXX" --oneline
```

**Check 2: Quality Validation**
```bash
# Run validation locally
source venv/bin/activate
python tools/quality/validate-implementation.py \
  --issue issues/XXX-[issue-name].md \
  --output validation-report.json
```

**Check 3: GitHub Actions Log**
1. Go to your repository's Actions tab
2. Look for "Enhanced Issue Auto-Close with Validation" workflow
3. Check the logs for validation results

### Common Solutions

**🔧 Fix Dependencies:**
```bash
source venv/bin/activate
pip install -e .
pip install fastapi sqlalchemy pydantic uvicorn alembic asyncpg redis kafka-python pytest-mock structlog
```

**🔧 Fix Import Paths:**
Update imports to use absolute paths from project root:
```python
# Change this:
from database.base import BaseModel

# To this:
from services.shared.database.base import BaseModel
```

**🔧 Add Missing Files:**
Ensure all files mentioned in the issue specification exist:
```bash
# Check for missing files
find services/ -name "*.py" | grep -E "(models|schemas|services|routers)"
```

## 📋 Best Practices

### 1. **Use PR Templates**
Always use the provided PR templates for consistency.

### 2. **Reference Issues Early**
Add issue references in your first commit message or PR draft.

### 3. **Test Locally First**
Run validation locally before creating the PR:
```bash
python tools/quality/validate-implementation.py --issue issues/XXX-[name].md
```

### 4. **Follow Implementation Structure**
Stick to the file structure outlined in the issue markdown.

### 5. **Comprehensive Testing**
Ensure ≥95% test coverage for new code.

## 🎯 Example Workflow

### Perfect PR Example:
```markdown
Title: "feat: Implement ML inference pipeline - Closes #004"

Description:
This PR implements the complete ML inference pipeline with NVIDIA Triton integration.

**Closes #004**

## Implementation Summary
- ✅ Triton client integration
- ✅ Inference service with batch processing  
- ✅ Model management and versioning
- ✅ Performance monitoring
- ✅ Comprehensive test coverage (96.2%)

Quality Score: 94.5/100 ✅
All validation checks passed ✅
```

This PR would automatically close issue #004 when merged because:
1. ✅ Contains "Closes #004" reference
2. ✅ Passes quality validation (≥80%)
3. ✅ All implementation requirements met

## 🔗 Related Files
- `.github/workflows/enhanced-auto-close.yml` - Auto-close workflow
- `.github/PULL_REQUEST_TEMPLATE/` - PR templates
- `tools/quality/validate-implementation.py` - Validation script
- `issues/` - Issue specifications

## 📞 Support
If you encounter issues with the auto-close workflow:
1. Check this documentation first
2. Run local validation to identify issues
3. Review GitHub Actions logs for specific errors
4. Ensure all dependencies are properly installed