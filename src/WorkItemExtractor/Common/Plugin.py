# ----------------------------------------------------------------------
# |
# |  Plugin.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2023-05-22 16:14:41
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2023
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Contains the Plugin object"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generator, Optional

from Common_Foundation.Streams.DoneManager import DoneManager

from .WorkItem import WorkItem, WorkItemChange


# ----------------------------------------------------------------------
@dataclass(frozen=True)
class Plugin(ABC):
    """Abstract base class for all project management plugins"""

    # ----------------------------------------------------------------------
    name: str

    epic_size_field_name: str
    feature_size_field_name: str
    state_field_name: str

    # ----------------------------------------------------------------------
    @abstractmethod
    def Initialize(
        self,
        verbose_dm: DoneManager,
        url: str,
        username: str,
        api_token: str,
        **kwargs,
    ) -> None:
        """Initializes the plugin for use."""
        raise Exception("Abstract method")  # pragma: no cover

    # ----------------------------------------------------------------------
    @abstractmethod
    def GetRootWorkItems(self, **kwargs) -> list[str]:
        """Returns a list of items that serve as the root of hierarchies that should be queried for changes over time."""
        raise Exception("Abstract method")  # pragma: no cover

    # ----------------------------------------------------------------------
    @abstractmethod
    def EnumChildren(
        self,
        root_id: str,
        **kwargs,
    ) -> Generator[str, None, None]:
        """Enumerate the children within the hierarchy of the provided root work item."""
        raise Exception("Abstract method")  # pragma: no cover

    # ----------------------------------------------------------------------
    @abstractmethod
    def GetWorkItem(
        self,
        work_item_id: str,
        **kwargs,
    ) -> Optional[WorkItem]:
        """Returns info about the work item and its history"""
        raise Exception("Abstract method")  # pragma: no cover

    # ----------------------------------------------------------------------
    @abstractmethod
    def GetWorkItemChanges(
        self,
        work_item: WorkItem,
        **kwargs,
    ) -> Generator[WorkItemChange, None, None]:
        """Generates changes to the work item, ordered from most-recent to least-recent"""
        raise Exception("Abstract method")  # pragma: no cover
