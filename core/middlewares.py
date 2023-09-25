def reverse_proxy(get_response):
    def process_request(request):
        xff = request.META.get('X-Forwarded-For')
        raddr = request.META.get('REMOTE_ADDR')
        if "X-Forwarded-For" in request.META:
            xff = request.META.get('X-Forwarded-For').split(",", 1)[0]
        if "REMOTE_ADDR" in request.META:
            raddr = request.META.get('REMOTE_ADDR').split(",", 1)[0]
        request.META['REMOTE_ADDR'] = xff or raddr
        return get_response(request)
    return process_request