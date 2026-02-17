from groq import Groq
from django.conf import settings

client = Groq(api_key=settings.GROQ_API_KEY)

class AIAssistant:
    def chat(self, user_message):
        try:
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",  # Free model
                messages=[
                    {
                        "role": "system",
                        "content": "You are an HR assistant helping to find candidates. Be helpful and concise. Dont give answers if the questions are not related to the hr work or resume work, just say to ask to related questions."
                    },
                    {
                        "role": "user",
                        "content": user_message
                    }
                ],
                max_tokens=300
            )

            return {
                'message': response.choices[0].message.content,
                'success': True
            }

        except Exception as e:
            return {
                'message': f"Error: {str(e)}",
                'success': False
            }