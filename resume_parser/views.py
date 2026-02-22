from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from .parser import ResumeParser
from .models import JobRole, Resume

class ResumeUploadView(APIView):
    parser_classes = (MultiPartParser,)
    
    def post(self, request):
        resume_file = request.FILES.get('resume')
        
        if not resume_file:
            return Response({'error': 'Resume file required'}, status=400)
        
        parser = ResumeParser()
        result = parser.parse_resume(resume_file, resume_file.name)
        
        if 'error' in result:
            return Response({'error': result['error']}, status=400)
            
        # CHECK FOR DUPLICATE EMAIL
        email = result.get('email', '')
        if email and Resume.objects.filter(email=email).exists():
            return Response({
                'error': 'Duplicate resume! A resume with this email already exists.',
                'duplicate': True
            }, status=400)
        
        # Save to database
        resume = Resume.objects.create(
            name=result.get('name', 'Unknown'),
            email=result.get('email', ''),
            phone=result.get('phone', ''),
            skills=result.get('skills', []),
            experience_years=result.get('experience_years', 0),
            resume_text=result.get('resume_text', '')
        )
        
        return Response({
            'message': 'Resume saved successfully',
            'id': resume.id,
            'data': result
        })


class JobRoleView(APIView):
    """Create and list job roles"""
    
    def get(self, request):
        """List all active job roles"""
        jobs = JobRole.objects.filter(status='active')
        data = [{
            'id': job.id,
            'title': job.title,
            'description': job.description,
            'required_skills': job.required_skills,
            'experience_required': job.experience_required,
            'location': job.location
        } for job in jobs]
        
        return Response({'jobs': data})
    
    def post(self, request):
        """Create new job role"""
        data = request.data
        
        job = JobRole.objects.create(
            title=data.get('title'),
            description=data.get('description'),
            required_skills=data.get('required_skills', []),
            experience_required=data.get('experience_required', 0),
            education_level=data.get('education_level', ''),
            location=data.get('location', ''),
            salary_range=data.get('salary_range', '')
        )
        
        return Response({
            'message': 'Job role created successfully',
            'id': job.id,
            'title': job.title
        })