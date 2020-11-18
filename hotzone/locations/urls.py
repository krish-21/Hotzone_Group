from django.urls import path

from locations import views
from .views import HomePage, get_name, save_address, list_locations, login_view, logOut_view

urlpatterns = [
    path('home',
        HomePage.as_view(),
        name='index'),
    path('search',
        get_name,
        name='search'),
    path('save',
        save_address,
        name='save'),
    path('list',
        list_locations,
        name='list'),
    path('', 
        login_view, 
        name='login'),
    path('logout', 
        logOut_view, 
        name='logout')
]
