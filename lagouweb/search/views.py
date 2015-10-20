# coding=utf-8
import os
from django.shortcuts import render
from django.conf import settings
import jieba
from jieba.analyse.analyzer import ChineseTokenizer
from whoosh.index import open_dir
from whoosh.qparser import MultifieldParser, QueryParser


jieba.add_word(u'机器学习')
jieba.add_word(u'自然语言处理')

cities = [u'不限', u'北京', u'上海', u'深圳', u'广州', u'杭州', u'南京', u'成都', u'武汉', u'西安', u'厦门', u'苏州', u'天津']
stages = [u'不限', u'初创型', u'成长型', u'成熟型', u'已上市']

void_query = u'不限'


def get_tokenized_query(query):
    t = ChineseTokenizer()
    l = t(query)
    q = [token.text for token in l]
    q = u' '.join(q)
    # print(q)
    return q


def index(request):
    query = request.GET.get('q', '')
    if not query:
        return render(request, 'search/index.html', {})

    qtext = get_tokenized_query(query)

    idx_dir = os.path.join(settings.BASE_DIR, 'search/lagou_idx')
    ix = open_dir(idx_dir)
    searcher = ix.searcher()

    parser = MultifieldParser(["name", "com_name", 'city'], schema=ix.schema)
    q = parser.parse(qtext)
    # TODO: print real parsed query object.
    # print q

    page = 1
    if 'pn' in request.GET:
        page = int(request.GET.get('pn'))
    plen = 10
    if 'pl' in request.GET:
        plen = int(request.GET.get('pl'))
    results = searcher.search_page(q, page, pagelen=plen)

    total = len(results)
    # got = results.scored_length()

    total_pages = total / plen + (1 if total % plen else 0)
    page_start = max(1, page - 2)
    page_end = min(total_pages, page_start + 20)

    pos_list = [{'id': hit['id'], 'name': hit['name'], 'com_name': hit['com_name'],
                 'salary': hit['salary'], 'education': hit['education'],
                 'advantage': hit['advantage']}
                for hit in results]
    return render(request, 'search/index.html',
                  {'pos_list': pos_list,
                   'query': query,
                   'page': page, 'plen': plen, 'total_pages': total_pages, 'pages': xrange(page_start, page_end + 1),
                   'prev': page - 1 if page > 1 else 1, 'next': page + 1 if page < total_pages else total_pages})


def rebuild_querystring(dict_, key, value):
    dict_[key] = value
    return dict_.urlencode()


def advanced(request):

    query = request.GET.get('q', None)
    city = request.GET.get('city', None)
    stage = request.GET.get('stage', None)

    dict_ = request.GET.copy()
    city_list = [{'name': c, 'query': rebuild_querystring(dict_, 'city', c)} for c in cities]
    print city_list

    dict_ = request.GET.copy()
    stage_list = [{'name': s, 'query': rebuild_querystring(dict_, 'stage', s)} for s in stages]

    if not query:
        return render(request, 'search/advanced.html',
                      {'city': city,
                       'state': stage,
                       'cities': city_list,
                       'stages': stage_list})

    if not city:
        city = u'上海'
    qtext = get_tokenized_query(query)
    if city != void_query:
        qtext = qtext + u' city:' + city
    if stage and stage != void_query:
        qtext = qtext + u' fin_stage:' + stage
    print qtext

    idx_dir = os.path.join(settings.BASE_DIR, 'search/lagou_idx')
    ix = open_dir(idx_dir)
    searcher = ix.searcher()

    parser = MultifieldParser(["name", "com_name", 'city', 'desc'], schema=ix.schema)
    q = parser.parse(qtext)
    # TODO: print real parsed query object.
    # print q

    page = 1
    if 'pn' in request.GET:
        page = int(request.GET.get('pn'))
    plen = 10
    if 'pl' in request.GET:
        plen = int(request.GET.get('pl'))
    results = searcher.search_page(q, page, pagelen=plen)

    total = len(results)
    total_pages = total / plen + (1 if total % plen else 0)
    page_start = max(1, page - 2)
    page_end = min(total_pages, page_start + 20)

    pos_list = [{'id': hit['id'], 'name': hit['name'], 'com_name': hit['com_name'],
                 'salary': hit['salary'], 'education': hit['education'],
                 'advantage': hit['advantage']}
                for hit in results]

    docnums = [hit.docnum for hit in results]
    keywords = [kw for kw, score in searcher.key_terms(docnums, 'desc', numterms=10) if kw not in qtext]

    suggests = []
    if len(results) < plen:
        print 'find suggests'
        corrector = searcher.corrector('desc')
        suggests = corrector.suggest(query)

    searcher.close()

    return render(request, 'search/advanced.html',
                  {'pos_list': pos_list,
                   'query': query,
                   'city': city,
                   'stage': stage,
                   'keywords': keywords,
                   'suggests': suggests,
                   'cities': city_list,
                   'stages': stage_list,
                   'page': page, 'plen': plen, 'total_pages': total_pages, 'pages': xrange(page_start, page_end + 1),
                   'prev': page - 1 if page > 1 else 1, 'next': page + 1 if page < total_pages else total_pages})


def stats(request):
    return render(request, 'search/stats.html')