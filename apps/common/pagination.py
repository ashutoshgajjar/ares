from rest_framework.pagination import LimitOffsetPagination

class DynamicLimitOffsetPagination(LimitOffsetPagination):
    """
    Dynamic pagination with:

    limit=<number>
    offset=<number>

    Supported:
        ?limit=1
        ?limit=50
        ?limit=100
        ?limit=all
        ?limit=50&offset=100

    `limit=all` disables the normal maximum.
    """

    default_limit = 50

    min_limit = 1
    max_limit = 100

    limit_query_param = "limit"
    offset_query_param = "offset"

    def get_limit(self, request):
        raw_limit = request.query_params.get(
            self.limit_query_param
        )

        if raw_limit is None:
            return self.default_limit

        if raw_limit.lower() == "all":
            return None

        try:
            limit = int(raw_limit)
        except (TypeError, ValueError):
            return self.default_limit

        if limit < self.min_limit:
            return self.min_limit

        if limit > self.max_limit:
            return self.max_limit

        return limit

    def paginate_queryset(
        self,
        queryset,
        request,
        view=None,
    ):
        self.request = request

        self.limit = self.get_limit(request)

        self.count = self.get_count(queryset)

        if self.limit is None:
            # `limit=all`
            self.offset = 0
            self.limit = self.count
            self.count = self.count

            return list(queryset)

        self.offset = self.get_offset(request)

        if (
            self.count > self.limit
            and self.template is not None
        ):
            self.display_page_controls = True

        if self.count == 0:
            return []

        return list(
            queryset[
                self.offset : self.offset + self.limit
            ]
        )