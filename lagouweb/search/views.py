# coding=utf-8
import os
import datetime
import re
from django.shortcuts import render
from django.conf import settings
import jieba
from jieba.analyse.analyzer import ChineseTokenizer
from whoosh.index import open_dir
from whoosh.qparser import MultifieldParser, QueryParser


# jieba.add_word(u'机器学习')
# jieba.add_word(u'自然语言处理')

cities = [u'不限', u'北京', u'上海', u'深圳', u'广州', u'杭州', u'南京', u'成都', u'武汉', u'西安', u'厦门', u'苏州', u'天津']
stages = [u'不限', u'初创型', u'成长型', u'成熟型', u'已上市']
salaries = [u'不限', u'5k以下', u'5k-10k', u'10k-15k', u'15k-25k', u'25k-50k', u'50k以上']
dates_keys = [u'不限', u'三天内', u'一周内', u'两周内', u'一月内']
dates_vals = [0, 3, 7, 14, 30]

void_query = u'不限'


def parse_time(s):
    if '.' in s:
        return datetime.datetime.strptime(s, '%Y-%m-%d %H:%M:%S.%f')
    else:
        return datetime.datetime.strptime(s, '%Y-%m-%d %H:%M:%S')


def parse_salary(s):
    m = re.search(u'(\d+)k以上', s)
    if m:
        return int(m.group(1)) * 1000, 2000000

    m = re.search(u'(\d+)k以下', s)
    if m:
        return 1, int(m.group(1)) * 1000

    m = re.search(u'(\d+)k-(\d+)k', s)
    if m:
        return int(m.group(1)) * 1000, int(m.group(2)) * 1000
    return None


def parse_date(days):
    print days
    if days not in dates_keys:
        return None

    i = dates_keys.index(days)
    delta = dates_vals[i] - 1
    if delta <= 0:
        return None

    now = datetime.datetime.now()
    date_to = now
    date_from = now + datetime.timedelta(days=-delta)
    return date_from.strftime('%Y%m%d'), date_to.strftime('%Y%m%d')


def get_tokenized_query(query):
    t = ChineseTokenizer()
    l = t(query)
    q = [token.text for token in l]
    q = u' '.join(q)
    return q


def index(request):
    query = request.GET.get('q', '')
    if not query:
        return render(request, 'search/index.html', {'page_name': 'search.index'})

    qtext = get_tokenized_query(query)
    print qtext

    idx_dir = os.path.join(settings.BASE_DIR, 'search/lagou_idx_quick')
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
                  {'page_name': 'search.index',
                   'pos_list': pos_list,
                   'query': query,
                   'page': page, 'plen': plen, 'total_pages': total_pages, 'pages': xrange(page_start, page_end + 1),
                   'prev': page - 1 if page > 1 else 1, 'next': page + 1 if page < total_pages else total_pages})


def advanced(request):
    query = request.GET.get('q', '')
    city = request.GET.get('city', u'上海')
    stage = request.GET.get('stage', '')

    salary = request.GET.get('salary', '')
    salary_range = parse_salary(salary)

    date = request.GET.get('date', '')
    date_range = parse_date(date)

    if not query:
        return render(request, 'search/advanced.html',
                      {'page_name': 'search.advanced',
                       'city': city,
                       'stage': stage,
                       'salary': salary,
                       'date': date,
                       'cities': cities,
                       'stages': stages,
                       'salaries': salaries,
                       'dates': dates_keys})

    if not city:
        city = u'上海'
    qtext = get_tokenized_query(query)
    if city != void_query:
        qtext += u' city:' + city
    if stage and stage != void_query:
        qtext += u' fin_stage:' + stage
    if salary_range:
        qtext += u' salary_from:[1 TO {1}] salary_to:[{0} TO]'.format(salary_range[0], salary_range[1])
    if date_range:
        qtext += u' date:[{0} TO {1}]'.format(date_range[0], date_range[1])
    print qtext

    idx_dir = os.path.join(settings.BASE_DIR, 'search/lagou_idx')
    ix = open_dir(idx_dir)
    searcher = ix.searcher()

    parser = MultifieldParser(["name", "com_name"], schema=ix.schema)
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
                  {'page_name': 'search.advanced',
                   'query': query,
                   'city': city,
                   'stage': stage,
                   'salary': salary,
                   'date': date,
                   'pos_list': pos_list,
                   'keywords': keywords,
                   'suggests': suggests,
                   'cities': cities,
                   'stages': stages,
                   'salaries': salaries,
                   'dates': dates_keys,
                   'page': page, 'plen': plen, 'total_pages': total_pages, 'pages': xrange(page_start, page_end + 1),
                   'prev': page - 1 if page > 1 else 1, 'next': page + 1 if page < total_pages else total_pages})


def keywords(request):
    query = request.GET.get('q', '')
    if not query:
        return render(request, 'search/keywords.html', {'page_name': 'search.keywords'})

    qtext = get_tokenized_query(query)
    print qtext

    idx_dir = os.path.join(settings.BASE_DIR, 'search/lagou_idx')
    ix = open_dir(idx_dir)
    searcher = ix.searcher()

    parser = MultifieldParser(["name", "com_name", 'city'], schema=ix.schema)
    q = parser.parse(qtext)

    plen = 100
    results = searcher.search(q, limit=plen)

    total = len(results)
    got = results.scored_length()
    numterms = 100
    if got < 10:
        numterms = 10
    elif got < 100:
        numterms = 50

    keywords = [(kw, score) for kw, score in results.key_terms("desc", docs=got, numterms=numterms)]

    return render(request, 'search/keywords.html',
                  {'page_name': 'search.keywords',
                   'query': query,
                   'total': total,
                   'got': got,
                   'keywords': keywords,
                  })


def stats(request):
    return render(request, 'search/stats.html', {'page_name': 'search.stats'})