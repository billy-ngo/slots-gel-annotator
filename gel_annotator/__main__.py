"""Allow ``python -m gel_annotator`` to launch the same CLI as ``slots``.

This is a thin shim — all the real work lives in :mod:`gel_annotator.cli`.
The Windows-specific event-loop fix is duplicated here (in addition to
``cli.main``) so that ``python -m gel_annotator`` from a fresh shell on
Windows doesn't crash if uvicorn picks the proactor policy before our
own setup runs.
"""

import sys

if sys.platform == "win32":
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from gel_annotator.cli import main

if __name__ == "__main__":
    sys.exit(main())
