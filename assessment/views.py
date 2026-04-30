from django.shortcuts import render
from .models import TestAttempt
# Create your views here.

def assessment_test(request, token):
    try:
        attempt = TestAttempt.objects.get(token=token)
    except TestAttempt.DoesNotExist:
        return HttpResponse("Invalid or expired link")

    request.session['attempt_id'] = attempt.id
    request.session['is_candidate'] = True

    return render(request, 'assessment_test.html', {
        'test': attempt.test
    })