from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
import pdfplumber
import docx
import spacy
import re
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

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
                score = match_score(jd_text, resume_text)
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
    candidates = 3
    
    context = {
        'candidates':candidates,
    }
    return render(request, 'candidates.html', context)