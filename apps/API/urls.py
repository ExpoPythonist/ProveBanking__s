from django.conf.urls import url, include

from rest_framework import routers
from rest_framework_nested import routers as nested_routers

from . import views



router = routers.DefaultRouter()
#router.register(r'search', SearchView)
router.register(r'aggregator', views.AggregatorViewSet)
router.register(r'users', views.UserViewSet)
router.register(r'vendors', views.VendorViewSet)
router.register(r'roles', views.RoleViewSet)
router.register(r'divisions', views.DivisionViewSet)
router.register(r'requests', views.RequestViewSet)
router.register(r'locations', views.LocationViewSet)
router.register(r'categories', views.CategoryViewSet)

vendors_router = nested_routers.NestedSimpleRouter(router, r'vendors', lookup='vendor')
vendors_router.register(r'news', views.VendorNewsViewSet)



# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browseable API.
urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^', include(vendors_router.urls)),
    url(r'^add_to_project/', views.add_to_project),
    url(r'^filters/', views.filters, name='filters'),
    url(r'^change_resource_status/', views.change_resource_status),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),

]
