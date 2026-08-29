"""
Mock Pre-Authorization Records — Solution
(Re-exports starter/mock_data.py so there is exactly one copy of the data.)
"""

# The starter file is ALSO called mock_data.py. A plain `from mock_data import
# ...` therefore resolves to *this* module — which Python has already placed in
# sys.modules and is still executing — so the name is not defined yet and the
# import dies with an ImportError. Adding starter/ to sys.path does not help,
# because sys.modules is consulted first. Load the file by path, under a name
# that cannot collide.
import importlib.util as _importlib_util
import os as _os

_starter_path = _os.path.join(_os.path.dirname(__file__), "..", "starter", "mock_data.py")
_spec = _importlib_util.spec_from_file_location("_starter_mock_data", _starter_path)
_starter = _importlib_util.module_from_spec(_spec)
_spec.loader.exec_module(_starter)

PREAUTH_RECORDS = _starter.PREAUTH_RECORDS

__all__ = ["PREAUTH_RECORDS"]
