# Quick Start Guide

This guide will help you get Banking Simulator up and running in less than 5 minutes.

## Prerequisites

- Python 3.11 or higher
- pip (Python package installer)
- Git (optional, for cloning the repository)

## Installation Steps

### 1. Clone or Download the Repository

```bash
git clone https://github.com/your-username/banking-simulator.git
cd banking-simulator
```

Or download and extract the ZIP file, then navigate to the extracted directory.

### 2. Create a Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Configure Environment Variables

Copy the example environment file and configure as needed:

```bash
cp .env.example .env
```

Edit `.env` with your preferred configuration. The most important variables are:

**DATABASE_URL**: Database connection string
- Development (SQLite): `sqlite:///./data/app.db` (default)
- Production (PostgreSQL): `postgresql+psycopg://user:password@localhost:5432/banking_simulator`

**ARTIFACT_STORE**: Storage backend for cached results
- `file`: Store artifacts as files (default, recommended for local development)
- `database`: Store artifacts as BLOBs in database (for production with PostgreSQL)

**ARTIFACT_PATH**: Directory for file-based artifacts (default: `./data/artifacts`)

**LOG_LEVEL**: Logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`) (default: `INFO`)

Example `.env` for local development:
```bash
DATABASE_URL=sqlite:///./data/app.db
ARTIFACT_STORE=file
ARTIFACT_PATH=./data/artifacts
LOG_LEVEL=INFO
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

This will install all required packages including Streamlit, SQLAlchemy, pandas, and pytest.

### 5. Initialize the Database

```bash
alembic upgrade head
```

This creates the SQLite database and applies all migrations.

### 6. Run the Application

```bash
streamlit run app/main.py
```

The application will open in your default browser at `http://localhost:8501`.

## First Steps in the Application

### Generate Your First Run

1. Navigate to the **Pipeline** page from the sidebar.
2. Select **"Run ID (I11)"** mode.
3. Configure the number of exposures (default: 36,000).
4. Click **"Lancer Pipeline E2E"** to generate a complete run.
5. Wait for the pipeline to complete (approximately 10-30 seconds).

### Explore the Results

The pipeline generates results across multiple risk modules:

- **Monte Carlo**: View simulation results and distributions
- **RWA**: Examine Risk-Weighted Assets by exposure class
- **SA-CCR**: Analyze counterparty credit risk for derivatives
- **CVA**: Review Credit Valuation Adjustment calculations
- **LCR**: Check Liquidity Coverage Ratio compliance
- **Capital**: Verify capital adequacy ratios (CET1, Tier 1, Total)
- **ECL**: Calculate Expected Credit Loss under IFRS 9

### Calculate IFRS 9 ECL

1. Navigate to the **💰 ECL** page.
2. Select your run ID from the dropdown.
3. Choose a scenario (e.g., "baseline_2025").
4. Click **"Calculer ECL"**.
5. Explore the results in the four tabs:
   - **Overview**: Summary statistics and stage distribution
   - **By Exposure**: Detailed ECL for each exposure
   - **By Segment**: Aggregated ECL by business segment
   - **Export**: Download results in various formats

### Generate Regulatory Reports

1. Navigate to the **Reporting** page.
2. Select your run ID.
3. Choose the report type (COREP or FINREP).
4. Click **"Generate Report"**.
5. Download the generated Excel file.

## Running Tests

To verify that everything is working correctly:

```bash
pytest tests/ -v
```

Expected result: 269/273 tests passing (4 legacy failures are known and documented).

## Troubleshooting

### Common Errors and Solutions

#### 1. ModuleNotFoundError: No module named 'db.models'

**Error**:
```
ModuleNotFoundError: No module named 'db.models'
```

**Solution**: Database migrations not applied. Run:
```bash
alembic upgrade head
```

#### 2. Database is Locked (SQLite)

**Error**:
```
sqlite3.OperationalError: database is locked
```

**Solution**: SQLite doesn't support concurrent writes. For multi-user or production environments, switch to PostgreSQL:

1. Install PostgreSQL (see [docs/MIGRATION_POSTGRESQL.md](docs/MIGRATION_POSTGRESQL.md))
2. Update `.env`:
   ```bash
   DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/banking_simulator
   ```
3. Run migrations: `alembic upgrade head`

#### 3. Alembic Revision Not Found

**Error**:
```
alembic.util.exc.CommandError: Can't locate revision identified by 'xyz'
```

**Solution**: Database schema out of sync. Downgrade and re-upgrade:
```bash
alembic downgrade -1
alembic upgrade head
```

If that doesn't work, reset database:
```bash
rm data/app.db  # or drop PostgreSQL database
alembic upgrade head
```

#### 4. Import Errors (Missing Dependencies)

**Error**:
```
ImportError: cannot import name 'X' from 'src.domain'
```

**Solution**: Dependencies not installed or virtual environment not activated:
```bash
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

If still failing, try reinstalling:
```bash
pip install --force-reinstall -r requirements.txt
```

#### 5. Port Already in Use

**Error**:
```
OSError: [Errno 48] Address already in use
```

**Solution**: Port 8501 already used by another Streamlit instance:
```bash
streamlit run app/main.py --server.port 8502
```

Or kill existing process:
```bash
# Find process
lsof -ti:8501

# Kill process (replace PID)
kill -9 <PID>
```

#### 6. Tests Failing

**Error**:
```
pytest tests/ -v
# Some tests fail unexpectedly
```

**Solution**:
1. Ensure database is initialized: `alembic upgrade head`
2. Check Python version: `python --version` (must be 3.11+)
3. Run tests with verbose output to identify issue:
   ```bash
   pytest tests/ -v --tb=short
   ```

Expected: 269/273 tests passing (4 UI smoke tests may fail due to Streamlit mocking)

#### 7. Cache Errors

**Error**:
```
FileNotFoundError: [Errno 2] No such file or directory: './data/artifacts/...'
```

**Solution**: Artifact directory doesn't exist. Create it:
```bash
mkdir -p data/artifacts
```

Or switch to database storage in `.env`:
```bash
ARTIFACT_STORE=database
```

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Review the [CHANGELOG.md](CHANGELOG.md) to understand recent changes
- Check the [CONTRIBUTING.md](CONTRIBUTING.md) if you want to contribute
- Explore the `docs/` directory for iteration-specific documentation

## Getting Help

If you encounter issues:

1. Check the existing [GitHub Issues](https://github.com/your-username/banking-simulator/issues)
2. Review the documentation in the `docs/` directory
3. Open a new issue using the bug report template

Enjoy using Banking Simulator!

