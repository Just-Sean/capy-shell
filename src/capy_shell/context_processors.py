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
        }
    }
