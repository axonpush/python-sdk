from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.admin_events_dto import AdminEventsDto
    from ..models.admin_mrr_dto import AdminMrrDto
    from ..models.admin_totals_dto import AdminTotalsDto
    from ..models.count_by_key_dto import CountByKeyDto


T = TypeVar("T", bound="AdminOverviewDto")


@_attrs_define
class AdminOverviewDto:
    """
    Attributes:
        totals (AdminTotalsDto):
        events (AdminEventsDto):
        plan_distribution (list[CountByKeyDto]): Org count grouped by plan
        subscription_status_distribution (list[CountByKeyDto]): Org count grouped by subscription status
        mrr (AdminMrrDto):
    """

    totals: AdminTotalsDto
    events: AdminEventsDto
    plan_distribution: list[CountByKeyDto]
    subscription_status_distribution: list[CountByKeyDto]
    mrr: AdminMrrDto
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.admin_events_dto import AdminEventsDto
        from ..models.admin_mrr_dto import AdminMrrDto
        from ..models.admin_totals_dto import AdminTotalsDto
        from ..models.count_by_key_dto import CountByKeyDto

        totals = self.totals.to_dict()

        events = self.events.to_dict()

        plan_distribution = []
        for plan_distribution_item_data in self.plan_distribution:
            plan_distribution_item = plan_distribution_item_data.to_dict()
            plan_distribution.append(plan_distribution_item)

        subscription_status_distribution = []
        for subscription_status_distribution_item_data in self.subscription_status_distribution:
            subscription_status_distribution_item = (
                subscription_status_distribution_item_data.to_dict()
            )
            subscription_status_distribution.append(subscription_status_distribution_item)

        mrr = self.mrr.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "totals": totals,
                "events": events,
                "planDistribution": plan_distribution,
                "subscriptionStatusDistribution": subscription_status_distribution,
                "mrr": mrr,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.admin_events_dto import AdminEventsDto
        from ..models.admin_mrr_dto import AdminMrrDto
        from ..models.admin_totals_dto import AdminTotalsDto
        from ..models.count_by_key_dto import CountByKeyDto

        d = dict(src_dict)
        totals = AdminTotalsDto.from_dict(d.pop("totals"))

        events = AdminEventsDto.from_dict(d.pop("events"))

        plan_distribution = []
        _plan_distribution = d.pop("planDistribution")
        for plan_distribution_item_data in _plan_distribution:
            plan_distribution_item = CountByKeyDto.from_dict(plan_distribution_item_data)

            plan_distribution.append(plan_distribution_item)

        subscription_status_distribution = []
        _subscription_status_distribution = d.pop("subscriptionStatusDistribution")
        for subscription_status_distribution_item_data in _subscription_status_distribution:
            subscription_status_distribution_item = CountByKeyDto.from_dict(
                subscription_status_distribution_item_data
            )

            subscription_status_distribution.append(subscription_status_distribution_item)

        mrr = AdminMrrDto.from_dict(d.pop("mrr"))

        admin_overview_dto = cls(
            totals=totals,
            events=events,
            plan_distribution=plan_distribution,
            subscription_status_distribution=subscription_status_distribution,
            mrr=mrr,
        )

        admin_overview_dto.additional_properties = d
        return admin_overview_dto

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
