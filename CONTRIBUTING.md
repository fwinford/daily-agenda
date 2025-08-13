# Contributing to Daily Agenda

Thank you for your interest in contributing to the Daily Agenda project! 

## Getting Started

1. **Fork the repository**
2. **Clone your fork:**
   ```bash
   git clone https://github.com/yourusername/daily-agenda.git
   cd daily-agenda
   ```

3. **Set up the development environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

4. **Set up your configuration:**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   # Update config.yaml with your database IDs
   ```

5. **Validate your setup:**
   ```bash
   ./.venv/bin/python validate_setup.py
   ```

## Development Workflow

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**

3. **Run tests:**
   ```bash
   ./.venv/bin/python run_tests.py
   ```

4. **Test the application:**
   ```bash
   ./.venv/bin/python main.py
   ```

5. **Commit and push:**
   ```bash
   git add .
   git commit -m "Add: your feature description"
   git push origin feature/your-feature-name
   ```

6. **Create a Pull Request**

## Code Style

- Follow PEP 8 for Python code style
- Add docstrings to new functions
- Include type hints where appropriate
- Add unit tests for new functionality

## Testing

- All new features should have corresponding unit tests
- Tests should be placed in the `tests/` directory
- Run the full test suite before submitting PRs

## Areas for Contribution

- **New calendar sources** (Outlook, CalDAV, etc.)
- **Additional Notion field types** (dates, numbers, etc.)  
- **Email template improvements**
- **Error handling and retry logic**
- **Performance optimizations**
- **Documentation improvements**

## Questions?

Feel free to open an issue for questions or suggestions!
