from django.contrib import admin
from django.urls import path
from django.views.generic import RedirectView

from simulator import views

# /unit, /unit/all și /unit/<id> funcționează și fără "/" final (APPEND_SLASH)
urlpatterns = [
    path('', RedirectView.as_view(pattern_name='unit_list', permanent=False)),
    path('admin/', admin.site.urls),

    # Easy
    path('unit/', views.unit_create_view, name='unit_create'),
    path('unit/all/', views.unit_list_view, name='unit_list'),
    path('unit/simulate/', views.fight_simulate_view, name='fight_simulate'),
    path('unit/<int:unit_id>/', views.unit_detail_view, name='unit_detail'),
    path('unit/<int:unit_id>/heal/', views.unit_heal_view, name='unit_heal'),

    # Hard
    path('people/', views.people_view, name='people'),
]
