from abc import ABC, abstractmethod
from typing import Any

from .types import DeliveryResult


class EmailProviderBase(ABC):
    name: str

    @abstractmethod
    def is_configured(self) -> bool: ...

    @abstractmethod
    def send(
        self,
        *,
        subject: str,
        recipients: list[dict[str, str]],
        html_body: str,
        text_body: str | None = None,
    ) -> DeliveryResult: ...


class PushProviderBase(ABC):
    name: str

    @abstractmethod
    def is_configured(self) -> bool: ...

    @abstractmethod
    def send(self, payload: dict[str, Any]) -> DeliveryResult: ...


class SmsProviderBase(ABC):
    name: str

    @abstractmethod
    def is_configured(self) -> bool: ...

    @abstractmethod
    def send(self, *, to_number: str, body: str) -> DeliveryResult: ...
