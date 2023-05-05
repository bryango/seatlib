import os
import sys

import pytest

PREFS_PATH_LINUX = os.path.expanduser('~/.config/seatlib/prefs.yml')


def rm_prefs():
    """ remove installed prefs """
    if sys.platform == 'linux':
        try:
            os.remove(PREFS_PATH_LINUX)
            print(f"# {PREFS_PATH_LINUX} removed")
        except FileNotFoundError:
            print(f"# {PREFS_PATH_LINUX} not found")
            pass


@pytest.fixture
def cleanup_prefs():
    """ clean up before and after the test """
    rm_prefs()  # before
    yield
    rm_prefs()  # after


def test_prefs(cleanup_prefs):
    """ check if default prefs are correctly generated """

    import seatlib  # when imported
    prefs_path = seatlib.find_config(seatlib.PREFS_YML)
    assert os.path.exists(prefs_path)

    if sys.platform == 'linux':
        assert prefs_path == PREFS_PATH_LINUX
