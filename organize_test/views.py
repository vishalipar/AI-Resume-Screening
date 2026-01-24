from django.shortcuts import render

# Create your views here.

def organize_test(request):
    return render(request, 'test.html')