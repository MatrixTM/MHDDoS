# Contributing to MHDDoS

Thanks for taking the time to contribute. This project is a stress-testing toolkit; keep changes focused, tested, and safe.

## Before you start

- Read the [wiki](https://github.com/MatrixTM/MHDDoS/wiki), especially [Usage](https://github.com/MatrixTM/MHDDoS/wiki/Usage) and [Safety](https://github.com/MatrixTM/MHDDoS/wiki/Safety).
- Search existing issues and discussions before opening a new one.
- For a large change or a new method, open an issue first. New attack methods need a maintainer decision.
- Do not include real proxy credentials, API keys, private keys, or third-party target data.

## Development setup

```bash
git clone https://github.com/MatrixTM/MHDDoS.git
cd MHDDoS
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python start.py DOCTOR
```

For the web panel:

```bash
bash web/scripts/install.sh
```

## Checks

Run these before opening a pull request:

```bash
python -m py_compile start.py web/app.py
uvx ruff check start.py web/app.py
uvx ruff format --check start.py web/app.py
python start.py DOCTOR
```

If you touched the web panel:

```bash
cd web
npm ci
npm run build
```

## Code style

- Python 3.11+.
- Ruff formatting, 100-column lines, double quotes.
- Keep `start.py` a single file; it is executed directly and by the panels.
- Put payload construction in the method handler.
- Do not add broad `except` blocks in hot loops; worker errors are handled at the thread boundary.
- Comments should explain why, not restate the code.

## Adding a method

1. Add the name to the right method set in `Methods`.
2. Map the name to a handler in `Layer4` or `HttpFlood`.
3. Implement the handler.
4. Register raw-socket or proxy requirements.
5. Update the README table and the wiki.
6. Explain the purpose and the expected environment in the pull request.

## Pull requests

- Keep one change per pull request.
- Use a clear title and describe the reason, not just the diff.
- Link the issue it closes.
- Include the commands you ran and the result.
- Expect review comments about safety and scope.

## Discussions

Use Discussions for questions, setup help, ideas, and show-and-tell. Use Issues for reproducible bugs and scoped feature requests. Use private security advisories for vulnerabilities.

## License

By contributing, you agree that your changes are licensed under the MIT license.
