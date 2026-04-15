"""Page modules. Kazdy modul registruje @ui.page routes pri importu."""

# Order matters? Only for import-time side effects. All paths independent.
from . import dashboard  # noqa: F401
from . import marathon   # noqa: F401
from . import practice   # noqa: F401
from . import exam       # noqa: F401
from . import srs        # noqa: F401
from . import mastery    # noqa: F401
from . import export     # noqa: F401
from . import settings   # noqa: F401
