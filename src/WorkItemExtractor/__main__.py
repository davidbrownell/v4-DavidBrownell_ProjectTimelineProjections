# ----------------------------------------------------------------------
# |
# |  __main__.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2023-05-22 16:04:32
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2023
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Extracts work items for a project."""

import importlib
import json
import sys
import textwrap

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from functools import singledispatchmethod
from pathlib import Path
from typing import Any, cast, Optional

import typer

from typer.core import TyperGroup

from Common_Foundation.ContextlibEx import ExitStack
from Common_Foundation import PathEx
from Common_Foundation.Streams.DoneManager import DoneManager, DoneManagerFlags
from Common_Foundation import TextwrapEx
from Common_Foundation import Types

from Common_FoundationEx.InflectEx import inflect

from Common.Plugin import Plugin                                                # type: ignore;  pylint: disable=import-error
from GenerateEvents import GenerateEvents as GenerateEventsImpl                 # type: ignore;  pylint: disable=import-error
from GenerateHierarchies import GenerateHierarchies as GenerateHierarchiesImpl  # type: ignore;  pylint: disable=import-error


# ----------------------------------------------------------------------
def _LoadPlugins() -> dict[str, Plugin]:
    root_dir = PathEx.EnsureDir(Path(__file__).parent.parent)

    sys.path.insert(0, str(root_dir))
    with ExitStack(lambda: sys.path.pop(0)):
        plugin_dir = PathEx.EnsureDir(root_dir / "WorkItemExtractor" / "ProjectManagementPlugins")

        sys.path.insert(0, str(plugin_dir))
        with ExitStack(lambda: sys.path.pop(0)):
            # ----------------------------------------------------------------------
            @dataclass(frozen=True)
            class PluginData(object):
                filename: Path
                plugin: Plugin

            # ----------------------------------------------------------------------

            potential_plugin_names: list[str] = ["Plugin", ]
            all_plugins: dict[str, PluginData] = {}

            for filename in plugin_dir.iterdir():
                if filename.suffix != ".py":
                    continue

                if not filename.stem.endswith("Plugin"):
                    continue

                mod = importlib.import_module(filename.stem)

                plugin: Optional[Plugin] = None

                for potential_plugin_name in potential_plugin_names:
                    potential_plugin = getattr(mod, potential_plugin_name, None)
                    if potential_plugin is None:
                        continue

                    plugin = cast(Plugin, potential_plugin())
                    break

                if plugin is None:
                    raise Exception("A plugin was not found in '{}'.".format(filename))

                prev_plugin = all_plugins.get(plugin.name, None)
                if prev_plugin is not None:
                    raise Exception(
                        "The plugin '{}', defined in '{}', was already defined in '{}'.".format(
                            plugin.name,
                            filename,
                            prev_plugin.filename,
                        ),
                    )

                all_plugins[plugin.name] = PluginData(filename, plugin)

            if not all_plugins:
                raise Exception("No plugins were found in '{}'.".format(plugin_dir))

            # If here, all plugins are valid and there weren't any conflicts
            return {k: v.plugin for k, v in all_plugins.items()}


_PLUGINS                                    = _LoadPlugins()
_PLUGIN_NAMES_ENUM                          = Types.StringsToEnum("_PLUGIN_NAMES_ENUM", _PLUGINS.keys())

del _LoadPlugins


# ----------------------------------------------------------------------
class NaturalOrderGrouper(TyperGroup):
    # pylint: disable=missing-class-docstring
    # ----------------------------------------------------------------------
    def list_commands(self, *args, **kwargs):  # pylint: disable=unused-argument
        return self.commands.keys()


# ----------------------------------------------------------------------
def _HelpEpilog() -> str:
    return textwrap.dedent(
        """\

        Plugins:

            {}

        """,
    ).format(
        TextwrapEx.Indent(
            TextwrapEx.CreateTable(
                ["Name", "Description"],
                [
                    [plugin.name, plugin.__doc__ or ""]
                    for plugin in _PLUGINS.values()
                ],
            ),
            4,
            skip_first_line=False,
        ),
    ).replace("\n", "\n\n")


# ----------------------------------------------------------------------
app                                         = typer.Typer(
    cls=NaturalOrderGrouper,
    help=__doc__,
    no_args_is_help=True,
    pretty_exceptions_show_locals=False,
    rich_markup_mode="rich",
    epilog=_HelpEpilog(),
)


# ----------------------------------------------------------------------
@app.command(
    "GenerateHierarchies",
    epilog=_HelpEpilog(),
    help=__doc__,
    no_args_is_help=True,
)
def GenerateHierarchies(
    plugin_name: _PLUGIN_NAMES_ENUM=typer.Argument(..., help="Name of the plugin used to extract information about work items."),  # type: ignore
    url: str=typer.Argument(..., help="Url associated with work items to extract."),
    username: str=typer.Argument(..., help="Username associated with work items to extract."),
    api_token_or_filename: str=typer.Argument(..., help="API token (or filename containing an API token) associated with the work items to extract."),
    output_filename: Path=typer.Argument(..., dir_okay=False, help="Output filename for extracted information."),
    root_work_item_ids: list[str]=typer.Option(None, "--id", help="Work item IDs associated with the root of one or more work item hierarchies."),
    verbose: bool=typer.Option(False, "--verbose", help="Write verbose information to the terminal."),
    debug: bool=typer.Option(False, "--debug", help="Write debug information to the terminal."),
) -> None:
    """Generates hierarchical information associated with one or more work items."""

    with DoneManager.CreateCommandLine(
        output_flags=DoneManagerFlags.Create(verbose=verbose, debug=debug),
    ) as dm:
        plugin = _InitPlugin(dm, plugin_name, url, username, api_token_or_filename)
        if plugin is None:
            return

        root_work_item_ids = _InitRootWorkItems(dm, plugin, root_work_item_ids)
        if not root_work_item_ids:
            return

        hierarchy_info = GenerateHierarchiesImpl(dm, plugin, root_work_item_ids)
        if hierarchy_info is None:
            return

        _WriteJson(dm, output_filename, hierarchy_info)


# ----------------------------------------------------------------------
@app.command(
    "GenerateEvents",
    epilog=_HelpEpilog(),
    help=__doc__,
    no_args_is_help=True,
)
def GenerateEvents(
    plugin_name: _PLUGIN_NAMES_ENUM=typer.Argument(..., help="Name of the plugin used to extract information about work items."),  # type: ignore
    url: str=typer.Argument(..., help="Url associated with work items to extract."),
    username: str=typer.Argument(..., help="Username associated with work items to extract."),
    api_token_or_filename: str=typer.Argument(..., help="API token (or filename containing an API token) associated with the work items to extract."),
    output_filename: Path=typer.Argument(..., dir_okay=False, help="Output filename for extracted information."),
    root_work_item_ids: list[str]=typer.Option(None, "--id", help="Work item IDs associated with the root of one or more work item hierarchies."),
    verbose: bool=typer.Option(False, "--verbose", help="Write verbose information to the terminal."),
    debug: bool=typer.Option(False, "--debug", help="Write debug information to the terminal."),
) -> None:
    """Generates events for hierarchies associated with one or more work items."""

    with DoneManager.CreateCommandLine(
        output_flags=DoneManagerFlags.Create(verbose=verbose, debug=debug),
    ) as dm:
        plugin = _InitPlugin(dm, plugin_name, url, username, api_token_or_filename)
        if plugin is None:
            return

        root_work_item_ids = _InitRootWorkItems(dm, plugin, root_work_item_ids)
        if not root_work_item_ids:
            return

        hierarchy_info = GenerateHierarchiesImpl(dm, plugin, root_work_item_ids)
        if hierarchy_info is None:
            return

        results = GenerateEventsImpl(dm, plugin, hierarchy_info)

        _WriteJson(
            dm,
            output_filename,
            {
                "titles": results.titles,
                "events": { str(k): v for k, v in results.events.items() },
            },
        )


# ----------------------------------------------------------------------
# |
# |  Internal Functions
# |
# ----------------------------------------------------------------------
def _InitPlugin(
    dm: DoneManager,
    plugin_name, # : _PLUGIN_NAMES_ENUM,
    url: str,
    username: str,
    api_token_or_filename: str,
) -> Optional[Plugin]:
    plugin = _PLUGINS[plugin_name.value]

    if not url.endswith("/"):
        url += "/"

    potential_filename = Path(api_token_or_filename)
    if potential_filename.is_file():
        with potential_filename.open() as f:
            api_token = f.read().strip()
    else:
        api_token = api_token_or_filename

    # Initialize the plugin
    with dm.VerboseNested("Initializing '{}'...".format(plugin.name)) as verbose_dm:
        plugin.Initialize(verbose_dm, url, username, api_token)
        if dm.result != 0:
            return None

    return plugin


# ----------------------------------------------------------------------
def _InitRootWorkItems(
    dm: DoneManager,
    plugin: Plugin,
    root_work_item_ids: list[str],
) -> list[str]:
    if not root_work_item_ids:
        with dm.Nested(
            "Extracting root work items...",
            lambda: "{} found".format(inflect.no("work item", len(root_work_item_ids))),
        ):
            root_work_item_ids += plugin.GetRootWorkItems()

    return root_work_item_ids


# ----------------------------------------------------------------------
def _WriteJson(
    dm: DoneManager,
    output_filename: Path,
    content: Any,
) -> None:
    with dm.Nested("Writing '{}'...".format(output_filename)):
        output_filename.parent.mkdir(parents=True, exist_ok=True)

        with output_filename.open("w", encoding="UTF-8") as f:
            # ----------------------------------------------------------------------
            class Encoder(json.JSONEncoder):
                # ----------------------------------------------------------------------
                @singledispatchmethod
                def default(self, o) -> Any:
                    return o.__dict__

                @default.register
                def _(self, o: date) -> Any:
                    return o.isoformat()

                @default.register
                def _(self, o: datetime) -> Any:
                    return o.isoformat()

                @default.register
                def _(self, o: Enum) -> Any:
                    return str(o)

            # ----------------------------------------------------------------------

            json.dump(
                content,
                f,
                cls=Encoder,
            )


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    app()
