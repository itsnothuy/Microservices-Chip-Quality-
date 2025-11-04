# Report Service

Quality reporting and analytics service for the Chip Quality Platform.

## Overview

The Report Service provides comprehensive quality reporting, statistical analytics, and FDA-compliant documentation generation for semiconductor manufacturing operations.

## Features

### Core Reporting
- **Quality Reports**: Automated quality control and compliance reports
- **Production Reports**: Manufacturing efficiency and throughput analytics
- **Custom Reports**: Configurable report templates and formats
- **Scheduled Reports**: Automated report generation and distribution
- **Multi-format Export**: PDF, Excel, CSV, JSON, HTML support

### Analytics
- **Statistical Process Control**: SPC charts, control limits, process capability
- **Defect Analysis**: Pareto charts, root cause analysis, trend detection
- **Performance Analytics**: OEE calculation, throughput analysis
- **Quality Metrics**: First pass yield, defect rates, quality trends

### Compliance
- **FDA 21 CFR Part 11**: Compliant report generation
- **Audit Trail**: Complete report generation and access audit logs
- **Data Integrity**: Immutable report data with validation
- **Electronic Records**: Secure storage and retrieval

## API Endpoints

### Reports
- `POST /api/v1/reports` - Generate new report
- `GET /api/v1/reports` - List reports
- `GET /api/v1/reports/{id}` - Get report details
- `GET /api/v1/reports/{id}/download` - Download report file
- `POST /api/v1/reports/{id}/regenerate` - Regenerate report
- `DELETE /api/v1/reports/{id}` - Delete report

### Analytics
- `POST /api/v1/analytics/quality` - Quality analytics
- `POST /api/v1/analytics/spc` - Statistical Process Control
- `POST /api/v1/analytics/capability` - Process capability analysis
- `POST /api/v1/analytics/pareto` - Pareto analysis
- `GET /api/v1/analytics/production` - Production analytics

### Templates
- `GET /api/v1/templates` - List report templates
- `GET /api/v1/templates/{id}` - Get template details

## Configuration

Environment variables:

```bash
# Service Configuration
SERVICE_NAME=report-service
SERVICE_VERSION=1.0.0
ENVIRONMENT=development
API_HOST=0.0.0.0
API_PORT=8083

# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/chip_quality

# Redis
REDIS_URL=redis://localhost:6379/0

# MinIO
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_REPORTS_BUCKET=reports

# Report Settings
REPORT_GENERATION_TIMEOUT=300
MAX_CONCURRENT_REPORTS=10
REPORT_RETENTION_DAYS=2555
```

## Development

### Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the service
python -m app.main
```

### Running with Docker

```bash
# Build image
docker build -t report-service .

# Run container
docker run -p 8083:8083 \
  -e DATABASE_URL=postgresql+asyncpg://postgres:postgres@host.docker.internal:5432/chip_quality \
  report-service
```

## Testing

```bash
# Run unit tests
pytest tests/unit/ -v

# Run integration tests
pytest tests/integration/ -v

# Run with coverage
pytest --cov=app --cov-report=html
```

## Performance

- **Report Generation**: < 30 seconds for standard reports
- **Dashboard Response**: < 3 seconds
- **Large Datasets**: Supports > 1M inspection records
- **Concurrent Access**: Handles 50+ simultaneous report requests

## Statistical Accuracy

All statistical calculations are accurate to 6 decimal places and validated against industry standards:

- SPC control limits (X-bar R, X-mR, p-chart, c-chart, u-chart)
- Process capability indices (Cp, Cpk, Pp, Ppk)
- Quality metrics (FPY, defect rates, yield)
- OEE calculations (availability, performance, quality)

## Compliance

The service meets FDA 21 CFR Part 11 requirements for electronic records:

- Electronic signatures
- Audit trails
- Data integrity validation
- 7-year data retention
- Immutable audit logs

## Architecture

The service follows a layered architecture:

1. **API Layer** (`routers/`): FastAPI endpoints
2. **Service Layer** (`services/`): Business logic
3. **Data Layer** (`models/`): Database models
4. **Schema Layer** (`schemas/`): Request/response validation
5. **Utility Layer** (`utils/`, `generators/`): Helper functions

## Dependencies

Key dependencies:

- **FastAPI**: Web framework
- **SQLAlchemy**: Database ORM
- **ReportLab**: PDF generation
- **OpenPyXL**: Excel generation
- **Pandas/NumPy/SciPy**: Data analysis and statistics
- **Matplotlib/Plotly**: Visualization

## License

MIT License - See LICENSE file for details
