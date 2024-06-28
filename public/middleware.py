from django.utils.deprecation import MiddlewareMixin
import logging, json

api_logger = logging.getLogger("api")


class APIMiddleware(MiddlewareMixin):
    def process_request(self, request):
        pass

    def process_view(self, request, view_func, view_args, view_kwargs):
        api_logger.info(
            " ".join([str(request.user), str(request.method), str(request.path)])
        )
        api_logger.info(
            " ".join([str(request.headers), str(request.GET), str(request.POST)])
        )
