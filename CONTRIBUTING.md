# Contributing to Banking Simulator

Thank you for considering contributing to Banking Simulator! This document provides guidelines and instructions for contributing to the project.

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the existing issues to avoid duplicates. When you create a bug report, include as many details as possible using the bug report template.

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, please include as many details as possible using the feature request template.

### Pull Requests

The process described here has several goals: maintain Banking Simulator's quality, fix problems that are important to users, and enable a sustainable system for maintainers to review contributions.

Please follow these steps:

1. Fork the repository and create your branch from `develop`.
2. If you've added code that should be tested, add tests.
3. If you've changed APIs, update the documentation.
4. Ensure the test suite passes.
5. Make sure your code follows the existing style guidelines.
6. Issue that pull request!

## Development Setup

1. Clone your fork of the repository:
   ```bash
   git clone https://github.com/your-username/banking-simulator.git
   cd banking-simulator
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. Initialize the database:
   ```bash
   alembic upgrade head
   ```

4. Run the tests to ensure everything is working:
   ```bash
   pytest tests/ -v
   ```

## Style Guidelines

### Python Style Guide

This project follows PEP 8 style guidelines with some modifications. Key points include:

- Use 4 spaces for indentation (not tabs)
- Maximum line length of 100 characters
- Use descriptive variable names
- Add docstrings to all functions and classes
- Use type hints where appropriate

### Git Commit Messages

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters or less
- Reference issues and pull requests liberally after the first line

## Architecture Guidelines

Banking Simulator follows a strict 3-layer architecture:

- **Domain Layer** (`src/domain/`): Pure business logic with no external dependencies
- **Service Layer** (`src/services/`): Orchestration between domain and UI
- **Adapter Layer** (`src/adapters/`): Interface between services and external systems
- **UI Layer** (`app/`): Streamlit pages for presentation only

When contributing, please respect this architecture and avoid mixing concerns between layers.

## Testing

All new features and bug fixes should include appropriate tests. The project uses pytest for testing.

Run tests with:
```bash
pytest tests/ -v
```

Check test coverage with:
```bash
pytest tests/ --cov=src --cov-report=html
```

## Documentation

All new features should be documented. This includes:

- Docstrings in the code
- Updates to relevant README files
- Updates to the CHANGELOG.md file
- User-facing documentation in the Streamlit UI where appropriate

## Questions?

If you have questions, please feel free to open an issue with the "question" label.

Thank you for contributing to Banking Simulator!

