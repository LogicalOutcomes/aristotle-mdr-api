from django.conf.urls import patterns, include, url
from aristotle_mdr_api import views
from rest_framework.routers import DefaultRouter

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r'concepts', views.ConceptViewSet)
router.register(r'types', views.ConceptTypeViewSet)

urlpatterns = patterns('',
#    url(r'^concept/(?P<pk>[0-9]+)/', views.ConceptDetail.as_view(), name='_concept-detail'),
    url(r'^', include(router.urls)),
#    url(r'^concepts/(?P<app>[A-Za-z\-]+)/(?P<model>[A-Za-z\-]+)(?:/(?P<pk>[0-9]+))?', views.ConceptList.as_view(), name='_concept-list'),
    url(r'^auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^search/', views.SearchList.as_view(), name='search'),
    )
