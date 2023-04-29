import os
import sys

PREFS_PATH_LINUX = os.path.expanduser('~/.config/seatlib/prefs.yml')

def rm_prefs():
    """ clean up previously installed prefs """
    if sys.platform == 'linux':
        try:
            os.remove(PREFS_PATH_LINUX)
        except FileNotFoundError:
            pass

def test_prefs():
    """ check if default prefs are correctly generated """

    rm_prefs()

    import seatlib  # when imported
    prefs_path = seatlib.find_config(seatlib.PREFS_YML)
    assert os.path.exists(prefs_path)

    if sys.platform == 'linux':
        assert prefs_path == PREFS_PATH_LINUX
