def test_main_has_fetch_user_data():
    # Import main.py by path to avoid module resolution issues in test runner
    import importlib.util
    import os
    path = os.path.join(os.path.dirname(__file__), '..', 'main.py')
    path = os.path.abspath(path)
    spec = importlib.util.spec_from_file_location('main_test', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert hasattr(module, 'fetch_user_data')
