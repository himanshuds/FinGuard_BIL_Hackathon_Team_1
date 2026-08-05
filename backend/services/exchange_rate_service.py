from __future__ import annotations

import time
from dataclasses import dataclass
from threading import Lock
from typing import Optional

import requests
from cachetools import TTLCache


# =====================================================
# Models
# =====================================================

@dataclass(frozen=True)
class ExchangeRate:
    source_currency: str
    target_currency: str
    rate: float


# =====================================================
# Exceptions
# =====================================================

class ExchangeRateError(Exception):
    pass


class InvalidCurrencyError(ExchangeRateError):
    pass


class ExchangeRateApiError(ExchangeRateError):
    pass


# =====================================================
# Service
# =====================================================

class ExchangeRateService:

    def __init__(
        self,
        ttl_seconds: int = 3600,
        cache_size: int = 1000,
        timeout_seconds: int = 10,
        max_retries: int = 3,
    ):
        self._session = requests.Session()
        self._cache = TTLCache(
            maxsize=cache_size,
            ttl=ttl_seconds,
        )

        # Never expires
        # Used if API becomes unavailable
        self._stale_cache: dict[
            tuple[str, str],
            ExchangeRate,
        ] = {}

        self._timeout_seconds = timeout_seconds
        self._max_retries = max_retries

        self._lock = Lock()

    # -------------------------------------------------
    # Public method
    # -------------------------------------------------

    def close(self):
        self._session.close()

    def get_rate(
        self,
        source_currency: str,
        target_currency: str,
    ) -> ExchangeRate:

        source_currency = source_currency.upper()
        target_currency = target_currency.upper()

        if source_currency == target_currency:
            return ExchangeRate(
                source_currency,
                target_currency,
                1.0,
            )

        key = (
            source_currency,
            target_currency,
        )

        # ---------------------------------------
        # Cache hit
        # ---------------------------------------

        with self._lock:
            cached = self._cache.get(key)

        if cached:
            return cached

        # ---------------------------------------
        # Retry loop
        # ---------------------------------------

        last_exception: Optional[Exception] = None

        for attempt in range(
            self._max_retries
        ):
            try:

                rate = self._call_api(
                    source_currency,
                    target_currency,
                )

                result = ExchangeRate(
                    source_currency=source_currency,
                    target_currency=target_currency,
                    rate=rate,
                )

                with self._lock:
                    self._cache[key] = result
                    self._stale_cache[key] = result

                return result

            except InvalidCurrencyError:
                raise

            except (
                requests.Timeout,
                requests.ConnectionError,
                requests.HTTPError,
            ) as ex:

                last_exception = ex

                # Exponential backoff
                if attempt < self._max_retries - 1:
                    time.sleep(2**attempt)

        # ---------------------------------------
        # Fallback to stale cache
        # ---------------------------------------

        stale = self._stale_cache.get(key)

        if stale:
            return stale

        raise ExchangeRateApiError(
            f"Unable to obtain exchange rate "
            f"{source_currency}->{target_currency}"
        ) from last_exception

    # -------------------------------------------------
    # Private API method
    # -------------------------------------------------

    def _call_api(
        self,
        source_currency: str,
        target_currency: str,
    ) -> float:

        url = (
            "https://api.frankfurter.dev/v1/latest"
            f"?base={source_currency}"
            f"&symbols={target_currency}"
        )

        response = self._session.get(
            url,
            timeout=self._timeout_seconds,
        )

        # Permanent error
        if 400 <= response.status_code < 500:
            raise InvalidCurrencyError(
                f"Invalid currency pair: "
                f"{source_currency}/{target_currency}"
            )

        response.raise_for_status()

        payload = response.json()

        try:
            return float(
                payload["rates"][
                    target_currency
                ]
            )
        except (
            KeyError,
            ValueError,
            TypeError,
        ) as ex:
            raise ExchangeRateApiError(
                "Unexpected API response"
            ) from ex
