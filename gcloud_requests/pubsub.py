from .proxy import RequestsProxy


class PubSubRequestsProxy(RequestsProxy):
    """A PubSub-specific requests proxy.

    This proxy handles retries according to [1].

    [1]: https://cloud.google.com/pubsub/docs/reference/error-codes
    """

    SCOPE = (
        "https://www.googleapis.com/auth/pubsub",
        "https://www.googleapis.com/auth/cloud-platform",
    )

    # A mapping from PubSub error states that can be retried to the
    # maximum number of times each one should be retried.
    _MAX_RETRIES = {
        "RESOURCE_EXHAUSTED": 5,
        "INTERNAL": 3,
        "UNAVAILABLE": 5,
        "DEADLINE_EXCEEDED": 5,
    }

    def _max_retries_for_error(self, error):
        """Handles PubSub response errors according to their documentation.

        Parameters:
          error(dict)

        Returns:
          int or None: The max number of times this error should be
          retried or None if it shouldn't.

        See also:
          https://cloud.google.com/pubsub/docs/reference/error-codes
        """
        return self._MAX_RETRIES.get(error.get("status"))
