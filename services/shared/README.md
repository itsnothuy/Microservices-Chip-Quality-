# Chip Quality Platform - Shared Database Module

Production-grade SQLAlchemy models, Pydantic schemas, and database utilities for the semiconductor manufacturing quality platform.

## 📁 Structure

```
services/shared/
├── database/           # Database engine and session management
│   ├── base.py        # Base model class with UUID and timestamps
│   ├── engine.py      # Async SQLAlchemy engine configuration
│   ├── session.py     # Session management and dependency injection
│   └── enums.py       # PostgreSQL enum types
├── models/            # SQLAlchemy ORM models
│   ├── manufacturing.py  # Part and Lot models
│   ├── inspection.py     # Inspection and Defect models
│   ├── inference.py      # ML Inference Job model
│   ├── artifacts.py      # Artifact storage model
│   ├── reporting.py      # Report generation model
│   └── audit.py          # Audit log for compliance
├── schemas/           # Pydantic schemas for API validation
│   ├── common.py         # Base schemas and pagination
│   ├── manufacturing.py  # Part and Lot schemas
│   └── inspection.py     # Inspection and Defect schemas
├── migrations/        # Alembic database migrations
│   ├── env.py            # Migration environment
│   ├── versions/         # Migration scripts
│   └── script.py.mako    # Migration template
└── tests/             # Comprehensive test suite
    ├── unit/             # Unit tests for models and schemas
    └── integration/      # Database integration tests
```

## 🚀 Features

### Database Layer
- **Async SQLAlchemy 2.0+** with asyncpg driver
- **Connection Pooling** with configurable parameters
- **Health Monitoring** and automatic reconnection
- **TimescaleDB Support** for time-series data (future enhancement)
- **Transaction Management** with savepoints

### SQLAlchemy Models
- **UUID Primary Keys** for all entities
- **Timestamp Mixins** for audit trails (created_at, updated_at)
- **Complex Relationships** with proper cascade rules
- **Check Constraints** for business rule validation
- **GIN Indexes** for JSONB fields
- **Automatic Updated Timestamps** via database triggers

### Pydantic Schemas
- **Comprehensive Validation** with custom validators
- **API Serialization** with proper type hints
- **Request/Response Models** for all operations
- **OpenAPI Documentation** with examples
- **Flexible JSONB Handling** for metadata fields

### Alembic Migrations
- **Async Migration Support** 
- **Complete Initial Schema** with all enums and tables
- **Proper Index Creation** for query performance
- **Database Triggers** for automated fields
- **Rollback Support** for safe deployments

## 🔧 Configuration

### Environment Variables

```bash
# Database Connection
DATABASE_URL=postgresql+asyncpg://user:password@host:port/database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=chip_quality
DB_USER=chip_quality_user
DB_PASSWORD=your_password

# Connection Pool
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_RECYCLE=3600
DB_POOL_PRE_PING=true

# Environment
ENVIRONMENT=development  # development, staging, production, test
```

## 📖 Usage

### Basic Database Session

```python
from database.session import get_db_session
from models.manufacturing import Part
from sqlalchemy import select

# In FastAPI endpoint
@app.get("/parts/")
async def list_parts(db: AsyncSession = Depends(get_db_session)):
    result = await db.execute(select(Part))
    parts = result.scalars().all()
    return parts
```

### Creating Records

```python
from models.manufacturing import Part, Lot
from database.enums import PartTypeEnum, LotStatusEnum
from datetime import date

async def create_manufacturing_data(db: AsyncSession):
    # Create part
    part = Part(
        part_number="PCB-2025-001",
        part_name="High-Density PCB",
        part_type=PartTypeEnum.PCB,
        specifications={"layers": 8, "thickness": "1.6mm"},
        tolerance_requirements={"dimensional": "±0.1mm"},
    )
    db.add(part)
    await db.commit()
    await db.refresh(part)
    
    # Create lot
    lot = Lot(
        lot_number="LOT-2025-001",
        part_id=part.id,
        production_date=date.today(),
        batch_size=1000,
        production_line="LINE-A",
        status=LotStatusEnum.ACTIVE,
    )
    db.add(lot)
    await db.commit()
    
    return part, lot
```

### Querying with Relationships

```python
from models.inspection import Inspection, Defect
from sqlalchemy.orm import selectinload

async def get_inspection_with_defects(
    db: AsyncSession, 
    inspection_id: UUID
):
    result = await db.execute(
        select(Inspection)
        .options(selectinload(Inspection.defects))
        .where(Inspection.id == inspection_id)
    )
    inspection = result.scalar_one_or_none()
    return inspection
```

### Using Pydantic Schemas

```python
from schemas.inspection import InspectionCreate, InspectionResponse
from models.inspection import Inspection

async def create_inspection_endpoint(
    data: InspectionCreate,
    db: AsyncSession = Depends(get_db_session)
) -> InspectionResponse:
    # Create model from schema
    inspection = Inspection(**data.model_dump())
    db.add(inspection)
    await db.commit()
    await db.refresh(inspection)
    
    # Return response schema
    return InspectionResponse.model_validate(inspection)
```

## 🗄️ Running Migrations

### Initialize Database

