from django.conf.urls import url, patterns
from search import views

urlpatterns = patterns('',
                       url(r'^$', views.index, name='search.index'),
                       url(r'^advanced/', views.advanced, name='search.advanced'),
                       url(r'^keywords/', views.keywords, name='search.keywords'),
                       #url(r'^suggest/', views.suggest, name='search.suggest'),
                       url(r'^stats/', views.stats, name='search.stats'),
                       )
