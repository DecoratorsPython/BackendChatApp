# Backend Coding & Git Conventions

This document describes the rules and conventions that must be followed in this project to ensure clean, consistent, and maintainable code, as well as a predictable Git history.

It covers:

- **Python code style rules** (PEP8, enforced via Black + Ruff)
- **Git branch naming conventions**
- **Git commit message conventions**

These rules are enforced automatically via **pre-commit hooks**.

---


## 1. Python Code Style (PEP8 + Black + Ruff)

### 1.1. Naming Conventions

We follow PEP8 naming standards:

| Element | Style | Example |
|---------|--------|---------|
| Variables | `snake_case` | `total_amount`, `user_name` |
| Functions | `snake_case` | `get_employee_by_id()` |
| Classes | `PascalCase` | `EmployeeService`, `AuthRepository` |
| Constants | `UPPER_CASE` | `MAX_RETRIES`, `DEFAULT_TIMEOUT` |
| Files / Modules | `snake_case` | `auth_service.py`, `employee_repository.py` |

Avoid vague names like `data`, `x`, `foo`, except in trivial cases (e.g., small comprehensions).

---

### 1.2. Formatting Rules (Black)

All code is formatted using **Black**, which enforces:

- 4 spaces per indentation level
- maximum line length of **79 characters**
- consistent spacing and parentheses
- unified quoting style (Black chooses automatically)
- no manual formatting required

---

### 1.3. Linting Rules (Ruff)

**Ruff** enforces additional correctness and style rules.

Commit creation is blocked if Ruff detects:

- unused imports or unused variables
- undefined variables
- bad formatting not aligned with PEP8
- overly complex expressions that can be simplified
- syntax problems
- import order issues

---


## 2. Git Branch Naming Conventions

Branches must follow one of the **three allowed prefixes**:

- `feature/` — for new features
- `fix/` — for bug fixes
- `test/` — for testing, experiments, spikes

### 2.1. Valid Formats

- feature/TASK-<number>
- feature/TASK-<number>-<description>

- fix/TASK-<number>
- fix/TASK-<number>-<description>

- test/TASK-<number>
- test/TASK-<number>-<description>

Where:

- `<number>` is any natural number (1, 2, 10, 100, …)
- `<description>` is optional, **but must not contain spaces**
- Description may contain:  
  - letters (a–z, A–Z)
  - digits (0–9)
  - `_` or `-`


## 3. Git Commit Message Conventions

Commit messages must follow this format:

- TASK-<number>-<description>

Where:

- `<number>` = natural number corresponding to the task ID
- `<description>` = short, meaningful summary of the change

## 4. How to apply the pre-commit hooks

- install in the local virtual environment the libraries from requirements.txt:
  pip install requirements.txt
- in the same folder, install the pre-commit:
  pre-commit install
- if you want to skip the verification step, use --no-verify:
  git commit --no-verify -m "TASK-1-Example"
