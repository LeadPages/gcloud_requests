from .proxy import RequestsProxy


class CloudStorageRequestsProxy(RequestsProxy):
    """A GCS-specific RequestsProxy.

    This proxy handles retries according to [1].

    [1]: https://cloud.google.com/storage/docs/json_api/v1/status-codes
    """

    SCOPE = (
        "https://www.googleapis.com/auth/devstorage.full_control",
        "https://www.googleapis.com/auth/devstorage.read_only",
        "https://www.googleapis.com/auth/devstorage.read_write",
    )

    #: Determines how connection and read timeouts should be handled
    #: by this proxy.
    TIMEOUT_CONFIG = (3.05, 30)

    # A mapping from GCS error codes that can be retried to the
    # maximum number of times each one should be retried.
    _MAX_RETRIES = {
        429: 10,
        500: 5,
        502: 5,
        503: 5,
    }

    def _convert_response_to_error(self, response):
        # Sometimes GCS 503s with no content so we handle that case here.
        if response.status_code == 503 and not response.text:
            return {"code": 503}

        return super(CloudStorageRequestsProxy, self)._convert_response_to_error(response)

    def _max_retries_for_error(self, error):
        """Handles Datastore response errors according to their documentation.

        Parameters:
          error(dict)

        Returns:
          int or None: The max number of times this error should be
          retried or None if it shouldn't.

        See also:
          https://cloud.google.com/storage/docs/json_api/v1/status-codes
        """
        status = error.get("code")
        return self._MAX_RETRIES.get(status)
