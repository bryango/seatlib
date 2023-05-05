import os
import sys

import pytest

PREFS_PATHS_LINUX : list[str] = [
    os.path.expanduser(yml_config)
    for yml_config in [
        '~/.config/seatlib/prefs.yml',
        '~/.config/seatlib/hates.yml',
    ]
]

def rm_prefs():
    """ remove installed prefs """
    if sys.platform == 'linux':
        for yml_config in PREFS_PATHS_LINUX:
            try:
                os.remove(yml_config)
                print(f"# {yml_config} removed")
            except FileNotFoundError:
                print(f"# {yml_config} not found")
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
    prefs_paths = [
        seatlib.find_config(yml_config)
        for yml_config in [
            seatlib.PREFS_YML,
            seatlib.HATES_YML
        ]
    ]
    assert all(os.path.exists(yml_config) for yml_config in prefs_paths)

    if sys.platform == 'linux':
        assert prefs_paths == PREFS_PATHS_LINUX
