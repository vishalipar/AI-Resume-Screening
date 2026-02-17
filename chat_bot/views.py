from rest_framework.views import APIView
from rest_framework.response import Response
from .ai_assistant import AIAssistant

class ChatView(APIView):
    """Minimal chat endpoint"""
    def post(self, request):
        user_message = request.data.get('message', '')
        
        if not user_message:
            return Response({'error': 'Message required'}, status=400)
        
        # Get AI response
        assistant = AIAssistant()
        result = assistant.chat(user_message)
        
        return Response({
            'message': result['message'],
            'success': result['success']
        })