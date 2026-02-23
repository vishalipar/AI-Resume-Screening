from rest_framework.views import APIView
from rest_framework.response import Response
from .ai_assistant import AIAssistant
from .session_manager import get_or_create_state
from resume_parser.models import JobRole, Resume
import uuid

class ChatView(APIView):
    
    def post(self, request):
        user_message = request.data.get('message', '').strip()
        session_id = request.data.get('session_id')
        
        if not user_message:
            return Response({'error': 'Message required'}, status=400)
        
        if not session_id:
            session_id = str(uuid.uuid4())
        
        state = get_or_create_state(session_id)
        assistant = AIAssistant()
        
        # Check for "show all" or "rank all" request
        if state.stage == 'idle' and any(keyword in user_message.lower() for keyword in ['show all', 'all candidates', 'rank all', 'list all']):
    
            # Find the job mentioned
            jobs = JobRole.objects.filter(status='active')
            target_job = None
            
            for job in jobs:
                if job.title.lower() in user_message.lower():
                    target_job = job
                    break
            
            # If no job mentioned but only one exists, use it
            if not target_job and jobs.count() == 1:
                target_job = jobs.first()
            
            # If multiple jobs and none mentioned, CHANGE STATE to 'selecting_job'
            if not target_job and jobs.count() > 1:
                state.stage = 'selecting_job_for_ranking'  # NEW STATE
                job_list = '\n'.join([f"- {job.title}" for job in jobs])
                return Response({
                    'session_id': session_id,
                    'message': f"Which job role?\n\n{job_list}\n\nPlease specify the job title.",
                    'success': True
                })
            
            # If no jobs exist
            if not target_job:
                return Response({
                    'session_id': session_id,
                    'message': "No job roles found. Please create a job role first.",
                    'success': True
                })
            
            # Get all resumes
            all_resumes = Resume.objects.all()
            
            if not all_resumes.exists():
                return Response({
                    'session_id': session_id,
                    'message': "No resumes in database. Please upload resumes first.",
                    'success': True
                })
            
            # Calculate scores for all resumes
            candidates_with_scores = []
            
            for resume in all_resumes:
                match_score = assistant.calculate_match_score(resume, target_job)
                candidates_with_scores.append({
                    'id': resume.id,
                    'name': resume.name,
                    'email': resume.email,
                    'skills': resume.skills,
                    'experience_years': resume.experience_years,
                    'match_score': match_score
                })
            
            # Sort by match score (highest first)
            candidates_with_scores.sort(key=lambda x: x['match_score'], reverse=True)
            
            # Build response message
            message = f"**All Candidates for {target_job.title}** (Total: {len(candidates_with_scores)})\n\n"
            
            for i, candidate in enumerate(candidates_with_scores[:10], 1):  # Top 10
                emoji = '🥇' if i == 1 else '🥈' if i == 2 else '🥉' if i == 3 else '📄'
                message += f"{emoji} **{i}. {candidate['name']}** - {candidate['match_score']}%\n"
                message += f"   Skills: {', '.join(candidate['skills'][:3])}...\n\n"
            
            if len(candidates_with_scores) > 10:
                message += f"... and {len(candidates_with_scores) - 10} more candidates"
            
            return Response({
                'session_id': session_id,
                'message': message,
                'candidates': candidates_with_scores,  # Send full data for frontend
                'job_title': target_job.title,
                'show_on_screen': True,  # Signal to show on main screen
                'success': True
            })
        
        # Check for matching request - IMPROVED
        elif state.stage == 'idle' and any(keyword in user_message.lower() for keyword in ['match', 'score', 'calculate']):
            
            # Find the job mentioned in message
            jobs = JobRole.objects.filter(status='active')
            target_job = None
            
            # Try to find job by title in message
            for job in jobs:
                if job.title.lower() in user_message.lower():
                    target_job = job
                    break
            
            # If no job mentioned but only one exists, use it
            if not target_job and jobs.count() == 1:
                target_job = jobs.first()
            
            # If multiple jobs and none mentioned, list them
            if not target_job and jobs.count() > 1:
                state.stage = 'selecting_job_for_matching'
                job_list = '\n'.join([f"- {job.title}" for job in jobs])
                return Response({
                    'session_id': session_id,
                    'message': f"Which job role do you want to match against?\n\n{job_list}\n\nPlease specify the job title.",
                    'success': True
                })
            
            # If no jobs exist
            if not target_job:
                return Response({
                    'session_id': session_id,
                    'message': "No job roles found in database. Please create a job role first.",
                    'success': True
                })
            
            # Check if resume exists
            if not Resume.objects.exists():
                return Response({
                    'session_id': session_id,
                    'message': "No resumes uploaded yet. Please upload a resume first.",
                    'success': True
                })
            
            recent_resume = Resume.objects.last()
            
            # Calculate match
            match_score = assistant.calculate_match_score(recent_resume, target_job)
            
            message = f"""
        **Match Analysis for {recent_resume.name}:**

        **Job Role:** {target_job.title}
        **Match Score:** {match_score}%

        **Candidate Skills:** {', '.join(recent_resume.skills) if recent_resume.skills else 'None found'}
        **Required Skills:** {', '.join(target_job.required_skills)}

        **Candidate Experience:** {recent_resume.experience_years} years
        **Required Experience:** {target_job.experience_required} years

        {'✅ **Strong Match!**' if match_score >= 70 else '⚠️ **Partial Match**' if match_score >= 50 else '❌ **Weak Match**'}
            """
            
            return Response({
                'session_id': session_id,
                'message': message,
                'match_score': match_score,
                'success': True
            })
            
        # Handle job selection for matching (NEW)
        elif state.stage == 'selecting_job_for_matching':
            jobs = JobRole.objects.filter(status='active')
            target_job = None
            
            for job in jobs:
                if job.title.lower() in user_message.lower():
                    target_job = job
                    break
            
            if not target_job:
                return Response({
                    'session_id': session_id,
                    'message': "Job not found. Please enter a valid job title.",
                    'success': True
                })
            
            state.stage = 'idle'  # Reset state
    
            if not Resume.objects.exists():
                return Response({
                    'session_id': session_id,
                    'message': "No resumes uploaded yet.",
                    'success': True
                })
            
            recent_resume = Resume.objects.last()
            match_score = assistant.calculate_match_score(recent_resume, target_job)
            
            message = f"""
        **Match Analysis for {recent_resume.name}:**

        **Job Role:** {target_job.title}
        **Match Score:** {match_score}%

        **Candidate Skills:** {', '.join(recent_resume.skills) if recent_resume.skills else 'None found'}
        **Required Skills:** {', '.join(target_job.required_skills)}

        **Candidate Experience:** {recent_resume.experience_years} years
        **Required Experience:** {target_job.experience_required} years

        {'✅ **Strong Match!**' if match_score >= 70 else '⚠️ **Partial Match**' if match_score >= 50 else '❌ **Weak Match**'}
        """
    
            return Response({
                'session_id': session_id,
                'message': message,
                'match_score': match_score,
                'success': True
            })
            
        # Handle job selection for ranking (NEW)
        elif state.stage == 'selecting_job_for_ranking':
            jobs = JobRole.objects.filter(status='active')
            target_job = None
            
            # Find the job by title
            for job in jobs:
                if job.title.lower() in user_message.lower():
                    target_job = job
                    break
            
            if not target_job:
                return Response({
                    'session_id': session_id,
                    'message': "Job not found. Please enter a valid job title from the list above.",
                    'success': True
                })
    
            # Reset state
            state.stage = 'idle'
            
            # Get all resumes and calculate scores
            all_resumes = Resume.objects.all()
            
            if not all_resumes.exists():
                return Response({
                    'session_id': session_id,
                    'message': "No resumes in database.",
                    'success': True
                })
            
            candidates_with_scores = []
            for resume in all_resumes:
                match_score = assistant.calculate_match_score(resume, target_job)
                candidates_with_scores.append({
                    'id': resume.id,
                    'name': resume.name,
                    'email': resume.email,
                    'skills': resume.skills,
                    'experience_years': resume.experience_years,
                    'match_score': match_score
                })
            
            candidates_with_scores.sort(key=lambda x: x['match_score'], reverse=True)
            
            message = f"**All Candidates for {target_job.title}** (Total: {len(candidates_with_scores)})\n\n"
            for i, candidate in enumerate(candidates_with_scores[:10], 1):
                emoji = '🥇' if i == 1 else '🥈' if i == 2 else '🥉' if i == 3 else '📄'
                message += f"{emoji} **{i}. {candidate['name']}** - {candidate['match_score']}%\n"
                message += f"   Skills: {', '.join(candidate['skills'][:3])}...\n\n"
            
            return Response({
                'session_id': session_id,
                'message': message,
                'candidates': candidates_with_scores,
                'job_title': target_job.title,
                'show_on_screen': True,
                'success': True
            })
            
        # Check for job creation intent
        elif state.stage == 'idle' and any(keyword in user_message.lower() for keyword in ['create job', 'new job', 'add job']):
            state.stage = 'collecting_jd'
            return Response({
                'session_id': session_id,
                'message': "Great! Let's create a new job role. What is the job title?",
                'success': True
            })
            
        # Collecting JD information
        elif state.stage == 'collecting_jd':
            
            # Job Title
            if 'title' not in state.jd_data:
                state.jd_data['title'] = user_message
                return Response({
                    'session_id': session_id,
                    'message': "What is the job description? (You can say 'generate for me' and I'll create one)",
                    'success': True
                })
            
            # Job Description - AUTO GENERATE if requested
            elif 'description' not in state.jd_data:
                # Check if user wants AI to generate
                if any(keyword in user_message.lower() for keyword in ['generate', 'create', 'write', 'make', 'whatever', 'you decide', 'suggest']):
                    # Generate description using AI
                    generated = self._generate_jd_content(
                        state.jd_data['title'], 
                        'description'
                    )
                    state.jd_data['description'] = generated
                    
                    return Response({
                        'session_id': session_id,
                        'message': f"I've generated this description:\n\n{generated}\n\nWhat skills are required? (Say 'generate' for auto-suggestion)",
                        'success': True
                    })
                else:
                    state.jd_data['description'] = user_message
                    return Response({
                        'session_id': session_id,
                        'message': "What skills are required? (comma separated, or say 'generate for me')",
                        'success': True
                    })
            
            # Required Skills - AUTO GENERATE if requested
            elif 'required_skills' not in state.jd_data:
                if any(keyword in user_message.lower() for keyword in ['generate', 'create', 'write', 'whatever', 'suggest', 'you decide']):
                    # Generate skills using AI
                    generated_skills = self._generate_jd_content(
                        state.jd_data['title'], 
                        'skills'
                    )
                    state.jd_data['required_skills'] = [s.strip() for s in generated_skills.split(',')]
                    
                    return Response({
                        'session_id': session_id,
                        'message': f"I've suggested these skills:\n\n{generated_skills}\n\nHow many years of experience required? (type a number or 0 for freshers)",
                        'success': True
                    })
                else:
                    state.jd_data['required_skills'] = [s.strip() for s in user_message.split(',')]
                    return Response({
                        'session_id': session_id,
                        'message': "How many years of experience required? (type a number or 0 for freshers)",
                        'success': True
                    })
            
            # Experience
            elif 'experience_required' not in state.jd_data:
                try:
                    exp = int(''.join(filter(str.isdigit, user_message)))
                    state.jd_data['experience_required'] = exp
                except:
                    state.jd_data['experience_required'] = 0
                
                return Response({
                    'session_id': session_id,
                    'message': "What is the job location? (type location or 'remote' or 'skip')",
                    'success': True
                })
            
            # Location
            elif 'location' not in state.jd_data:
                if user_message.lower() != 'skip':
                    state.jd_data['location'] = user_message
                else:
                    state.jd_data['location'] = ''
                
                # Move to confirmation
                state.stage = 'confirming_jd'
                
                summary = f"""
Here's the job role summary:

📋 **Title:** {state.jd_data.get('title')}

📝 **Description:** 
{state.jd_data.get('description')}

🔧 **Required Skills:** {', '.join(state.jd_data.get('required_skills', []))}

⏱️ **Experience:** {state.jd_data.get('experience_required')} years

📍 **Location:** {state.jd_data.get('location') or 'Not specified'}

---
Do you want to save this job role? 
Reply 'yes' to confirm, 'no' to cancel, or 'edit [field]' to make changes.
                """
                
                return Response({
                    'session_id': session_id,
                    'message': summary,
                    'success': True
                })
        
        # Confirming JD
        elif state.stage == 'confirming_jd':
            if user_message.lower() in ['yes', 'confirm', 'save', 'ok']:
                job = JobRole.objects.create(
                    title=state.jd_data.get('title'),
                    description=state.jd_data.get('description'),
                    required_skills=state.jd_data.get('required_skills', []),
                    experience_required=state.jd_data.get('experience_required', 0),
                    location=state.jd_data.get('location', '')
                )
                
                state.reset()
                
                return Response({
                    'session_id': session_id,
                    'message': f"✅ Job role '{job.title}' has been saved successfully! You can now upload resumes to match against this role.",
                    'job_created': True,
                    'job_id': job.id,
                    'success': True
                })
            
            elif user_message.lower() in ['no', 'cancel']:
                state.reset()
                return Response({
                    'session_id': session_id,
                    'message': "Job creation cancelled. How else can I help you?",
                    'success': True
                })
            
            elif user_message.lower().startswith('edit'):
                return Response({
                    'session_id': session_id,
                    'message': "Which field would you like to edit? (title, description, skills, experience, location)",
                    'success': True
                })
            
            else:
                return Response({
                    'session_id': session_id,
                    'message': "Please reply 'yes' to save or 'no' to cancel.",
                    'success': True
                })
          
        # Normal chat
        else:
            result = assistant.chat(user_message)
            
            return Response({
                'session_id': session_id,
                'message': result['message'],
                'success': result['success']
            })
    
    def _generate_jd_content(self, job_title, content_type):
        """Use AI to generate JD content"""
        assistant = AIAssistant()
        
        if content_type == 'description':
            prompt = f"""Write a professional job description for '{job_title}' role suitable for freshers. 
Include responsibilities and what the candidate will learn. Keep it concise (3-4 sentences).
Only return the description, nothing else."""
            
        elif content_type == 'skills':
            prompt = f"""List the essential technical skills required for a '{job_title}' position for freshers.
Return ONLY comma-separated skills (e.g., Python, Django, SQL). Maximum 6 skills.
Only return the skills list, nothing else."""
        
        result = assistant.chat(prompt)
        return result['message'].strip()