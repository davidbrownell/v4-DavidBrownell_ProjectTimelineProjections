# ----------------------------------------------------------------------
# |
# |  Activate_custom.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2023-05-22 15:24:26
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2023
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
# pylint: disable=invalid-name
# pylint: disable=missing-module-docstring

import os

from pathlib import Path
from typing import List, Optional

from Common_Foundation.Shell import Commands                                # type: ignore  # pylint: disable=import-error,unused-import
from Common_Foundation.Shell.All import CurrentShell                        # type: ignore  # pylint: disable=import-error,unused-import
from Common_Foundation.Streams.DoneManager import DoneManager               # type: ignore  # pylint: disable=import-error,unused-import
from Common_Foundation import SubprocessEx                                  # type: ignore  # pylint: disable=import-error,unused-import

from RepositoryBootstrap import Configuration                               # type: ignore  # pylint: disable=import-error,unused-import
from RepositoryBootstrap import DataTypes                                   # type: ignore  # pylint: disable=import-error,unused-import


# ----------------------------------------------------------------------
# Note that it is safe to remove this function if it will never be used.
def GetCustomActions(                                                       # pylint: disable=too-many-arguments
    # Note that it is safe to remove any parameters that are not used
    dm: DoneManager,                                                        # pylint: disable=unused-argument
    repositories: List[DataTypes.ConfiguredRepoDataWithPath],               # pylint: disable=unused-argument
    generated_dir: Path,                                                    # pylint: disable=unused-argument
    configuration: Optional[str],                                           # pylint: disable=unused-argument
    version_specs: Configuration.VersionSpecs,                              # pylint: disable=unused-argument
    force: bool,                                                            # pylint: disable=unused-argument
    is_mixin_repo: bool,                                                    # pylint: disable=unused-argument
) -> List[Commands.Command]:
    """Returns a list of actions that should be invoked as part of the activation process."""

    commands: list[Commands.Command] = []

    # Ensure that npm is installed
    binary_name = "npm"
    retries = 0

    while True:
        result = SubprocessEx.Run('"{}" --version'.format(binary_name))
        if result.returncode == 0:
            break

        if CurrentShell.family_name == "Windows" and retries == 0:
            binary_name = Path(os.getenv("ProgramFiles")) / "nodejs" / "npm.cmd"
            if binary_name.is_file():
                commands.append(Commands.AugmentPath.Create(str(binary_name.parent)))

                retries += 1
                continue

        dm.WriteError("\nnpm must be installed and available.\n")
        return []

    # Ensure that node_modules/.bin is on the path.
    commands.append(Commands.AugmentPath.Create(str(Path(__file__).parent / "src" / "ProjectTimelineProjections" / "src" / "node_modules" / ".bin")))

    return commands
