"""Make the shell's config available to templates as `shell`.

A project adds "capy_shell.context_processors.shell" to its template
context_processors so the shell base template can read the content container's
width and padding and the brand link.
"""

from . import conf


def shell(request):
    return {
        "shell": {
            "content_max_width": conf.get("CAPY_SHELL_CONTENT_MAX_WIDTH"),
            "content_padding": conf.get("CAPY_SHELL_CONTENT_PADDING"),
            "home_url": conf.get("CAPY_SHELL_HOME_URL"),
            "header_sticky": conf.get("CAPY_SHELL_HEADER_STICKY"),
            "sidebar": conf.get("CAPY_SHELL_SIDEBAR"),
            "sidebar_width": conf.get("CAPY_SHELL_SIDEBAR_WIDTH"),
            "sidebar_sticky": conf.get("CAPY_SHELL_SIDEBAR_STICKY"),
            "aside": conf.get("CAPY_SHELL_ASIDE"),
            "aside_width": conf.get("CAPY_SHELL_ASIDE_WIDTH"),
            "aside_sticky": conf.get("CAPY_SHELL_ASIDE_STICKY"),
            "footer": conf.get("CAPY_SHELL_FOOTER"),
        }
    }
