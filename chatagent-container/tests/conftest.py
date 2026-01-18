def pytest_addoption(parser):
    parser.addoption(
        "--enable-livellm", action="store_true", help="Enable live LLM tests"
    )
