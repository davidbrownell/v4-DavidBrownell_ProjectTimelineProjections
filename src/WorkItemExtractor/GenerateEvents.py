# ----------------------------------------------------------------------
# |
# |  GenerateEvents.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2023-10-04 12:44:23
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2023
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Contains types and functionality to generate events"""

from dataclasses import dataclass, field
from datetime import date, datetime
from functools import cached_property
from typing import Optional

from Common_Foundation.Streams.DoneManager import DoneManager

from Common.Plugin import Plugin                                            # type: ignore; pylint: disable=import-error
from Common.WorkItem import State                                           # type: ignore; pylint: disable=import-error
from GenerateHierarchies import HierarchyItem, HierarchyResult              # type: ignore; pylint: disable=import-error


# ----------------------------------------------------------------------
# |
# |  Public Types
# |
# ----------------------------------------------------------------------
@dataclass(frozen=True)
class EventChange(object):
    work_item_id: str
    epic_id: str
    size: Optional[int]
    state: State


# ----------------------------------------------------------------------
class EventInfo(object):
    # ----------------------------------------------------------------------
    def __init__(self):
        self.pending = 0
        self.active = 0
        self.completed = 0

    # ----------------------------------------------------------------------`
    @staticmethod
    def StateToAttributeName(
        state: Optional[State],
    ) -> str:
        # We can't use direct comparison here as State imported here is considered to
        # be different from the State enum used when generating the work item information.
        # More info at https://stackoverflow.com/questions/26589805/python-enums-across-modules.

        if state is None:
            return "pending"
        if state.value in [State.New.value, State.Estimated.value, State.Pending.value]:
            return "pending"
        if state.value == State.Active.value:
            return "active"
        if state.value == State.Closed.value:
            return "completed"
        if state.value == State.Removed.value:
            raise Exception("The removed state does not correspond to an EventInfo attribute value.")

        assert False, state  # pragma: no cover


# ----------------------------------------------------------------------
@dataclass(frozen=True)
class Event(object):
    estimated_epic: EventInfo               # Count
    unestimated_epic: EventInfo             # Count

    estimated_feature: EventInfo            # Size
    unestimated_feature: EventInfo          # Count

    team: Optional[str]

    changes: list[EventChange]


# ----------------------------------------------------------------------
@dataclass(frozen=True)
class GenerateEventsResult(object):
    titles: dict[str, str]
    events: dict[date, Event]


# ----------------------------------------------------------------------
# |
# |  Public Functions
# |
# ----------------------------------------------------------------------
def GenerateEvents(
    dm: DoneManager,
    plugin: Plugin,
    hierarchy_results: list[HierarchyResult],
) -> GenerateEventsResult:
    titles: dict[str, str] = {}
    resolved_work_item_data: dict[
        date,
        dict[
            str,                    # work_item_id
            _WorkItemData,
        ],
    ] = {}

    with dm.Nested("Organizing events..."):
        # Extract titles and group events by date

        # ----------------------------------------------------------------------
        def ProcessHierarchyItem(
            epic_id: str,
            hierarchy_item: HierarchyItem,
        ) -> None:
            work_item_id = hierarchy_item.work_item.work_item_id

            if work_item_id not in titles:
                titles[work_item_id] = hierarchy_item.work_item.title

            for change in hierarchy_item.changes:
                work_item_data: Optional[_WorkItemData] = None

                if change.field == plugin.feature_size_field_name:
                    work_item_data = _WorkItemData(
                        change.dt,
                        epic_id,
                        work_item_id if work_item_id != epic_id else None,
                        change.new_value,
                        None,
                    )

                elif change.field == plugin.state_field_name:
                    work_item_data = _WorkItemData(
                        change.dt,
                        epic_id,
                        work_item_id if work_item_id != epic_id else None,
                        None,
                        change.new_value,
                    )

                if work_item_data is None:
                    continue

                this_day = resolved_work_item_data.setdefault(change.dt.date(), {})

                if work_item_id not in this_day:
                    this_day[work_item_id] = work_item_data
                else:
                    this_day[work_item_id].Merge(work_item_data)

        # ----------------------------------------------------------------------

        for hierarchy_result in hierarchy_results:
            epic_id = hierarchy_result.root.work_item.work_item_id

            ProcessHierarchyItem(epic_id, hierarchy_result.root)

            for child in hierarchy_result.children:
                ProcessHierarchyItem(epic_id, child)

    all_event_results: dict[date, Event] = {}

    with dm.Nested("Normalizing events..."):
        previous_work_item_data: dict[str, _WorkItemData] = {}

        sorted_dates = list(resolved_work_item_data.keys())
        sorted_dates.sort()

        for sorted_date in sorted_dates:
            work_item_data_items = resolved_work_item_data[sorted_date]
            changes: list[EventChange] = []

            for work_item_id, work_item_data in work_item_data_items.items():
                changes.append(
                    EventChange(
                        work_item_id,
                        work_item_data.epic_id,
                        work_item_data.size,
                        work_item_data.state or State.New,
                    ),
                )

                if work_item_data.state is not None and work_item_data.state.value == State.Removed.value:
                    previous_work_item_data.pop(work_item_id, None)
                    continue

                if work_item_id not in previous_work_item_data:
                    previous_work_item_data[work_item_id] = work_item_data
                else:
                    previous_work_item_data[work_item_id].Merge(work_item_data)

            # Sort changes by feature then epic & numerical order
            changes.sort(key=lambda change: (change.work_item_id == change.epic_id, change.work_item_id))

            estimated_epic = EventInfo()
            estimated_feature = EventInfo()

            unestimated_epic = EventInfo()
            unestimated_feature = EventInfo()

            for work_item_data in previous_work_item_data.values():
                if work_item_data.feature_id is None:
                    estimated_info = estimated_epic
                    unestimated_info = unestimated_epic
                else:
                    estimated_info = estimated_feature
                    unestimated_info = unestimated_feature

                attribute_name = EventInfo.StateToAttributeName(work_item_data.state)

                if work_item_data.size is None:
                    setattr(unestimated_info, attribute_name, getattr(unestimated_info, attribute_name) + 1)
                else:
                    setattr(estimated_info, attribute_name, getattr(estimated_info, attribute_name) + work_item_data.size)

            all_event_results[sorted_date] = Event(
                estimated_epic,
                unestimated_epic,
                estimated_feature,
                unestimated_feature,
                None, # TODO: Team
                changes,
            )

    return GenerateEventsResult(titles, all_event_results)


# ----------------------------------------------------------------------
# |
# |  Private Types
# |
# ----------------------------------------------------------------------
@dataclass(frozen=True)
class _WorkItemData(object):
    """Information about a change to a work item"""

    dt: datetime

    epic_id: str
    feature_id: Optional[str]

    size: Optional[int]
    state: Optional[State]

    # ----------------------------------------------------------------------
    @cached_property
    def work_item_id(self) -> str:
        return self.feature_id or self.epic_id

    # ----------------------------------------------------------------------
    def Merge(
        self,
        other: "_WorkItemData",
    ) -> None:
        if other.size is not None and (self.size is None or other.dt >= self.dt):
            object.__setattr__(self, "size", other.size)

        if other.state is not None and (self.state is None or other.dt >= self.dt):
            object.__setattr__(self, "state", other.state)
