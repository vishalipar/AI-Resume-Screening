from django.shortcuts import render, redirect
from .models import newTest, Position

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
    return render(request, 'add_question.html')
    
def manage_test(request):
    return render(request, 'manage_test.html')