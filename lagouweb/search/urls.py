from django.conf.urls import url, patterns
from search import views

urlpatterns = patterns('',
                       url(r'^$', views.index, name='search.index'),
                       # url(r'^search$', views.search, name='search.search'),
                       )
