"""
URL configuration for tradingtracker project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from charts import views
from django.views.generic import RedirectView
from django.urls import path

urlpatterns = [
    path('', RedirectView.as_view(url='charts/homepage/')),
    path('admin/', admin.site.urls),
    path('charts/homepage/', views.homepage.as_view(), name='homepage'),
    path('charts/markets/', views.markets.as_view(), name='markets'),
    path('api/live-data/', views.get_live_data, name='get_live_data'),
    path('api/market-data/chart/', views.get_chart_data, name='get_chart_data'),
    path('charts/login/', views.login_view.as_view(), name='login'),
    path('charts/logout/', views.logout_view.as_view(), name='logout'),
    path('charts/register/', views.register_view.as_view(), name='register'),
    path('charts/profile/', views.profile_view.as_view(), name='profile'),
]
# This file defines the URL patterns for the tradingtracker project.
# It includes paths for the admin interface, homepage, markets, login, logout etc