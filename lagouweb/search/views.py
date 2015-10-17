from django.shortcuts import render


def index(request):
    cxt_dict = {'categories': None, 'pages': None}
    return render(request, 'search/index.html', cxt_dict)
