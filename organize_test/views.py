from django.shortcuts import render, redirect
from .models import newTest, Position, Question, QuestionOption, QuestionModel
from rest_framework.views import APIView
from rest_framework.response import Response
from .utils import generate_questions
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
    questions = QuestionModel.objects.all().order_by('-id')

    return render(request, "manage_test.html", {
        "questions": questions
    })
    
class GenerateQuestionsAPI(APIView):
    def post(self, request):
        paragraph = request.data.get("paragraph")
        q_type = request.data.get("type")
        count = request.data.get("count")
        difficulty = request.data.get("difficulty")
        mcq_options = request.data.get("mcq_options")

        data = generate_questions(paragraph, q_type, count, difficulty, mcq_options)
        return Response({"questions": data})
        
class SaveQuestionsAPI(APIView):
    def post(self, request):
        questions = request.data.get("questions", [])

        saved = []

        for q in questions:
            obj = QuestionModel.objects.create(
                question=q.get("question", "").strip(),
                options=q.get("options", []),   # handles MCQ
                answer=q.get("answer", "").strip()
            )
            saved.append(obj.id)

        return Response({
            "status": "success",
            "saved_ids": saved
        })
        
class DeleteQuestionAPI(APIView):
    def post(self, request):
        q_id = request.data.get("id")
        QuestionModel.objects.filter(id=q_id).delete()
        return Response({"status": "deleted"})
        
class UpdateQuestionsAPI(APIView):
    def post(self, request):
        questions = request.data.get("questions", [])

        for q in questions:
            obj = QuestionModel.objects.get(id=q["id"])
            obj.question = q["question"]
            obj.options = q.get("options", [])
            obj.answer = q["answer"]
            obj.save()

        return Response({"status": "updated"})
