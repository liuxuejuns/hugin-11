import logging
from django.http import HttpResponse

logger = logging.getLogger('django')

def test_view(request):
    print("1111111")
    logger.info('test log')
    logger.warning('warning log')
    logger.error('error log')
    # return 'get'
    return HttpResponse('get')
