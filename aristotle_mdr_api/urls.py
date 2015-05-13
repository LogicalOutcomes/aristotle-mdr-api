from django.conf.urls import patterns, include, url
from aristotle_mdr_api import views
from rest_framework import routers

# Create a router and register our viewsets with it.
router = routers.DefaultRouter()
router.register(r'concepts', views.ConceptViewSet)
router.register(r'types', views.ConceptTypeViewSet)
router.register(r'search', views.SearchViewSet, base_name="search")

urlpatterns = patterns('',
    url(r'^', include(router.urls)),
    url(r'^auth/', include('rest_framework.urls', namespace='rest_framework')),
    )
