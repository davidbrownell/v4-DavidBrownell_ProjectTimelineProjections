# ----------------------------------------------------------------------
# |
# |  Build.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2023-11-02 09:36:41
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2023
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Builds ProjectTimelineProjections"""

import re
import shutil

from enum import auto, Enum
from pathlib import Path
from typing import Callable, Optional, TextIO, Union

from Common_Foundation import PathEx
from Common_Foundation import SubprocessEx
from Common_Foundation.Streams.DoneManager import DoneManager, DoneManagerFlags
from Common_Foundation.Types import overridemethod

from Common_FoundationEx.BuildImpl import BuildInfoBase


# ----------------------------------------------------------------------
class BuildInfo(BuildInfoBase):
    # ----------------------------------------------------------------------
    # |
    # |  Public Types
    # |
    # ----------------------------------------------------------------------
    class BuildSteps(Enum):
        Install                             = 0
        Build                               = auto()
        Copy                                = auto()
        RemoveDir                           = auto()

    # ----------------------------------------------------------------------
    # |
    # |  Public Functions
    # |
    # ----------------------------------------------------------------------
    def __init__(self):
        super(BuildInfo, self).__init__(
            name="ProjectTimelineProjections",
            configurations=None,
            requires_output_dir=True,
            required_development_configurations=[
                re.compile("dev"),
            ],
        )

    # ----------------------------------------------------------------------
    @overridemethod
    def GetNumBuildSteps(
        self,
        configuration: str | None,
    ) -> int:
        return len(self.__class__.BuildSteps)

    # ----------------------------------------------------------------------
    @overridemethod
    def Build(                              # pylint: disable=arguments-differ
        self,
        configuration: Optional[str],       # pylint: disable=unused-argument
        output_dir: Path,
        output_stream: TextIO,
        on_progress_update: Callable[       # pylint: disable=unused-argument
            [
                int,                        # Step ID
                str,                        # Status info
            ],
            bool,                           # True to continue, False to terminate
        ],
        *,
        is_verbose: bool,
        is_debug: bool,
        force: bool=False,                  # pylint: disable=unused-argument
    ) -> Union[
        int,                                # Error code
        tuple[int, str],                    # Error code and short text that provides info about the result
    ]:
        this_dir = Path(__file__).parent.resolve()

        with DoneManager.Create(
            output_stream,
            "Building...",
            output_flags=DoneManagerFlags.Create(verbose=is_verbose, debug=is_debug),
        ) as dm:
            on_progress_update(self.__class__.BuildSteps.Install.value, "Installing dependencies...")

            with dm.Nested("Installing dependencies...") as install_dm:
                with install_dm.YieldStream() as stream:
                    install_dm.result = SubprocessEx.Stream(
                        "npm install",
                        stream,
                        this_dir,
                    )

                    if install_dm.result != 0:
                        return install_dm.result

            on_progress_update(self.__class__.BuildSteps.Build.value, "Building content...")

            with dm.Nested("Building content...") as build_dm:
                with build_dm.YieldStream() as stream:
                    build_dm.result = SubprocessEx.Stream(
                        "npm run build",
                        stream,
                        this_dir,
                    )

                    if build_dm.result != 0:
                        return build_dm.result

            dist_dir = PathEx.EnsureDir(this_dir / "dist")

            on_progress_update(self.__class__.BuildSteps.Copy.value, "Copying content...")

            with dm.Nested("Copying content..."):
                PathEx.RemoveTree(output_dir)
                shutil.copytree(dist_dir, output_dir)

            on_progress_update(self.__class__.BuildSteps.RemoveDir.value, "Removing dist dir...")

            with dm.Nested("Removing dist dir..."):
                PathEx.RemoveTree(dist_dir)

            return dm.result

    # ----------------------------------------------------------------------
    @overridemethod
    def Clean(                              # pylint: disable=arguments-differ
        self,
        configuration: Optional[str],       # pylint: disable=unused-argument
        output_dir: Path,
        output_stream: TextIO,
        on_progress_update: Callable[       # pylint: disable=unused-argument
            [
                int,                        # Step ID
                str,                        # Status info
            ],
            bool,                           # True to continue, False to terminate
        ],
        *,
        is_verbose: bool,
        is_debug: bool,
    ) -> Union[
        int,                                # Error code
        tuple[int, str],                    # Error code and short text that provides info about the result
    ]:
        with DoneManager.Create(
            output_stream,
            "Cleaning...",
            output_flags=DoneManagerFlags.Create(verbose=is_verbose, debug=is_debug),
        ) as dm:
            if not output_dir.is_dir():
                dm.WriteLine("The directory '{}' does not exist.\n".format(output_dir))
            else:
                with dm.Nested("Removing '{}'...".format(output_dir)):
                    PathEx.RemoveTree(output_dir)

            return dm.result


# ----------------------------------------------------------------------
def Install():
    """Installs development dependencies"""

    with DoneManager.CreateCommandLine(
        output_flags=DoneManagerFlags.Create(debug=False, verbose=False),
    ) as dm:
        with dm.Nested("Running 'npm install'...") as install_dm:
            with install_dm.YieldStream() as stream:
                install_dm.result = SubprocessEx.Stream(
                    "npm install",
                    stream,
                    Path(__file__).parent.resolve(),
                )


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    BuildInfo().Run()
