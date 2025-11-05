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

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

This will install all required packages including Streamlit, SQLAlchemy, pandas, and pytest.

### 4. Initialize the Database

```bash
alembic upgrade head
```

This creates the SQLite database and applies all migrations.

### 5. Run the Application

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

### Port Already in Use

If port 8501 is already in use, you can specify a different port:

```bash
streamlit run app/main.py --server.port 8502
```

### Database Errors

If you encounter database errors, try resetting the database:

```bash
rm banking_app.db
alembic upgrade head
```

### Import Errors

Make sure your virtual environment is activated and all dependencies are installed:

```bash
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
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

