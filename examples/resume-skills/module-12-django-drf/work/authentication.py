from django.contrib.auth import get_user_model
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed
from .models import Membership

# Public opaque fixtures; no JWT, password verification or production token store.
TOKENS = {b'alice-demo':('alice','alpha'), b'bob-demo':('bob','alpha'),
          b'reader-demo':('reader','alpha'), b'eve-demo':('eve','beta')}

class FixtureBearer(BaseAuthentication):
    def authenticate(self, request):
        parts = get_authorization_header(request).split()
        if not parts:
            return None
        if len(parts)!=2 or parts[0].lower()!=b'bearer' or parts[1] not in TOKENS:
            raise AuthenticationFailed('Invalid fixture credential')
        username, tenant = TOKENS[parts[1]]
        try:
            user = get_user_model().objects.get(username=username, is_active=True)
            membership = Membership.objects.select_related('tenant').get(user=user, tenant__slug=tenant)
        except (get_user_model().DoesNotExist, Membership.DoesNotExist):
            raise AuthenticationFailed('Invalid fixture credential')
        return user, membership
    def authenticate_header(self, request):
        return 'Bearer'
