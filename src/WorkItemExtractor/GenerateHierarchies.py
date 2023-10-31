# ----------------------------------------------------------------------
# |
# |  GenerateHierarchies.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2023-10-04 12:31:04
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2023
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Contains the GenerateHierarchies function"""

import textwrap
import traceback

from dataclasses import dataclass
from typing import Callable, cast, Optional

from Common_Foundation.Streams.DoneManager import DoneManager
from Common_Foundation import TextwrapEx

from Common_FoundationEx import ExecuteTasks

from Common.Plugin import Plugin                        # pylint: disable=import-error
from Common.WorkItem import WorkItem, WorkItemChange    # pylint: disable=import-error


# ----------------------------------------------------------------------
# |
# |  Public Types
# |
# ----------------------------------------------------------------------
@dataclass(frozen=True)
class HierarchyItem(object):
    work_item: WorkItem
    changes: list[WorkItemChange]


# ----------------------------------------------------------------------
@dataclass(frozen=True)
class HierarchyResult(object):
    root: HierarchyItem
    children: list[HierarchyItem]


# ----------------------------------------------------------------------
# |
# |  Public Functions
# |
# ----------------------------------------------------------------------
def GenerateHierarchies(
    dm: DoneManager,
    plugin: Plugin,
    root_work_item_ids: list[str],
) -> Optional[list[HierarchyResult]]:
    # ----------------------------------------------------------------------
    def ExecuteTask(
        context: str,
        on_simple_status_func: Callable[[str], None],
    ) -> tuple[Optional[int], ExecuteTasks.TransformTypes.FuncType[HierarchyResult]]:
        root_work_item_id = context
        del context

        on_simple_status_func("Extracting work item hierarchy...")
        hierarchy_work_item_ids: list[str] = list(plugin.EnumChildren(root_work_item_id))

        # ----------------------------------------------------------------------
        def Impl(
            status: ExecuteTasks.Status,
        ) -> HierarchyResult:
            status.OnProgress(0, "Extracting work item info...")
            root_work_item = plugin.GetWorkItem(root_work_item_id)

            status.OnProgress(0, "Extracting work item changes...")
            root_work_item_changes = list(plugin.GetWorkItemChanges(root_work_item))

            hierarchy_results: list[HierarchyItem] = []

            for hierarchy_work_item_id in hierarchy_work_item_ids:
                index = 1 + len(hierarchy_results)

                status.OnProgress(index, "Extracting '{}'...".format(hierarchy_work_item_id))
                work_item = plugin.GetWorkItem(hierarchy_work_item_id)

                status.OnProgress(index, "Extracting '{}' changes...".format(hierarchy_work_item_id))
                work_item_changes = list(plugin.GetWorkItemChanges(work_item))

                hierarchy_results.append(HierarchyItem(work_item, work_item_changes))

            return HierarchyResult(
                HierarchyItem(root_work_item, root_work_item_changes),
                hierarchy_results,
            )

        # ----------------------------------------------------------------------

        return 1 + len(hierarchy_work_item_ids), Impl

    # ----------------------------------------------------------------------

    results = cast(
        list[HierarchyResult | Exception | None],
        ExecuteTasks.Transform(
            dm,
            "Extracting...",
            [
                ExecuteTasks.TaskData(root_work_item_id, root_work_item_id)
                for root_work_item_id in root_work_item_ids
            ],
            ExecuteTask,
            return_exceptions=True,
        ),
    )

    for root_work_item_id, result in zip(root_work_item_ids, results):
        assert result is not None

        if isinstance(result, Exception):
            if dm.is_debug:
                error = "\n".join(traceback.format_exception(result))
            else:
                error = str(result)

            dm.WriteError(
                textwrap.dedent(
                    """\

                    Error extracting information for '{}':
                        {}
                    """,
                ).format(
                    root_work_item_id,
                    TextwrapEx.Indent(error.rstrip(), 4, skip_first_line=True),
                ),
            )

            continue

        assert isinstance(result, HierarchyResult), result

    if dm.result != 0:
        return None

    return cast(list[HierarchyResult], results)
