from django.shortcuts import render, redirect, get_object_or_404,HttpResponse
from .models import TestAttempt, Answer
from organize_test.models import QuestionModel
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from datetime import timedelta
# Create your views here.

def assessment_test(request, token):
    try:
        attempt = TestAttempt.objects.get(token=token)
    except TestAttempt.DoesNotExist:
        return HttpResponse("Invalid or expired link")
        
    now = timezone.now()
    start_time = attempt.scheduled_at 
    if not start_time:
        return HttpResponse("Test schedule not set")
    end_time = start_time + timedelta(minutes=attempt.test.duration)

    request.session['attempt_id'] = attempt.id
    request.session['is_candidate'] = True

    return render(request, 'assessment_test.html', {
        'test': attempt.test,
        'attempt': attempt,
        "start_time": start_time,
        "end_time": end_time,
        "now": now
    })
    
def start_test(request, token):
    attempt = get_object_or_404(TestAttempt, token=token)
    
    if timezone.is_naive(attempt.scheduled_at):
        attempt_time = timezone.make_aware(attempt.scheduled_at)
    else:
        attempt_time = attempt.scheduled_at

    if timezone.now() < attempt_time:
        return HttpResponse("Test not started yet")

    if attempt.status == "submitted":
        return HttpResponse("You have already completed this test.")

    if attempt.status == "started":
        return redirect('take_test', token=token)

    if not attempt.start_time:
        attempt.start_time = timezone.now()
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
    
    remaining_seconds = 0

    if attempt.start_time:
        elapsed = (timezone.now() - attempt.start_time).total_seconds()
        total_time = attempt.test.duration * 60
        remaining_seconds = max(0, int(total_time - elapsed))

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

        if request.POST.get("auto_submit") == "true":
            return HttpResponse(f"Time over. Auto-submitted.")
        else:
            return HttpResponse(f"Test submitted successfully.")

    total_marks = sum(q.marks for q in questions)

    return render(request, "take_test.html", {
        "attempt": attempt,
        "test": attempt.test,
        "questions": questions,
        "total_marks": total_marks,
        "remaining_seconds": remaining_seconds
    })
    