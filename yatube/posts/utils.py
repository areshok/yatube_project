from django.conf import settings
from django.core.paginator import Paginator


def paginator(post_list, request):
    paginator = Paginator(post_list, settings.OUTPUT_LIMIT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
