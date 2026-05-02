from django.shortcuts import render, redirect, get_object_or_404,HttpResponse
from .models import TestAttempt, Answer
from organize_test.models import QuestionModel
from django.views.decorators.csrf import csrf_exempt
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
    attempt = get_object_or_404(TestAttempt, token=token)

    if attempt.status == "submitted":
        return HttpResponse("You have already completed this test.")

    if attempt.status == "started":
        return redirect('take_test', token=token)

    attempt.status = "started"
    attempt.save()

    request.session['attempt_id'] = attempt.id

    return redirect('take_test', token=token)
    
@csrf_exempt
def take_test(request, token):
    attempt = get_object_or_404(TestAttempt, token=token)
    # optional: prevent reattempt
    if attempt.status == 'submitted':
        return HttpResponse("You already submitted this test")
    
    questions = QuestionModel.objects.filter(
        test=attempt.test,
        is_selected=True
    )

    if request.method == "POST":
        total_score = 0
        for q in questions:
            selected = request.POST.get(f"q_{q.id}")

            Answer.objects.create(
                attempt=attempt,
                question=q,
                selected_answer=selected
            )

            if selected == q.answer:
                total_score += q.marks

        attempt.score = total_score
        attempt.status = "submitted"
        attempt.save()

        return HttpResponse(f"Test submitted successfully")

    total_marks = sum(q.marks for q in questions)

    return render(request, "take_test.html", {
        "attempt": attempt,
        "test": attempt.test,
        "questions": questions,
        "total_marks": total_marks
    })
    