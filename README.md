# Banking Simulator

**A comprehensive banking risk management application with Monte Carlo simulations, advanced risk calculations (Credit, Counterparty, Liquidity, Capital), IFRS 9 ECL, and regulatory reporting (COREP/FINREP).**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

This project implements a sophisticated banking simulator built on a strict 3-layer architecture (UI → Services → Domain). It features a Streamlit-based user interface, a powerful Python backend with SQLAlchemy ORM, and a robust testing suite with pytest.

## Key Features

- **Run-Based Architecture**: All calculations are tied to a unique `run_id` for full traceability and auditability, processing over 36,000 exposures across 6 financial product types.
- **IFRS 9 ECL Module**: Advanced Expected Credit Loss calculation with S1/S2/S3 staging, PD term structures, and LGD downturn.
- **Comprehensive Risk Modules**: 
  - Credit Risk: RWA (Standardized Approach)
  - Counterparty Risk: SA-CCR, CVA
  - Liquidity Risk: LCR, NSFR
  - Capital Adequacy: CET1, Tier 1, Total Capital Ratios
- **Regulatory Reporting**: Automated generation of COREP and FINREP reports from a given run.
- **Caching System**: DB-based caching for significant performance improvements (50-150x speedup).
- **Data Export**: Export results to various formats (CSV, Excel, JSON, Parquet).

## Tech Stack

- **Frontend**: Streamlit
- **Backend**: Python 3.11+
- **Database**: SQLite (for development), PostgreSQL (for production)
- **ORM**: SQLAlchemy with Alembic for database migrations
- **Testing**: pytest (269/273 tests passing)

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/banking-simulator.git
   cd banking-simulator
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install the dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize the database:**
   ```bash
   alembic upgrade head
   ```

## Usage

1. **Run the Streamlit application:**
   ```bash
   streamlit run app/main.py
   ```

2. **Access the application in your browser at `http://localhost:8501`.**

3. **New Workflow (Recommended):**
   - Start at the **Home** page (`00_Home.py`) to view existing simulations or create a new one
   - Use the **Simulation** page (`01_Simulation.py`) to generate exposure portfolios with a unique `run_id`
   - Navigate to risk calculation pages (RWA, SA-CCR, LCR, Capital) to perform analyses on your generated portfolios
   - See `docs/README_WORKFLOW_REFACTORING.md` for detailed workflow documentation

## Project Structure

The project follows a strict 3-layer architecture:

- `src/domain`: Contains the core business logic and domain models.
- `src/services`: Implements the application's use cases and orchestrates the domain layer.
- `src/adapters`: Provides the interface between the services and the outside world (e.g., UI, database).
- `app`: Contains the Streamlit user interface and the main application entry point.
- `tests`: Contains the pytest test suite.

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

