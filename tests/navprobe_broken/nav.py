"""A nav.py whose own import is broken — for the re-raise test. NOT in INSTALLED_APPS,
so it only loads when a test imports it directly via _import_nav."""

import capy_shell_this_module_does_not_exist as missing

NAV = [missing]  # Never reached: importing `missing` above fails first.
