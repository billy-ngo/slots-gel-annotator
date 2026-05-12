"""
Slots Gel Annotator
===================

Vector-native gel annotation. The display IS the export: every annotation
the user creates lives as a real SVG element, and PNG export rasterizes
that same SVG. There is no second renderer.

The package ships:

* A FastAPI backend (``gel_annotator.server``) that decodes raw / TIFF /
  PNG / JPEG images into a canonical 2-D numpy array, generates the
  LUT-stretched preview PNG, computes the saturation overlay, and
  performs the destructive image rotations the user asks for.
* A single-page frontend (``gel_annotator.frontend``) that owns ALL
  rendering — the lane geometry, brackets, ticks, ladder labels, free-
  form annotations, region outline, and saturation overlay are all
  drawn into one SVG element which is also the export source.
* A small CLI (``gel_annotator.cli``) that launches the local server
  and opens the user's browser, with single-instance detection,
  optional auto-update, and desktop-shortcut installation.

Public API: ``__version__``. Everything else is internal — clients
should drive the tool through the ``slots`` CLI or the HTTP endpoints.
"""

__version__ = "1.0.4"
__app_name__ = "Slots Gel Annotator"
