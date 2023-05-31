# ----------------------------------------------------------------------
# |
# |  WorkItem.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2023-05-23 11:47:18
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2023
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Contains the WorkItem and WorkItemChange objects"""

from dataclasses import dataclass
from datetime import date, datetime
from enum import auto, Enum
from functools import total_ordering
from typing import Any, Callable, Generator, Iterable, Optional, Type as PythonType, Union


# ----------------------------------------------------------------------
# |
# |  Public Types
# |
# ----------------------------------------------------------------------
@dataclass(frozen=True)
class WorkItem(object):
    """A work item within a project management tool"""

    # ----------------------------------------------------------------------
    work_item_id: str
    title: str

    dt: datetime
    status: str

    type: str

    # ----------------------------------------------------------------------
    def Clone(self, **kwargs) -> "WorkItem":
        return self.__class__(
            **{
                **self.__dict__,
                **kwargs,
            },
        )


# ----------------------------------------------------------------------
@dataclass(frozen=True)
class StoryPointsWorkItem(WorkItem):
    """WorkItem that tracks estimates in terms of story points."""

    # ----------------------------------------------------------------------
    story_points: Optional[int]

    # ----------------------------------------------------------------------
    def __post_init__(self):
        if self.story_points is not None and self.story_points <= 0:
            raise ValueError("Invalid story points.")


# ----------------------------------------------------------------------
@dataclass(frozen=True)
class TeeShirtWorkItem(WorkItem):
    """WorkItem that tracks estimates in terms of tee-shirt sizes."""

    # ----------------------------------------------------------------------
    # |  Public Data
    class Size(Enum):
        Small                               = auto()
        Medium                              = auto()
        Large                               = auto()
        ExtraLarge                          = auto()
        DoubleExtraLarge                    = auto()

        # ----------------------------------------------------------------------
        @classmethod
        def FromString(
            cls,
            value: str,
        ) -> "TeeShirtWorkItem.Size":
            simple_map: dict[str, TeeShirtWorkItem.Size] = {
                "S": TeeShirtWorkItem.Size.Small,
                "M": TeeShirtWorkItem.Size.Medium,
                "L": TeeShirtWorkItem.Size.Large,
                "XL": TeeShirtWorkItem.Size.ExtraLarge,
                "XXL": TeeShirtWorkItem.Size.DoubleExtraLarge,
            }

            result = simple_map.get(value, None)
            if result is not None:
                return result

            return cls[value]

    # ----------------------------------------------------------------------
    # |  Public Data
    estimate: Optional[Size]


# ----------------------------------------------------------------------
@dataclass(frozen=True)
class DaysWorkItem(WorkItem):
    """WorkItem that tracks estimates in terms of days."""

    # ----------------------------------------------------------------------
    days: Optional[float]

    # ----------------------------------------------------------------------
    def __post_init__(self):
        if self.days is not None and self.days < 1:
            raise ValueError("Invalid days.")


# ----------------------------------------------------------------------
@dataclass(frozen=True)
class HoursWorkItem(WorkItem):
    """WorkItem that tracks estimates in terms of hours."""

    # ----------------------------------------------------------------------
    hours: Optional[float]

    # ----------------------------------------------------------------------
    def __post_init__(self):
        if self.hours is not None and self.hours < 1:
            raise ValueError("Invalid hours.")


# ----------------------------------------------------------------------
@dataclass(frozen=True)
@total_ordering
class WorkItemChange(object):
    """A change to a WorkItem"""

    # ----------------------------------------------------------------------
    dt: datetime
    field: str
    new_value: Any
    old_value: Any

    # ----------------------------------------------------------------------
    def __lt__(
        self,
        other: "WorkItemChange",
    ) -> bool:
        return self.dt < other.dt


# ----------------------------------------------------------------------
# |
# |  Public Functions
# |
# ----------------------------------------------------------------------
def GenerateDailyWorkItemHistory(
    work_item_or_id: Union[str, WorkItem],
    work_item_changes: Iterable[WorkItemChange],
    type_to_class_func: Callable[[str], PythonType[WorkItem]],
    *,
    suppress_unsupported_field_errors: bool=False,
    title_field_name: Optional[str]="title",
    datetime_field_name: Optional[str]="datetime",
    status_field_name: Optional[str]="status",
    type_field_name: Optional[str]="type",
    story_points_field_name: Optional[str]="story_points",
    tee_shirt_field_name: Optional[str]="tee_shirt_estimate",
    days_field_name: Optional[str]="days",
    hours_field_name: Optional[str]="hours",
) -> Generator[WorkItem, None, None]:
    """Generates the WorkItem as it existed on different days."""

    changes = list(work_item_changes)
    changes.sort()

    assert changes

    # ----------------------------------------------------------------------
    def ChangeTitle(
        work_item: WorkItem,
        change: WorkItemChange,
    ) -> WorkItem:
        object.__setattr__(work_item, "title", change.new_value)
        return work_item

    # ----------------------------------------------------------------------
    def ChangeDateTime(
        work_item: WorkItem,
        change: WorkItemChange,
    ) -> WorkItem:
        object.__setattr__(work_item, "dt", change.new_value)
        return work_item

    # ----------------------------------------------------------------------
    def ChangeStatus(
        work_item: WorkItem,
        change: WorkItemChange,
    ) -> WorkItem:
        object.__setattr__(work_item, "status", change.new_value)
        return work_item

    # ----------------------------------------------------------------------
    def ChangeType(
        work_item: WorkItem,
        change: WorkItemChange,
    ) -> WorkItem:
        new_type = type_to_class_func(change.new_value)

        if type(work_item) != new_type:
            work_item = new_type(
                work_item.work_item_id,
                work_item.title,
                work_item.dt,
                work_item.status,
                work_item.type,
            )

        return work_item

    # ----------------------------------------------------------------------
    def ChangeStoryPoints(
        work_item: WorkItem,
        change: WorkItemChange,
    ) -> WorkItem:
        if not isinstance(work_item, StoryPointsWorkItem):
            raise Exception(
                "The work item is a '{}' type but 'StoryPointsWorkItem' was expected.".format(
                    type(work_item).__name__,
                ),
            )

        return work_item.Clone(story_points=change.new_value)

    # ----------------------------------------------------------------------
    def ChangeTeeShirt(
        work_item: WorkItem,
        change: WorkItemChange,
    ) -> WorkItem:
        if not isinstance(work_item, TeeShirtWorkItem):
            raise Exception(
                "The work item is a '{}' type but 'TeeShirtWorkItem' was expected.".format(
                    type(work_item).__name__,
                ),
            )

        return work_item.Clone(estimate=change.new_value)

    # ----------------------------------------------------------------------
    def ChangeDays(
        work_item: WorkItem,
        change: WorkItemChange,
    ) -> WorkItem:
        if not isinstance(work_item, DaysWorkItem):
            raise Exception(
                "The work item is a '{}' type but 'DaysWorkItem' was expected.".format(
                    type(work_item).__name__,
                ),
            )

        return work_item.Clone(days=change.new_value)

    # ----------------------------------------------------------------------
    def ChangeHours(
        work_item: WorkItem,
        change: WorkItemChange,
    ) -> WorkItem:
        if not isinstance(work_item, HoursWorkItem):
            raise Exception(
                "The work item is a '{}' type but 'HoursWorkItem' was expected.".format(
                    type(work_item).__name__,
                ),
            )

        return work_item.Clone(hours=change.new_value)

    # ----------------------------------------------------------------------

    change_map: dict[str, Callable[[WorkItem, WorkItemChange], WorkItem]] = {}

    if title_field_name is not None:
        change_map[title_field_name] = ChangeTitle
    if datetime_field_name is not None:
        change_map[datetime_field_name] = ChangeDateTime
    if status_field_name is not None:
        change_map[status_field_name] = ChangeStatus
    if type_field_name is not None:
        change_map[type_field_name] = ChangeType
    if story_points_field_name is not None:
        change_map[story_points_field_name] = ChangeStoryPoints
    if tee_shirt_field_name is not None:
        change_map[tee_shirt_field_name] = ChangeTeeShirt
    if days_field_name is not None:
        change_map[days_field_name] = ChangeDays
    if hours_field_name is not None:
        change_map[hours_field_name] = ChangeHours

    # ----------------------------------------------------------------------
    def DateToDateTime(
        d: date,
    ) -> datetime:
        return datetime(d.year, d.month, d.day)

    # ----------------------------------------------------------------------

    if isinstance(work_item_or_id, str):
        work_item = WorkItem(
            work_item_or_id,
            "",
            DateToDateTime(changes[0].dt.date()),
            "",
            "",
        )
    elif isinstance(work_item_or_id, WorkItem):
        work_item = work_item_or_id
    else:
        assert False, work_item_or_id  # pragma: no cover

    current_day: date = changes[0].dt.date()

    for change in changes:
        change_day = change.dt.date()

        if change_day != current_day:
            yield work_item

            current_day = change_day
            work_item = work_item.Clone(dt=DateToDateTime(current_day))

        func = change_map.get(change.field, None)
        if func is None:
            if suppress_unsupported_field_errors:
                continue

            raise Exception("'{}' is not a supported change field.".format(change.field))

        func(work_item, change)

    yield work_item
