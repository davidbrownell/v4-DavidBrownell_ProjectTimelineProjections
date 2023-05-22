# ----------------------------------------------------------------------
# |
# |  Setup_custom.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2023-05-22 15:23:22
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2023
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
# pylint: disable=missing-module-docstring

import os
import uuid                                             # pylint: disable=unused-import

from pathlib import Path
from typing import Dict, List, Optional, Union

from semantic_version import Version as SemVer          # pylint: disable=unused-import

from Common_Foundation.Shell.All import CurrentShell                        # type: ignore  # pylint: disable=import-error,unused-import
from Common_Foundation.Shell import Commands                                # type: ignore  # pylint: disable=import-error,unused-import
from Common_Foundation.Streams.DoneManager import DoneManager               # type: ignore  # pylint: disable=import-error,unused-import
from Common_Foundation import Types                                         # type: ignore  # pylint: disable=import-error,unused-import

from RepositoryBootstrap import Configuration                               # type: ignore  # pylint: disable=import-error,unused-import
from RepositoryBootstrap import Constants                                   # type: ignore  # pylint: disable=import-error,unused-import


# ----------------------------------------------------------------------
# Uncomment the decorator below to make this repository a mixin repository.
# Mixin repositories can not be activated on their own and cannot have tool
# or version specifications. Mixin repositories are valuable because they
# can provide scripts or tools that augment other repositories when activated.
#
# @Configuration.MixinRepository
def GetConfigurations() -> Union[
    Configuration.Configuration,
    Dict[
        str,                                # configuration name
        Configuration.Configuration,
    ],
]:
    common_python_libraries: list[Configuration.VersionInfo] = []

    configurations: dict[str, Configuration.Configuration] = {
        "standard": Configuration.Configuration(
            "Configuration for using the functionality",
            [
                Configuration.Dependency(
                    Constants.COMMON_FOUNDATION_REPOSITORY_ID,
                    "Common_Foundation",
                    "python310",
                    "https://github.com/davidbrownell/v4-Common_Foundation.git",
                ),
            ],
            Configuration.VersionSpecs(
                [],                             # tools
                {
                    "Python": common_python_libraries,
                },                             # libraries
            ),
        ),
        "dev": Configuration.Configuration(
            "Configuration for developing the functionality.",
            [
                Configuration.Dependency(
                    uuid.UUID("e4170a9d-70f9-4615-85b6-d514055e62b6"),
                    "Common_PythonDevelopment",
                    "python310",
                    "https://github.com/davidbrownell/v4-Common_PythonDevelopment.git",
                ),
            ],
            Configuration.VersionSpecs(
                [],                             # tools
                {
                    "Python": common_python_libraries + [
                        Configuration.VersionInfo("cx_freeze", SemVer("6.13.1")),
                    ],
                },                             # libraries
            ),
        ),
    }

    return configurations


# ----------------------------------------------------------------------
# Note that it is safe to remove this function if it will never be used.
def GetCustomActions(
    # Note that it is safe to remove any parameters that are not used
    dm: DoneManager,                                    # pylint: disable=unused-argument
    explicit_configurations: Optional[List[str]],       # pylint: disable=unused-argument
    force: bool,                                        # pylint: disable=unused-argument
    interactive: Optional[bool],                        # pylint: disable=unused-argument
) -> List[Commands.Command]:
    commands: List[Commands.Command] = []

    root_dir = Path(__file__).parent
    assert root_dir.is_dir(), root_dir

    # Create a link to the foundation's .pylintrc file
    foundation_root_file = Path(Types.EnsureValid(os.getenv(Constants.DE_FOUNDATION_ROOT_NAME))) / ".pylintrc"
    assert foundation_root_file.is_file(), foundation_root_file

    commands.append(
        Commands.SymbolicLink(
            root_dir / foundation_root_file.name,
            foundation_root_file,
            remove_existing=True,
            relative_path=True,
        ),
    )

    return commands
