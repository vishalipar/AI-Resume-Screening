from rest_framework.views import APIView
from rest_framework.response import Response
from .ai_assistant import AIAssistant
from resume_parser.models import JobRole
import re

class ChatView(APIView):
    """Minimal chat endpoint"""
    def post(self, request):
        user_message = request.data.get('message', '')
        
        if not user_message:
            return Response({'error': 'Message required'}, status=400)
            
        # Check if user wants to create a job
        if 'create job' in user_message.lower() or 'new job' in user_message.lower():
            return self.handle_job_creation(user_message)
        
        # Get AI response
        assistant = AIAssistant()
        result = assistant.chat(user_message)
        
        return Response({
            'message': result['message'],
            'success': result['success']
        })
        
    def handle_job_creation(self, message):
        """Extract job details and create job"""
        
        # Simple extraction (you can make this smarter)
        assistant = AIAssistant()
        
        # Ask AI to extract details
        extraction_prompt = f"""Extract job details from this message: "{message}"
        
Return in this format:
Title: [job title]
Skills: [comma separated skills]
Experience: [number] years

If not clear, ask for clarification."""
        
        result = assistant.chat(extraction_prompt)
        
        return Response({
            'message': result['message'],
            'action': 'job_creation',
            'success': True
        })