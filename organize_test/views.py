from django.shortcuts import render, redirect
from .models import newTest, Position, Question, QuestionOption

# Create your views here.

def organize_test(request):
    newtest = newTest.objects.all()
    positions = Position.objects.all()
    
    if request.method == 'POST':
        title  = request.POST['title']
        position_id  = request.POST['position']
        level  = request.POST['level']
        duration  = request.POST['duration']
        passing_score  = request.POST['passing_score']
        test_description  = request.POST['description']
        
        try:
            position_obj = Position.objects.get(id=position_id)
            newTest.objects.create(title=title, position=position_obj, difficulty=level,duration=duration,passing_score=passing_score,description=test_description)
            return redirect('manage_test')
            
        except Position.DoesNotExist:
            pass
        
    context = {
        'newtest':newtest,
        'positions': positions,
    }
    return render(request, 'test.html', context)
    
def add_question(request):
    if request.method == 'POST':
        type = request.POST['type']
        question = request.POST['question']
        difficulty = request.POST['difficulty']
        marks = request.POST['marks']
        
        question_obj = Question.objects.create(question_text=question, 
        question_type=type, 
        difficulty=difficulty, 
        marks=marks)
        
        if type == 'coding':
            expected_solution = request.POST.get('expected_solution', '')
            question_obj.expected_solution = expected_solution
            question_obj.save()
            
        elif type == 'descriptive':
            sample_answer = request.POST.get('sample_answer', '')
            question_obj.sample_answer = sample_answer
            question_obj.save()
            
        elif type == 'mcq':
            option_a = request.POST.get('option_a')
            option_b = request.POST.get('option_b')
            option_c = request.POST.get('option_c')
            option_d = request.POST.get('option_d')
            correct_answer = request.POST.get('correct_answer')
            
            QuestionOption.objects.create(
                question = question_obj,
                option_text = option_a,
                is_correct = (correct_answer == 'A')
            )
            QuestionOption.objects.create(
                question = question_obj,
                option_text = option_b,
                is_correct = (correct_answer == 'B')
            )
            QuestionOption.objects.create(
                question = question_obj,
                option_text = option_c,
                is_correct = (correct_answer == 'C')
            )
            QuestionOption.objects.create(
                question = question_obj,
                option_text = option_d,
                is_correct = (correct_answer == 'D')
            )
        
    return render(request, 'add_question.html')
    
def manage_test(request):
    return render(request, 'manage_test.html')