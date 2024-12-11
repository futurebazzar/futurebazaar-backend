from functools import wraps
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied

def restrict_user_type(allowed_user_type: str):
    """
    Decorator to restrict access to views based on the user type.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Ensure the user is authenticated
            if not request.user.is_authenticated:
                return JsonResponse({"error": "Authentication required."}, status=401)

            # Check if the user has the required user type
            if request.user.user_type != allowed_user_type:
                return JsonResponse(
                    {"error": f"Access restricted to {allowed_user_type} users."},
                    status=403
                )
            
            return view_func(request, *args, **kwargs)
        
        return _wrapped_view
    return decorator
