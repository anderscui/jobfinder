# coding=utf-8
import os
from django.shortcuts import render
from django.conf import settings
from whoosh.index import open_dir
from whoosh.qparser import MultifieldParser, QueryParser


def index(request):
    query = request.GET.get('q', '')
    print query
    if not query:
        return render(request, 'search/index.html', {})

    idx_dir = os.path.join(settings.BASE_DIR, 'search/lagou_idx')
    ix = open_dir(idx_dir)
    searcher = ix.searcher()

    parser = QueryParser("name", schema=ix.schema)
    q = parser.parse(query + u' city:上海')

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

    print(xrange(page_start, page_end))

    pos_list = [{'id': hit['id'], 'name': hit['name'], 'com_name': hit['com_name']} for hit in results]
    return render(request, 'search/index.html',
                  {'pos_list': pos_list,
                   'query': query,
                   'page': page, 'plen': plen, 'total_pages': total_pages, 'pages': xrange(page_start, page_end+1),
                   'prev': page-1 if page > 1 else 1, 'next': page+1 if page < total_pages else total_pages})


def search(request):
    return index(request)
