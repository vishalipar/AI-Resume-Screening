from django.shortcuts import render, redirect, get_object_or_404,HttpResponse
from .models import TestAttempt
from organize_test.models import QuestionModel
# Create your views here.

def assessment_test(request, token):
    try:
        attempt = TestAttempt.objects.get(token=token)
    except TestAttempt.DoesNotExist:
        return HttpResponse("Invalid or expired link")

    request.session['attempt_id'] = attempt.id
    request.session['is_candidate'] = True

    return render(request, 'assessment_test.html', {
        'test': attempt.test,
        'attempt': attempt
    })
    
def start_test(request, token):
    attempt = TestAttempt.objects.get(token=token)
    # mark as started
    attempt.status = "started"
    attempt.save()
    request.session['attempt_id'] = attempt.id
    return redirect('take_test', token=token)
    
def take_test(request, token):
    attempt = get_object_or_404(TestAttempt, token=token)
    # optional: prevent reattempt
    # if attempt.submitted:
    #     return HttpResponse("You already submitted this test")
    
    questions = QuestionModel.objects.filter(
        test=attempt.test,
        is_selected=True
    )

    # mark started
    attempt.started = True
    attempt.save()
    total_marks = sum(q.marks for q in questions)
    return render(request, "take_test.html", {
        "attempt": attempt,
        "test": attempt.test,
        "questions": questions,
        "total_marks": total_marks
    })
    