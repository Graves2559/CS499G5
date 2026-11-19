To test,
1. cd to backend
2. [Terminal] pytest -v (for all)
3. [Terminal] pytest -v tests/(specific test file)

Requirement test cases (the numbered items marked DONE: 1, 2, 5, 9, 10; test names start with `test_reqNN_`):
- `tests/test_requirements.py`: fast, no server or database needed (in-memory fakes).
- `tests/e2e/test_e2e_requirements.py`: end to end over HTTP against the RUNNING app, so start it first with `docker compose up -d`. It is skipped automatically if the app is not running. It creates its own throw-away users and deletes them (and their files) afterwards.
- Item 9 (restart) restarts the Docker containers, so it only runs when asked: `E2E_RESTART=1 pytest -v tests/e2e -k req09`
- By requirement number: `pytest -v -k req02` (all tests for requirement 2).