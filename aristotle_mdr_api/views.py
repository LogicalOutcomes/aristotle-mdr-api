from django.http import Http404
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied

from rest_framework import serializers, pagination
from rest_framework import status
from rest_framework.views  import APIView
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.decorators import detail_route

from django.forms import model_to_dict
from aristotle_mdr import models, perms
from aristotle_mdr.forms.search import PermissionSearchForm,PermissionSearchQuerySet

from rest_framework import viewsets

standard_fields = ('id','concept_type','api_url','name','status','description')
class ConceptSerializerBase(serializers.ModelSerializer):
    api_url = serializers.HyperlinkedIdentityField(view_name='aristotle_mdr_api:_concept-detail', format='html')
    concept_type = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()

    class Meta:
        model = models._concept
        fields = standard_fields
    def get_concept_type(self,instance):
        item = instance.item
        out = {"app":item._meta.app_label,'model':item._meta.model_name}
        return out
    def get_status(self,instance):
        out = {"public":instance.is_public(),'locked':instance.is_locked()}
        return out
    def get_description(self,instance):
        return instance.description

class ConceptListSerializer(ConceptSerializerBase):
    def get_description(self,instance):
        from django.utils.html import strip_tags
        import re
        d = strip_tags(instance.description)
        d = re.sub(r"\s+", " ",d, flags=re.UNICODE)
        d=d.split()
        if len(d) > 100:
            d = d[0:100] + ["..."]
        return " ".join(d)

class ConceptDetailSerializer(ConceptSerializerBase):
    superseded_by = serializers.HyperlinkedRelatedField(view_name='aristotle_mdr_api:_concept-detail', format='html',read_only='True')
    supersedes = serializers.HyperlinkedRelatedField(many=True,view_name='aristotle_mdr_api:_concept-detail', format='html',read_only='True')
    fields = serializers.SerializerMethodField('get_extra_fields')

    class Meta:
        model = models._concept
        fields = standard_fields+('fields','superseded_by','supersedes')
    def get_extra_fields(self,instance):
        concept_dict = model_to_dict(instance,
            fields=[field.name for field in instance._meta.fields if field.name not in api_excluded_fields],
            exclude=api_excluded_fields
            )
        return concept_dict

class ConceptResultsPagination(pagination.PageNumberPagination):
    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 100


class MultiSerializerViewSet(viewsets.ReadOnlyModelViewSet):
    serializers = {
        'default': None,
    }

    def get_serializer_class(self):
        return self.serializers.get(self.action,self.serializers['default'])

class ConceptViewSet(MultiSerializerViewSet):
    """
    This viewset automatically provides `list` and `detail` actions.
    """
    queryset = models._concept.objects.all()
    serializer_class = ConceptListSerializer
    pagination_class = ConceptResultsPagination

    serializers = {
        'default':  ConceptDetailSerializer,
        'list':    ConceptListSerializer,
        'detail':  ConceptDetailSerializer,
    }

    def get_queryset(self):
        """
        Optionally restricts the returned purchases to a given user,
        by filtering against a `username` query parameter in the URL.

        Possible arguments include:

        type (string) : restricts to a particular concept type, eg. dataelement

        """
        queryset = self.queryset
        concepttype = self.request.QUERY_PARAMS.get('type', None)
        if concepttype is not None:
            ct = concepttype.lower().split(":",1)
            if len(ct) == 2:
                app,model = ct
                queryset = ContentType.objects.get(app_label=app,model=model).model_class().objects.all()
            else:
                model = concepttype
                queryset = ContentType.objects.get(model=model).model_class().objects.all()
        return queryset.visible(self.request.user)

    def get_object(self):
        item = super(ConceptViewSet,self).get_object()
        request = self.request
        item = item.item
        if not perms.user_can_view(request.user, item):
            raise PermissionDenied
        else:
            return item

aristotle_apps = getattr(settings, 'ARISTOTLE_SETTINGS', {}).get('CONTENT_EXTENSIONS',[])
aristotle_apps += ["aristotle_mdr"]

api_excluded_fields = [
            "_concept_ptr",
            "_concept_ptr_id",
            "_is_locked",
            "_is_public",
            "packages",
            "relatedDiscussions",
            "superseded_by",
            "superseded_by_id",
            "supersedes",
            "version",
            "workgroup",
            "workgroup_id"
        ]

class ConceptTypeSerializer(serializers.ModelSerializer):
    api_url = serializers.HyperlinkedIdentityField(view_name='aristotle_mdr_api:contenttype-detail', format='html')
    documentation = serializers.SerializerMethodField()
    fields = serializers.SerializerMethodField('get_extra_fields')
    class Meta:
        model = ContentType
        fields = ('id','api_url','name','app_label','model','documentation','fields')
    def get_documentation(self,instance):
        return instance.model_class().__doc__.strip()
    def get_extra_fields(self,instance):
        field_names = instance.model_class()._meta.get_all_field_names()
        return [field for field in field_names if field not in api_excluded_fields]

class ConceptTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    This viewset automatically provides `list` and `detail` actions.
    """
    queryset = ContentType.objects.filter(app_label__in=aristotle_apps).all()
    serializer_class = ConceptTypeSerializer

    def get_queryset(self):
        """
        Optionally restricts the returned purchases to a given user,
        by filtering against a `username` query parameter in the URL.
        """
        outputs = []
        for m in ContentType.objects.filter(app_label__in=aristotle_apps).all():
            if issubclass(m.model_class(),models._concept) and not m.model.startswith("_"):
                outputs.append(m)
        return outputs


#class PermissionSearchForm
class ConceptSearchSerializer(serializers.Serializer):
    name = serializers.CharField()
    object = serializers.SerializerMethodField()
    def __init__(self,*args,**kwargs):
        self.request = kwargs.pop('request',None)
        super(ConceptSearchSerializer,self).__init__(*args,**kwargs)
    def get_object(self,instance):
        data = {}
        return ConceptDetailSerializer(instance.object,context={'request': self.request}).data

from haystack.models import SearchResult
#class SearchList(APIView):
class SearchViewSet(viewsets.GenericViewSet):
    "Search."

    serializer_class = ConceptSearchSerializer
    pagination_class = ConceptResultsPagination
    base_name="search"

#    def get(self, request, format=None):
    def list(self, request):
        if not self.request.QUERY_PARAMS.keys():
            return Response({'search_options':'q model state ra'.split()})

        items = PermissionSearchQuerySet().auto_query(self.request.QUERY_PARAMS['q'])
        if self.request.QUERY_PARAMS.get('models') is not None:
            search_models = []
            models = self.request.QUERY_PARAMS.get('models')
            if type(models) != type([]):
                models = [models]
            for mod in models:
                    print mod
                    if len(mod.split('.',1)) == 2:
                        app_label,model=mod.split('.',1)
                        i = ContentType.objects.get(app_label=app_label,model=model)
                    else:
                        i = ContentType.objects.get(model=mod)
                    search_models.append(i.model_class())
            items = items.models(*search_models)
        items = items.apply_permission_checks(user=request.user)

        items = items[:10]
        serializer = ConceptSearchSerializer(items, request=self.request, many=True)
        return Response(serializer.data)
