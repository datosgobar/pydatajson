import io
import json
import os
from functools import wraps

RESULTS_DIR = os.path.join("tests", "results")


def load_expected_result():
    def case_decorator(test):
        case_filename = test.__name__.split("test_")[-1]

        @wraps(test)
        def decorated_test(*args, **kwargs):
            result_path = os.path.join(
                RESULTS_DIR, case_filename + ".json")

            with io.open(result_path, encoding='utf8') as result_file:
                expected_result = json.load(result_file)

            kwargs["expected_result"] = expected_result
            test(*args, **kwargs)

        return decorated_test

    return case_decorator


def load_case_filename():
    def case_decorator(test):
        case_filename = test.__name__.split("test_validity_of_")[-1]

        @wraps(test)
        def decorated_test(*args, **kwargs):
            kwargs["case_filename"] = case_filename
            test(*args, **kwargs)

        return decorated_test

    return case_decorator