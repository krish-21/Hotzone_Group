from django.urls import path

from locations import views
from .views import login_view, logout_view, HomePage, search_location, save_location, list_locations, list_cases, view_case

urlpatterns = [
    path('', 
        login_view, 
        name='login'),
    path('logout', 
        logout_view, 
        name='logout'),
    path('home',
        HomePage.as_view(),
        name='index'),
    path('search_location',
        search_location,
        name='search_location'),
    path('save_location',
        save_location,
        name='save_location'),
    path('list_location',
        list_locations,
        name='list_location'),
    path('list_cases',
        list_cases,
        name='list_cases'),
    path('view_case',
        view_case,
        name='view_case'),
]
