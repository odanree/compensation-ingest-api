"""Ingest handler registry — the plugin extension point for apps.surveys.

apps.surveys is a domain-agnostic ingest pipeline (idempotency via fingerprint,
Celery fan-out, state-machine on QuoteSubmission). Each domain plugs in its
own normalizer via `@register_ingest_handler(key)` in apps.<domain>.handlers,
and QuoteSource.handler_key selects which handler to invoke per submission.

Handler contract: a callable taking a QuoteSubmission and returning None.
The handler is responsible for validating / normalizing the raw record and
persisting whatever domain-specific rows it produces. Errors propagate — the
caller (process_submission Celery task) catches them and updates status to
FAILED with the exception message.

Handlers register at Django AppConfig.ready() time so autoreload / test
teardown / worker startup all see the same registry. Import order does not
matter — a handler_key referenced by a QuoteSource before its handler app
is loaded will raise UnknownIngestHandler at dispatch time.
"""
from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from apps.surveys.models import QuoteSubmission

Handler = Callable[["QuoteSubmission"], None]

_HANDLERS: dict[str, Handler] = {}


class UnknownIngestHandler(LookupError):
    """Raised when a QuoteSource.handler_key has no registered handler."""


def register_ingest_handler(key: str) -> Callable[[Handler], Handler]:
    """Decorator: register a handler function under `key`.

    Usage:
        @register_ingest_handler("solar_quote")
        def solar_quote_handler(submission):
            ...
    """
    def decorator(func: Handler) -> Handler:
        if key in _HANDLERS and _HANDLERS[key] is not func:
            raise ValueError(
                f"Ingest handler '{key}' already registered by "
                f"{_HANDLERS[key].__module__}.{_HANDLERS[key].__qualname__}; "
                f"attempted re-register by {func.__module__}.{func.__qualname__}"
            )
        _HANDLERS[key] = func
        return func
    return decorator


def get_handler(key: str) -> Handler:
    """Look up a registered handler. Raises UnknownIngestHandler if missing."""
    try:
        return _HANDLERS[key]
    except KeyError:
        raise UnknownIngestHandler(
            f"No ingest handler registered for key '{key}'. "
            f"Registered: {sorted(_HANDLERS)}"
        )


def registered_keys() -> list[str]:
    """List all currently-registered handler keys (for admin / diagnostics)."""
    return sorted(_HANDLERS)
