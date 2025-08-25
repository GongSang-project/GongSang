from django.urls import path
from . import views
from .views import home_view, autocomplete_region
#from .views import home_view, autocomplete_region, listings_by_region  # 여기서 import 추가

urlpatterns = [
    path('', home_view, name='home'),

    path('search_location/', autocomplete_region, name='autocomplete_region'),
    path("autocomplete-region/", autocomplete_region, name="autocomplete_region_alias"),

    #path('autocomplete-region/', autocomplete_region, name='autocomplete_region'),
    #path('search_location/', views.autocomplete_region),
    #path('listings-by-region/', listings_by_region, name='listings_by_region'),
]