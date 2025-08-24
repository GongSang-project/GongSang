# 시니어만 접근하도록
from django.contrib.auth.mixins import UserPassesTestMixin

class SeniorRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        u = self.request.user
        return u.is_authenticated and not getattr(u, "is_youth", True)