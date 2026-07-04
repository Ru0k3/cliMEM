from .claude import configure as configure_claude
from .claude import restore as restore_claude
from .codex import configure as configure_codex
from .codex import restore as restore_codex
from .opencode import configure as configure_opencode
from .opencode import restore as restore_opencode

HANDLERS = {
    "opencode": {
        "configure": configure_opencode,
        "restore": restore_opencode,
    },
    "claude": {
        "configure": configure_claude,
        "restore": restore_claude,
    },
    "codex": {
        "configure": configure_codex,
        "restore": restore_codex,
    },
}