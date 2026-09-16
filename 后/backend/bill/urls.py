from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from .views import (
    BookViewSet, AccountViewSet, CategoryViewSet, TagViewSet, BillViewSet,
    test_auth, test_public,
    statistics_overview, statistics_pie, statistics_trend,
    statistics_accounts, statistics_budget, statistics_tags,
)

router = DefaultRouter()
router.register(r'books', BookViewSet, basename='book')
router.register(r'accounts', AccountViewSet, basename='account')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'tags', TagViewSet, basename='tag')
router.register(r'bills', BillViewSet, basename='bill')

urlpatterns = [
    # Token 接口
    path('token/', obtain_auth_token, name='api_token_auth'),

    # 测试接口
    path('test/auth/', test_auth, name='test_auth'),
    path('test/public/', test_public, name='test_public'),

    # 统计报表接口
    path('statistics/overview/', statistics_overview, name='statistics_overview'),
    path('statistics/pie/', statistics_pie, name='statistics_pie'),
    path('statistics/trend/', statistics_trend, name='statistics_trend'),
    path('statistics/accounts/', statistics_accounts, name='statistics_accounts'),
    path('statistics/budget/', statistics_budget, name='statistics_budget'),
    path('statistics/tags/', statistics_tags, name='statistics_tags'),

    # ViewSet 路由
    path('', include(router.urls)),
]