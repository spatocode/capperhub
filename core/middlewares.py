def reverse_proxy(get_response):
    def process_request(request):
        request.META['REMOTE_ADDR'] = request.META.get('X-Forwarded-For') or request.META.get('REMOTE_ADDR')
        return get_response(request)
    return process_request