```bash
# Navigate to shared directory
cd services/shared

# Run migrations
alembic upgrade head

# Check current version
alembic current

# Show migration history
alembic history
```

### Creating New Migrations

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "Description of changes"

# Create empty migration
alembic revision -m "Description of changes"

# Apply migration
alembic upgrade head

# Rollback one version
alembic downgrade -1
```

## 🧪 Testing

### Run Unit Tests

```bash
# Run all unit tests
pytest tests/unit/ -v

# Run specific test file
pytest tests/unit/test_models.py -v

# Run with coverage
pytest tests/unit/ --cov=. --cov-report=html
```

### Run Integration Tests

```bash
# Requires PostgreSQL running
docker-compose up -d postgresql

# Run integration tests
pytest tests/integration/ -v -m integration

# Run all tests
pytest tests/ -v
```

### Test Markers

- `@pytest.mark.unit` - Unit tests (fast, isolated)
- `@pytest.mark.integration` - Integration tests (database required)
- `@pytest.mark.database` - Database-specific tests
- `@pytest.mark.asyncio` - Async tests

## 📊 Database Schema

### Core Entities

| Entity | Description | Key Relationships |
|--------|-------------|-------------------|
| `parts` | Part definitions | → lots |
| `lots` | Manufacturing batches | ← parts, → inspections |
| `inspections` | Quality inspections | ← lots, → defects, → inference_jobs |
| `defects` | Detected defects | ← inspections |
| `inference_jobs` | ML inference tasks | ← inspections, → artifacts |
| `artifacts` | File storage metadata | ← inspections, ← inference_jobs |
| `reports` | Generated reports | - |
| `audit_log` | Compliance audit trail | - |

### Enumerations

All enum types are defined in `database/enums.py`:
- `PartTypeEnum` - pcb, semiconductor, component, assembly, wafer
- `LotStatusEnum` - active, completed, quarantined, released, rejected
- `InspectionTypeEnum` - visual, electrical, thermal, dimensional, functional, optical
- `InspectionStatusEnum` - pending, in_progress, completed, failed, cancelled
- `DefectTypeEnum` - scratch, void, contamination, misalignment, short, open, crack, burn, etc.
- `DefectSeverityEnum` - low, medium, high, critical
- And more...

## 🔒 Security & Compliance

### FDA 21 CFR Part 11 Compliance

- **Audit Trail**: All record modifications logged in `audit_log` table
- **Data Integrity**: SHA-256 checksums for artifacts
- **Timestamps**: Immutable creation and update timestamps
- **User Tracking**: User ID and session tracking for all actions

### Security Features

- **Parameterized Queries**: Protection against SQL injection
- **Connection Encryption**: TLS/SSL support for production
- **Connection Pooling**: Prevents connection exhaustion attacks
- **Input Validation**: Comprehensive Pydantic validation

## 🎯 Performance Optimizations

### Indexes

- **B-tree indexes** on foreign keys and commonly queried fields
- **GIN indexes** on JSONB columns for fast JSON queries
- **Composite indexes** for multi-column queries
- **Partial indexes** for filtered queries

### Query Optimization

- **Connection pooling** with optimal pool size
- **Prepared statements** via SQLAlchemy
- **Eager loading** with selectinload for relationships
- **Query result caching** (application level)

### Future Enhancements

- **TimescaleDB hypertables** for metrics and events
- **Read replicas** for query distribution
- **Partitioning** for large tables (audit_log)
- **Materialized views** for complex analytics

## 📝 Best Practices

### Models

1. Always use UUID for primary keys
2. Include timestamps (created_at, updated_at)
3. Add appropriate check constraints
4. Use JSONB for flexible metadata
5. Define proper cascade rules for relationships

### Schemas

1. Separate Create/Update/Response schemas
2. Add field validators for complex validation
3. Include examples in schema configuration
4. Use Optional[] for nullable fields
5. Validate enum values

### Migrations

1. Test migrations in development first
2. Always provide downgrade path
3. Create indexes concurrently in production
4. Keep migrations small and focused
5. Document breaking changes

## 🐛 Troubleshooting

### Connection Issues

```python
# Test database connectivity
from database.engine import health_check

async def test_connection():
    is_healthy = await health_check()
    print(f"Database healthy: {is_healthy}")
```

### Migration Issues

```bash
# Check current state
alembic current

# Show pending migrations
alembic history

# Force stamp a version (use with caution)
alembic stamp head
```

### Common Errors

1. **Foreign Key Violation**: Ensure parent records exist before creating child records
2. **Unique Constraint**: Check for duplicate part_number, lot_number, etc.
3. **Connection Pool Exhausted**: Increase DB_POOL_SIZE or fix connection leaks

## 📚 Additional Resources

- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [TimescaleDB Documentation](https://docs.timescale.com/)

## 📄 License

MIT License - See LICENSE file for details

## 🤝 Contributing

1. Create feature branch from `main`
2. Implement changes with tests
3. Ensure 95%+ test coverage
4. Run linters (ruff, mypy)
5. Submit pull request with description

---

**Status**: ✅ Production Ready  
**Version**: 0.1.0  
**Last Updated**: 2025-10-29
