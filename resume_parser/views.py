from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser
from .parser import ResumeParser

class ResumeUploadView(APIView):
    parser_classes = (MultiPartParser,)
    
    def post(self, request):
        resume_file = request.FILES.get('resume')
        
        if not resume_file:
            return Response({'error': 'Resume file required'}, status=400)
        
        # Parse resume
        parser = ResumeParser()
        result = parser.parse_resume(resume_file, resume_file.name)
        
        if 'error' in result:
            return Response({'error': result['error']}, status=400)
        
        return Response({
            'message': 'Resume parsed successfully',
            'data': result
        })