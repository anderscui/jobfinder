import datetime
from django import template

register = template.Library()


@register.simple_tag
def cur_time(fmt_str):
    return datetime.datetime.now().strftime(fmt_str)


@register.simple_tag(takes_context=True)
def replace_query_str(context, key, val):
    req = context['request']
    if key:
        dict_ = req.GET.copy()
        dict_[key] = val
    return dict_.urlencode()


@register.simple_tag(takes_context=True)
def query_str(context, key):
    req = context['request']
    return req.GET.get(key, '')


side_pages = [(u'Quick Search', 'search.index'),
              (u'Advanced Search', 'search.advanced'),
              (u'Statistics', 'search.stats'),
              ]


@register.inclusion_tag('sidebar.html')
def get_side_bar(page=None):
    return {'urls': side_pages, 'act_page': page}
