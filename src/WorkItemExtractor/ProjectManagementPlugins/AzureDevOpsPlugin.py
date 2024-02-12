# ----------------------------------------------------------------------
# |
# |  AzureDevOpsPlugin.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2023-05-22 16:23:56
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

import textwrap

from dataclasses import dataclass, field
from datetime import datetime
from typing import ClassVar, Generator, Optional, Type as PythonType
from urllib.parse import urljoin
from urllib3 import Retry

import requests

from requests.adapters import HTTPAdapter

from Common_Foundation.Streams.DoneManager import DoneManager
from Common_Foundation.Types import overridemethod

from WorkItemExtractor.Common.Plugin import Plugin as PluginBase
from WorkItemExtractor.Common.WorkItem import DaysWorkItem, HoursWorkItem, State, StoryPointsWorkItem, TeeShirtWorkItem, WorkItem, WorkItemChange


# ----------------------------------------------------------------------
@dataclass(frozen=True)
class Plugin(PluginBase):
    """Extracts work items from Azure DevOps instances."""

    # ----------------------------------------------------------------------
    # |  Public Types
    DefaultWorkItemTypeMapping: ClassVar[dict[str, Optional[PythonType[WorkItem]]]] = {
        "Bug": None,
        "Epic": TeeShirtWorkItem,
        "Feature": StoryPointsWorkItem,
        "Task": DaysWorkItem,
        "User Story": StoryPointsWorkItem,
    }

    # ----------------------------------------------------------------------
    # |  Public Data
    name: ClassVar[str]                                 = "AzureDevOps"

    epic_size_field_name: ClassVar[str]                 = "estimate"
    feature_size_field_name: ClassVar[str]              = "story_points"
    state_field_name: ClassVar[str]                     = "state"

    _session: requests.Session                          = field(init=False)

    # ----------------------------------------------------------------------
    # |  Public Methods
    @overridemethod
    def Initialize(
        self,
        verbose_dm: DoneManager,
        url: str,
        username: str,
        api_token: str,
        *,
        api_version: str="7.0",
    ) -> None:
        if not url.endswith("/"):
            url += "/"

        if not url.endswith("_apis/wit/"):
            url += "_apis/wit/"

        original_url = url; del url         # pylint: disable=multiple-statements
        original_self = self; del self      # pylint: disable=multiple-statements

        # ----------------------------------------------------------------------
        class CustomSession(requests.Session):
            # ----------------------------------------------------------------------
            def __init__(self, *args, **kwargs):
                super(CustomSession, self).__init__(*args, **kwargs)

                self.auth = (username, api_token)
                self.headers.update(
                    {
                        "Accept": "application/json",
                        "Connection": "keep-alive",
                    },
                )

                self.mount(
                    "https://",
                    HTTPAdapter(
                        max_retries=Retry(
                            total=7,
                            backoff_factor=0.5,
                            allowed_methods=None,
                            status_forcelist=[429, 500, 502, 504, 504, ],
                        ),
                    ),
                )

            # ----------------------------------------------------------------------
            def request(self, method, url, *args, **kwargs):
                if url.startswith("/"):
                    url = url[1:]

                url = urljoin(original_url, url)

                if "params" not in kwargs:
                    kwargs["params"] = {}

                if "api-version" not in kwargs["params"]:
                    kwargs["params"]["api-version"] = api_version

                return super(CustomSession, self).request(method, url, *args, **kwargs)

            # ----------------------------------------------------------------------
            def prepare_request(self, *args, **kwargs):
                result = super(CustomSession, self).prepare_request(*args, **kwargs)

                # Commas should remain commas
                result.url = result.url.replace("%2C", ",")  # type: ignore

                return result

        # ----------------------------------------------------------------------

        object.__setattr__(original_self, "_session", CustomSession())

    # ----------------------------------------------------------------------
    @overridemethod
    def GetRootWorkItems(
        self,
        *,
        work_item_type: Optional[str]="Epic",
        where_clauses: Optional[list[str]]=None,
    ) -> list[str]:
        where_clauses = where_clauses or []

        if work_item_type is not None:
            where_clauses.append("[System.WorkItemType] = '{}'".format(work_item_type))

        response = self._session.post(
            "wiql",
            json={
                "query": textwrap.dedent(
                    """\
                    SELECT
                        [System.Id]
                    FROM
                        WorkItems
                    {where}
                    ORDER BY
                        [Microsoft.VSTS.Common.Priority] asc,
                        [System.CreatedDate] desc
                    """,
                ).format(
                    where="" if not where_clauses else "WHERE {}".format(" AND ".join(where_clauses)),
                ),
            },
        )

        response.raise_for_status()
        response = response.json()

        results: list[str] = [str(work_item["id"]) for work_item in response["workItems"]]

        return results

    # ----------------------------------------------------------------------
    @overridemethod
    def EnumChildren(
        self,
        root_id: str,
    ) -> Generator[str, None, None]:
        response = self._session.get(
            "workitems/{}".format(root_id),
            params={
                "$expand": "Relations",
            },
        )

        response.raise_for_status()
        response = response.json()

        for relationship in response["relations"]:
            if relationship["attributes"]["name"] != "Child":
                continue

            yield relationship["url"].rsplit("/", 1)[1]

    # ----------------------------------------------------------------------
    @overridemethod
    def GetWorkItem(
        self,
        work_item_id: str,
        *,
        work_item_mapping: Optional[dict[str, Optional[PythonType[WorkItem]]]]=None,
    ) -> Optional[WorkItem]:
        if work_item_mapping is None:
            work_item_mapping = self.__class__.DefaultWorkItemTypeMapping

        query_fields: set[str] = set()

        for field_values in self.__class__._ITEM_ATTRIBUTE_TO_ADO_MAP.values():  # pylint: disable=protected-access
            if isinstance(field_values, str):
                field_values = [field_values, ]

            for field_value in field_values:
                query_fields.add(field_value)

        response = self._session.get(
            "workitems/{}".format(work_item_id),
            params={
                "fields": ",".join(query_fields),
            },
        )

        response.raise_for_status()
        response = response.json()

        fields = response["fields"]

        # ----------------------------------------------------------------------
        class DoesNotExist(object):
            pass

        # ----------------------------------------------------------------------

        work_item_type = work_item_mapping.get(fields["System.WorkItemType"], DoesNotExist())
        if isinstance(work_item_type, DoesNotExist):
            raise Exception(
                "The work item type '{}' (Id: {}) is not a recognized work item type.".format(
                    fields["System.WorkItemType"],
                    work_item_id,
                ),
            )

        if work_item_type is None:
            return None
        
        if work_item_type is TeeShirtWorkItem:
            effort = fields.get('Custom.EffortasTShirtSize', None)
            if effort is not None:
                effort = TeeShirtWorkItem.Size.FromString(effort)

        else:
            effort = None

            for potential_field in [
                "Microsoft.VSTS.Scheduling.Effort",
                "Microsoft.VSTS.Scheduling.StoryPoints",
            ]:
                potential_effort = fields.get(potential_field, None)
                if potential_effort is not None:
                    effort = float(potential_effort)
                    break

        return work_item_type(
            work_item_id,
            fields["System.Title"],
            self.__class__._DatetimeFromString(fields["System.CreatedDate"]),   # pylint: disable=protected-access
            self.__class__._ToState(fields["System.State"]),                    # pylint: disable=protected-access
            fields["System.WorkItemType"],
            effort,  # type: ignore
        )

    # ----------------------------------------------------------------------
    @overridemethod
    def GetWorkItemChanges(
        self,
        work_item: WorkItem,
        *,
        work_item_mapping: Optional[dict[str, Optional[PythonType[WorkItem]]]]=None,
    ) -> Generator[WorkItemChange, None, None]:
        if work_item_mapping is None:
            work_item_mapping = self.__class__.DefaultWorkItemTypeMapping

        current_type: PythonType[WorkItem] = type(work_item)

        # ----------------------------------------------------------------------
        def GetTypeAttributeName(
            ado_value: str,
        ) -> Optional[str]:
            for (matching_type, attribute_name), matching_ado_value_or_values in self.__class__._ITEM_ATTRIBUTE_TO_ADO_MAP.items():  # pylint: disable=protected-access

                if matching_type is not WorkItem and current_type != matching_type:
                    continue

                if isinstance(matching_ado_value_or_values, str):
                    if ado_value == matching_ado_value_or_values:
                        return attribute_name
                else:
                    if ado_value in matching_ado_value_or_values:
                        return attribute_name

            return None

        # ----------------------------------------------------------------------

        index = 0

        previously_revised_date: Optional[datetime] = None

        while True:
            response = self._session.get(
                "workitems/{}/updates".format(work_item.work_item_id),
                params={
                    "$skip": index,
                },
            )

            response.raise_for_status()
            response = response.json()

            count = response["count"]
            if count == 0:
                break

            index += count
            response = response["value"]

            for response_item in response:
                revised_date: Optional[datetime] = None

                for name, value in response_item.get("fields", {}).items():
                    attribute_name = GetTypeAttributeName(name)
                    if attribute_name is None:
                        continue

                    if revised_date is None:
                        try:
                            revised_date = self.__class__._DatetimeFromString(response_item["revisedDate"])  # pylint: disable=protected-access
                            previously_revised_date = revised_date
                        except ValueError:
                            # Sometimes, ADO will give us a bogus dates for revised date; attempt to find another version.
                            for potential_attribute_name in [
                                "System.RevisedDate",
                                "System.ChangedDate",
                            ]:
                                try:
                                    revised_date = self.__class__._DatetimeFromString(response_item["fields"][potential_attribute_name]["newValue"])  # pylint: disable=protected-access
                                    break
                                except ValueError:
                                    continue

                            if revised_date is None:
                                assert previously_revised_date is not None, "previously_revised_date is None"
                                revised_date = previously_revised_date

                    new_value = value.get("newValue", None)
                    old_value = value.get("oldValue", None)

                    if attribute_name in ["System.State", "state"]:
                        new_value = self.__class__._ToState(value["newValue"])              # pylint: disable=protected-access
                        old_value = self.__class__._ToState(value.get("oldValue", None))    # pylint: disable=protected-access
                    elif isinstance(work_item, TeeShirtWorkItem) and attribute_name == "estimate":
                        if new_value is not None:
                            new_value = TeeShirtWorkItem.Size.FromString(new_value)
                        if old_value is not None:
                            old_value = TeeShirtWorkItem.Size.FromString(old_value)

                    yield WorkItemChange(revised_date, attribute_name, new_value, old_value)

    # ----------------------------------------------------------------------
    # |
    # |  Private Types
    # |
    # ----------------------------------------------------------------------
    _ITEM_ATTRIBUTE_TO_ADO_MAP: ClassVar[
        dict[
            tuple[
                PythonType[WorkItem],       # Matching type
                str,                        # Attribute name for type
            ],
            str | list[str],                # ADO Type or Types
        ]
    ]                                       = {
        (WorkItem, "title"): "System.Title",
        (WorkItem, "dt"): "System.CreatedDate",
        (WorkItem, "state"): "System.State",
        (WorkItem, "type"): "System.WorkItemType",
        (StoryPointsWorkItem, "story_points"): ["Microsoft.VSTS.Scheduling.Effort", "Microsoft.VSTS.Scheduling.StoryPoints"],
        (TeeShirtWorkItem, "estimate"): "Custom.EffortasTShirtSize",
        (DaysWorkItem, "days"): "Microsoft.VSTS.Scheduling.Effort",
        (HoursWorkItem, "hours"): "Microsoft.VSTS.Scheduling.Effort",
    }

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    @staticmethod
    def _DatetimeFromString(
        value: str,
    ) -> datetime:
        result = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S{}%z".format(".%f" if "." in value else ""))
        if result.year == 9999:
            raise ValueError("Invalid date")

        return result

    # ----------------------------------------------------------------------
    _state_map: ClassVar[dict[str, State]]  = {
        "New": State.New,
        "Active": State.Active,
        "Closed": State.Closed,
        "Removed": State.Removed,
        "Resolved": State.Closed,
    }

    @classmethod
    def _ToState(
        cls,
        value: Optional[str],
    ) -> Optional[State]:
        if value is None:
            return None

        state = cls._state_map.get(value, None)
        if state is not None:
            return state

        assert False, state
