from django.http import JsonResponse

# Allow only particular domain to access the API
class CheckAllowedOriginMixin:
    ALLOWED_ORIGINS = [
        "https://onlinecomplain.subrat.xyz", 
    ]

    def dispatch(self, request, *args, **kwargs):
        origin = request.META.get('HTTP_ORIGIN')
        print(origin)
        if origin not in self.ALLOWED_ORIGINS:
            return JsonResponse({'error': 'Forbidden'}, status=403)
        return super().dispatch(request, *args, **kwargs)
