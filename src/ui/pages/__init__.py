"""Page modules. Kazdy modul registruje @ui.page routes pri importu."""

# Order matters? Only for import-time side effects. All paths independent.
from . import (
    admin,  # noqa: F401
    dashboard,  # noqa: F401
    diagnostika,  # noqa: F401
    exam,  # noqa: F401
    export,  # noqa: F401
    marathon,  # noqa: F401
    mastery,  # noqa: F401
    patterns,  # noqa: F401
    practice,  # noqa: F401
    settings,  # noqa: F401
    srs,  # noqa: F401
    study,  # noqa: F401
)
