from django.shortcuts import render, redirect
from django.core.files.storage import FileSystemStorage
import pdfplumber
import docx
import spacy
import re
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from .models import UserInfo
from django.core.mail import send_mail, send_mass_mail
from django.contrib import messages
from resume_project.settings import EMAIL_HOST_USER
from openpyxl import Workbook
from django.http import HttpResponse
from datetime import datetime


nlp = spacy.load("en_core_web_sm")
model = SentenceTransformer('all-MiniLM-L6-v2')

def extract_text_from_pdf(file):
    with pdfplumber.open(file) as pdf:
        return "\n".join(page.extract_text() or "" for page in pdf.pages)

def extract_text_from_docx(file):
    doc = docx.Document(file)
    return "\n".join([para.text for para in doc.paragraphs])

def extract_text(file):
    if file.name.endswith(".pdf"):
        return extract_text_from_pdf(file)
    elif file.name.endswith(".docx"):
        return extract_text_from_docx(file)
    else:
        return file.read().decode("utf-8")

def match_score(jd_text, resume_text):
    jd_vec = model.encode(jd_text)
    res_vec = model.encode(resume_text)
    return float(cosine_similarity([jd_vec], [res_vec])[0][0]) * 100

def extract_resume_details(resume_text):
    doc = nlp(resume_text)
    
    # Extract email
    email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', resume_text)
    email = email_match.group(0) if email_match else "Not found"
    
    # name = email.split('@')[0]
    name = re.sub(r'[^a-zA-Z\s]', '', email.split('@')[0]).capitalize()
    
    # Extract skills (predefined list matching)
    skills_list = [
        'Python', 'Django', 'JavaScript', 'React', 'Node.js', 'Java', 'C++', 
        'SQL', 'PostgreSQL', 'MongoDB', 'AWS', 'Docker', 'Kubernetes', 
        'Machine Learning', 'Deep Learning', 'TensorFlow', 'PyTorch',
        'Git', 'HTML', 'CSS', 'REST API', 'Flask', 'FastAPI', 'HR Software Proficiency', 'Email Management', 'HRIS Management', 'Data Management'
    ]
    
    # Find skills present in resume
    resume_lower = resume_text.lower()
    found_skills = [skill for skill in skills_list if skill.lower() in resume_lower]
    
    return {
        'name': name,
        'email': email,
        'skills': found_skills[:5]  # Top 5 skills
    }
    
    
def home(request):
    context = {'jd_text': None, 'results': []}
    
    if request.method == 'POST':
        # Handle JD upload
        if 'jd_file' in request.FILES:
            jd_file = request.FILES['jd_file']
            jd_text = extract_text(jd_file)
            request.session['jd_text'] = jd_text
            context['jd_text'] = jd_text[:300] + "..."
        
        # Handle resume uploads
        if 'resume_files' in request.FILES and 'jd_text' in request.session:
            jd_text = request.session['jd_text']
            resume_files = request.FILES.getlist('resume_files')
            
            results = []
            for resume_file in resume_files:
                resume_text = extract_text(resume_file)
                details = extract_resume_details(resume_text)
                score = match_score(jd_text, resume_text)
                if score >= 80:
                    status = True
                else:
                    status = False
                UserInfo.objects.create(name = details['name'], email = details['email'], skills = details['skills'], score = score, resume = resume_file, status = status)
                results.append({
                    'name': resume_file.name,
                    'score': f"{score:.2f}"
                })
            
            context['results'] = results
            context['jd_text'] = jd_text[:300] + "..."
    
    elif 'jd_text' in request.session:
        context['jd_text'] = request.session['jd_text'][:300] + "..."
    
    return render(request, 'home.html', context)

def candidates(request):
    users = UserInfo.objects.all()
    candidates = len(users)
    
    context = {
        'candidates':candidates,
        'users':users,
    }
    return render(request, 'candidates.html', context)
    
def delete_user(request, user_id):
    UserInfo.objects.filter(id = user_id).delete()
    return redirect('candidates')
    
def send_email_view(request):
    if request.method == 'POST':
        to_email = request.POST.get('to_email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        try:
            send_mail(
                subject,
                message,
                EMAIL_HOST_USER,
                [to_email],
                fail_silently = False,
            )
            messages.success(request, 'Email sent successfully.')
        except Exception as e:
            messages.error(request, 'Failed to send email.')
            
        return redirect('candidates')
        
def export_candidates(request):
    wb = Workbook()
    ws = wb.active
    ws.title = 'Candidates'
    
    headers = ['Name', 'Email','Match Score', 'Skills', 'Status']
    ws.append(headers)
    
    candidates = UserInfo.objects.all()
    for candidate in candidates:
        skills = ', '.join(candidate.skills) if isinstance(candidate.skills, list) else candidate.skills
        status = 'Shortlisted' if candidate.status else 'Review'
        ws.append([
            candidate.name,
            candidate.email,
            f"{candidate.score}%",
            skills,
            status
        ])
        
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=candidates.xlsx'
    
    wb.save(response)
    return response

def schedule_interviews(request):
    if request.method == 'POST':
        candidate_ids = request.POST.getlist('candidates')
        interview_datetime = request.POST.get('interview_datetime')
        subject = request.POST.get('subject')
        message_template = request.POST.get('message')
        
        # Format datetime
        dt = datetime.strptime(interview_datetime, '%Y-%m-%dT%H:%M')
        formatted_datetime = dt.strftime('%B %d, %Y at %I:%M %p')
        
        # Replace placeholder in message
        message = message_template.replace('[Will be filled automatically]', formatted_datetime)
        
        # Get candidates
        candidates = UserInfo.objects.filter(id__in=candidate_ids)
        
        # Prepare emails
        emails = []
        for candidate in candidates:
            personalized_message = message.replace('Dear Candidate', f'Dear {candidate.name}')
            emails.append((
                subject,
                personalized_message,
                EMAIL_HOST_USER,  # From email
                [candidate.email]
            ))
        
        # Send emails
        try:
            send_mass_mail(emails, fail_silently=False)
            messages.success(request, f'Interview invitations sent to {len(emails)} candidates!')
        except Exception as e:
            messages.error(request, f'Failed to send emails: {str(e)}')
        
        return redirect('candidates')
        
def dashboard(request):
    return render(request, 'dashboard.html')