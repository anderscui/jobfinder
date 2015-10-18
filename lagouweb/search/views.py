# coding=utf-8
import os
from django.shortcuts import render
from django.conf import settings
from jieba.analyse.analyzer import ChineseTokenizer
from whoosh.index import open_dir
from whoosh.qparser import MultifieldParser, QueryParser


def build_query(query):
    pass


def index(request):
    query = request.GET.get('q', '')
    if not query:
        return render(request, 'search/index.html', {})

    t = ChineseTokenizer()
    l = t(query)
    q = [token.text for token in l]
    q = u' '.join(q)
    print(q)

    idx_dir = os.path.join(settings.BASE_DIR, 'search/lagou_idx')
    ix = open_dir(idx_dir)
    searcher = ix.searcher()

    parser = MultifieldParser(["name", "com_name", 'city'], schema=ix.schema)
    q = parser.parse(q)
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
    page_start = max(1, page-2)
    page_end = min(total_pages, page_start+20)

    pos_list = [{'id': hit['id'], 'name': hit['name'], 'com_name': hit['com_name'],
                 'salary': hit['salary'], 'education': hit['education'],
                 'advantage': hit['advantage']}
                for hit in results]
    return render(request, 'search/index.html',
                  {'pos_list': pos_list,
                   'query': query,
                   'page': page, 'plen': plen, 'total_pages': total_pages, 'pages': xrange(page_start, page_end+1),
                   'prev': page-1 if page > 1 else 1, 'next': page+1 if page < total_pages else total_pages})


def search(request):
    return index(request)
