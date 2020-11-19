from django.urls import path

from locations import views
from .views import HomePage, search_location, save_location, list_locations, login_view, logout_view

urlpatterns = [
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
    path('', 
        login_view, 
        name='login'),
    path('logout', 
        logout_view, 
        name='logout')
]
