# *******************************************************************************
# Copyright (c) 2024 Contributors to the Eclipse Foundation
#
# See the NOTICE file(s) distributed with this work for additional
# information regarding copyright ownership.
#
# This program and the accompanying materials are made available under the
# terms of the Apache License Version 2.0 which is available at
# https://www.apache.org/licenses/LICENSE-2.0
#
# SPDX-License-Identifier: Apache-2.0
# *******************************************************************************

"""
This extension sets up PlantUML within the SCORE Bazel environment.

The complexity arises, as the plantuml binary is only available through Bazel.
However going through `bazel run //docs:plantuml` for every PlantUML diagram
is simply too slow.

This extension determines the path to the plantuml binary and sets it up in the
Sphinx configuration.

In addition it sets common PlantUML options, like output to svg_obj.
"""

from gettext import find
import os
import sys
from pathlib import Path

from sphinx.application import Sphinx
from sphinx.util import logging

logger = logging.getLogger(__name__)


def get_runfiles_dir() -> Path:
    if r := os.getenv("RUNFILES_DIR"):
        # Runfiles are only available when running in Bazel.
        # bazel build and bazel run are both supported.
        # i.e. `bazel build //docs:docs` and `bazel run //docs:incremental`.
        logger.debug("Using runfiles to determine plantuml path.")

        runfiles_dir = Path(r)

    else:
        # The only way to land here is when running from within the virtual
        # environment created by the `docs:ide_support` rule in the BUILD file.
        # i.e. esbonio or manual sphinx-build execution within the virtual
        # environment.
        # We'll still use the plantuml binary from the bazel build.
        # But we need to find it first.
        logger.debug("Running outside bazel.")

        git_root = Path.cwd().resolve()
        while not (git_root / ".git").exists():
            git_root = git_root.parent
            if git_root == Path("/"):
                sys.exit("Could not find git root.")

        runfiles_dir = git_root / "bazel-bin" / "docs" / "ide_support.runfiles"

    if not runfiles_dir.exists():
        sys.exit(
            f"Could not find runfiles_dir at {runfiles_dir}. "
            "Have a look at README.md for instructions on how to build docs."
        )
    return runfiles_dir


def find_correct_path(runfiles: str) -> str:
    """
    This ensures that the 'plantuml' binary path is found in local 'score_docs_as_code' and module use.
    """
    dirs = [str(x) for x in Path(runfiles).glob("*score_docs_as_code~")]
    if dirs:
        # Happens if 'score_docs_as_code' is used as Module
        p = runfiles + "/score_docs_as_code~/src/plantuml"
    else:
        # Only happens in 'score_docs_as_code' repository
        p = runfiles + "/../plantuml"
    return p


def setup(app: Sphinx):
    app.config.plantuml = find_correct_path(str(get_runfiles_dir()))
    app.config.plantuml_output_format = "svg_obj"
    app.config.plantuml_syntax_error_image = True
    app.config.needs_build_needumls = "_plantuml_sources"

    logger.debug(f"PlantUML binary found at {app.config.plantuml}")

    # The extension is not even active at runtime.
    return {"parallel_read_safe": True, "parallel_write_safe": True}
