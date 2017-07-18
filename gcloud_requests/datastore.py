from threading import local

from .proxy import RequestsProxy

_state = local()


def enter_transaction():
    """This method should be called by any client code using the
    Datastore proxy when entering a transaction.
    """
    _state.transactions = get_transactions() + 1


def exit_transaction():
    """This method should be called by any client code using the
    Datastore proxy when exiting a transaction.
    """
    _state.transactions = max(get_transactions() - 1, 0)


def get_transactions():
    return getattr(_state, "transactions", 0)


class DatastoreRequestsProxy(RequestsProxy):
    """A Datastore-specific RequestsProxy.

    This proxy handles retries according to [1].

    [1]: https://cloud.google.com/datastore/docs/concepts/errors.
    """

    SCOPE = ("https://www.googleapis.com/auth/datastore",)

    # A mapping from Datastore error states that can be retried to the
    # maximum number of times each one should be retried.
    _MAX_RETRIES = {
        "ABORTED": 5,
        "INTERNAL": 1,
        "UNKNOWN": 1,
        "UNAVAILABLE": 5,
        "DEADLINE_EXCEEDED": 5,
    }

    def _convert_response_to_error(self, response):
        content_type = response.headers.get("content-type", "")
        if response.status_code == 502 and content_type.startswith("text/html"):
            # The Datastore error handling docs don't mention anything
            # about how 502s should be handled so we just handle them
            # the same way we do 503s.
            return {"status": "UNAVAILABLE"}

        return super(DatastoreRequestsProxy, self)._convert_response_to_error(response)

    def _max_retries_for_error(self, error):
        """Handles Datastore response errors according to their documentation.

        Parameters:
          error(dict)

        Returns:
          int or None: The max number of times this error should be
          retried or None if it shouldn't.

        See also:
          https://cloud.google.com/datastore/docs/concepts/errors
        """
        status = error.get("status")
        if status == "ABORTED" and get_transactions() > 0:
            # Avoids retrying Conflicts when inside a transaction.
            return None
        return self._MAX_RETRIES.get(status)
