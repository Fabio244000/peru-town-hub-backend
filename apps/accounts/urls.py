from rest_framework.routers import SimpleRouter

from apps.accounts.apis import AccountViewSet

app_name = 'accounts'

router = SimpleRouter()
router.register('accounts', AccountViewSet, basename='accounts')

urlpatterns = router.urls
