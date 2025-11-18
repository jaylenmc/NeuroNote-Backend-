import anthropic
import re
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from flashcards.models import Card, Deck
from datetime import date
from .services import clean_claude_response
from rest_framework.decorators import permission_classes, api_view
import json
import tiktoken
import os
from .models import DFBLUserInteraction, UPSUserInteraction
from .serializers import UPSSerializer

client = anthropic.Anthropic(
    api_key=os.environ.get("ANTHROPIC_KEY")
) 

def thinker_ai(prompt: str, user: object):
    if user.token_amount <= 0:
        return f"Not enough tokens"

    message = client.messages.create(
    model="claude-3-7-sonnet-20250219",
    max_tokens=user.token_amount,
    temperature=1,
    system="You are a educational tutor, only asnwer to educational questions.",
    messages=[
            {
                "role": "user",
                "content": [{"type": "text", "text": prompt}]
            }
        ]
    )
    
    user.token_amount -= (message.usage.output_tokens + message.usage.input_tokens)
    user.save()
   
    return message.content

class NoteTakerAi(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        prompt = request.data.get('prompt')

        try:
            message = client.messages.create(
                model="claude-3-haiku-20240307",  # Using the free model
                max_tokens=1000,
                temperature=0.7,
                system="You are a educational tutor. Provide clear and concise answers.",
                messages=[
                    {
                        "role": "user",
                        "content": [{"type": "text", "text": prompt}]
                    }
                ]
            )
            raw_output = message.content

            # Extract only text blocks
            text_only = " ".join(
                block.text for block in raw_output if block.type == "text"
            )
    
            return Response({'Message': text_only}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'Error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
class CardsGen(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        prompt = request.data.get('prompt')
        deck_id = request.data.get('deck_id')
        if not prompt:
            return Response({'Error': 'Prompt is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            message = client.messages.create(
                model="claude-3-7-sonnet-20250219",
                max_tokens=10000,
                temperature=0.7,
                system="Generate a list of flashcards based on the prompt. Each card should be separated by '## Card', and each card should follow this format:\n## Card\n**Front**: <front>\n**Back**: <back>. Just respond with the flashcards, no other text.",
                messages=[
                    {
                        "role": "user",
                        "content": [{"type": "text", "text": prompt}]
                    }
                ]
            )

            raw_output = message.content
            text_output = "".join(
                block.text for block in raw_output if getattr(block, 'type', "") == 'text'
            )


            cards = []
            pattern = re.compile(
                r"## Card\s*\d*\s*\*\*Front\*\*:\s*(.+?)\s*\n\*\*Back\*\*:\s*((?:.|\n)*?)(?=\n## Card|\Z)",
                re.MULTILINE
            )
            matches = pattern.findall(text_output)

            for front, back in matches:
                cards.append({
                    'front': front.strip(),
                    'back': back.strip()
                })
            
            for card in cards:
                Card.objects.create(
                    question=card['front'],
                    answer=card['back'],
                    card_deck=Deck.objects.filter(id=deck_id).first(),
                    scheduled_date=date.today()
                )

            return Response({'Cards': cards}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'Error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_quiz(request):
    prompt = request.data.get('prompt')
    if not prompt:
        return Response({'Message': 'Requires prompt'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        message = client.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=1000,
            temperature=0.7,
            system = """Generate a quiz with as many multiple choice questions as needed based on the user’s prompt.
            Format each question as JSON in the following structure:
            {
            "questions": [
                {
                "question": "What is Django?",
                "answer_type": "mc",
                "choices": [
                    {"text": "A JavaScript framework", "is_correct": false},
                    {"text": "A Python web framework", "is_correct": true},
                    {"text": "A database management system", "is_correct": false},
                    {"text": "A front-end design tool", "is_correct": false}
                ]
                }
            ]
            }
            Return only the JSON object. No explanations or extra text. And make sure nothings has missing values/information""",
            messages=[
                {
                    "role": "user",
                    "content": [{"type": "text", "text": prompt}]
                }
            ]
        )
        # encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
        raw_output = message.content
        text_output = "".join(
            block.text for block in raw_output if getattr(block, 'type', "") == 'text'
        )

        cleaned_text = text_output.strip()

        if cleaned_text.startswith("```json"):
            cleaned_text = cleaned_text[len("```json"):].strip()

        if cleaned_text.endswith("```"):
            cleaned_text = cleaned_text[:-3].strip()
        data = json.loads(text_output)

        return Response(data, status=status.HTTP_200_OK)
    except Exception as e:
            return Response({'Error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
def cards_to_quiz(user_answers):
    if not user_answers:
        return {'Error': 'No data provided'}
    
    prompt_text = "\n\n".join(
        f"Question: {user['question_input']}\n"
        f"User answer: {user['answers']['user_answer']}\n"
        f"Correct answer: {user['answers']['correct']}"
        for user in user_answers
    )
    
    try:
        message = client.messages.create(
            model = "claude-3-7-sonnet-20250219",
            max_tokens=1000,
            temperature=0.7,
            system=("Grade the user's answers to the flashcards based on the correct written answers. "
                "Return the response in JSON format in the following format with score being either Correct or Incorrect: "
                "{'question_input': '...', 'score': 'Correct' or 'Incorrect', 'explanation': '...', 'user_answer': '...', 'correct_answer': '...'} — do not reference the user. "
                "Make sure each explanation clearly matches its question."
                "Make as many flashcards as needed to cover everything in the prompt, dont hold back on the number of flashcards"
            ),
            messages=[
                {
                    "role": "user",
                    "content": [{"type": "text", "text": prompt_text}]
                }
            ]
        )

        cleaned_response = clean_claude_response(message.content)
        return cleaned_response
    except Exception as e:
        return {'Error': str(e)}

# ------------------------------------------------ Doing + Feedback Loop ------------------------------------------------

@api_view(["POST"])
def doing_feedback_loop(request):
    ups_serializer = UPSSerializer(data=request.data, context={"request": request})
    if not ups_serializer.is_valid():
        return Response({'Message': ups_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    validated_data = ups_serializer.validated_data
    card = Card.objects.filter(id=validated_data.get("card").id)
    if not card:
        return Response({'Message': 'Card not found'}, status=status.HTTP_400_BAD_REQUEST)
    card_instance = card.first()

    tutor_style_descriptions = {
        "strict": "A no-nonsense tutor who challenges you and pushes you hard.",
        "friendly": "A warm, casual tutor who explains things gently and encourages you.",
        "professional": "A polished, classroom-style instructor with clear reasoning.",
        "speed_run": "Fast-paced, optimized explanations focusing on efficiency.",
        "socratic": "A question-driven tutor that guides you to discover the answer.",
        "supportive": "A motivational guide who reassures you and celebrates progress."
    }

    if validated_data.get("layer") == 1:
        system = f"""
            You are an AI study tutor. Adopt the following style: {tutor_style_descriptions.get(validated_data.get("tutor_style"))}

            Layer 1 – Quick Definition:
            Your goal:
            - Give a **short, super simple explanation** of the concept.
            - Focus on defining the term or idea in the most basic way possible.
            - Avoid details, examples, or metaphors unless absolutely necessary.

            Now evaluate the user's answer to: "{card_instance.question}"
            User's answer: "{validated_data.get('userAnswer')}"
            Correct Answer: "{card_instance.answer}"

            Provide:
            - Feedback (clarity, correctness, completeness)
            - A 1–2 sentence “Correct Answer (short version)”
            - A simple Layer 1 explanation
            - Decision: move to Layer 2 or stay at Layer 1
        """

    elif validated_data.get("layer") == 2:
        system = f"""
            You are an AI study tutor. Adopt the following style: {tutor_style_descriptions.get(validated_data.get("tutor_style"))}

            Layer 2 – Deeper Concept:
            Your goal:
            - Go deeper into the concept.
            - Explain not just *what* it is but *how* it works and *why* it matters.
            - Introduce key details, reasoning, or underlying mechanisms.
            - Keep it concise; avoid overwhelming the user.

            Evaluate the user's answer to: "{card_instance.question}"
            User's answer: "{validated_data.get('userAnswer')}"
            Correct Answer: "{card_instance.answer}"

            Provide:
            - Feedback (clarity, correctness, completeness)
            - A concise “Correct Answer (medium version)”
            - Layer 2 explanation focusing on how/why the concept works
            - Contrast explanation for common misconceptions
            - Decision: move to Layer 3, stay at Layer 2, or fallback to Layer 1
        """

    else:
        system = f"""
            You are an AI study tutor. Adopt the following style: {tutor_style_descriptions.get(validated_data.get("tutor_style"))}

            Layer 3 – Applied Example:
            Your goal:
            - Apply the concept to a real scenario, analogy, or problem.
            - Show how the concept works in practice or why understanding it matters.
            - Provide a concrete example that clarifies the idea.

            Evaluate the user's answer to: "{card_instance.question}"
            User's answer: "{validated_data.get('userAnswer')}"
            Correct Answer: "{card_instance.answer}"

            Provide:
            - Feedback (clarity, correctness, completeness)
            - “Correct Answer (applied version)” showing deeper understanding
            - Layer 3 explanation with real-world example and applied reasoning
            - Comparison-based correction if the user is confused
            - Decision: indicate whether the user has mastered the card or should return to a previous layer
            - Decision: move to Layer 4 or stay at Layer 3
        """

    dfbl_interaction = DFBLUserInteraction.objects.filter(user=request.data.get("user")).order_by('created_at')
    interaction_history = []
    if dfbl_interaction.exists():
        if card_instance.question.lower() == dfbl_interaction.last().question.lower():
            print(f'card instance question: {card_instance.question}')
            
            for interaction in dfbl_interaction:
                interaction_history.append({
                    'role': 'user',
                    'content': [{
                        'type': 'text',
                        'text': f"Question: {card_instance.question}\nCorrect answer: {card_instance.correct_answer}\nUser answer: {interaction.user_answer}\nCurrent attempt: {interaction.attempts}"
                    }]
                })
                interaction_history.append({
                    'role': 'assistant',
                    'content': [{
                        'type': 'text',
                        'text': interaction.neuro_response
                    }]
                })
        else:
            dfbl_interaction.delete()

    interaction_history.append({
            'role': 'user',
            'content': [{
                'type': 'text',
                'text': f"Question: {validated_data.get('question')}\nCorrect answer: {validated_data.get('correct_answer')}\nUser answer: {validated_data.get('user_answer')}\nCurrent attempt: {validated_data.get('attempt_count')}"
            }]
        })

    message = client.messages.create(
        model="claude-3-7-sonnet-20250219",
        max_tokens=3000,
        system=system,
        messages=interaction_history
    )
    validated_data['neuro_response'] = message.content[0].text
    ups_serializer.save(validated_data=validated_data)

    return Response(message.content[0].text, status=status.HTTP_200_OK)

    # dfbl_interaction.delete()
    # message = client.messages.create(
    #         model="claude-3-7-sonnet-20250219",
    #         max_tokens=1000,
    #         system='''
    #             You are an expert tutor trained in cognitive science and deliberate practice.
    #             Your goal is to help the user master understanding of a concept or question by giving high-quality,
    #             critical feedback — without ever revealing the correct answer directly.

    #             Your behavior and principles:
    #                 1.	Never give away the correct answer.
    #             Instead, guide the user through reasoning, point out misconceptions, and challenge their assumptions.
    #                 2.	Be honest and direct.
    #             If the user's answer is weak, say so clearly. Never say something is “good” or “almost right” if it’s not.
    #                 3.	Be specific.
    #             Identify what exactly is wrong or missing and why it matters.
    #                 4.	Encourage improvement, not perfection.
    #             Suggest how to rethink or improve the explanation rather than repeating memorized definitions.
    #                 5.	Foster deep learning.
    #             Push the user to connect ideas, use examples, and explain reasoning, not just recall facts..
    #                 6. Grade the users answer
    #             Label this grade as "Verdict", give it the value of correct, incorrect or anything between. But have another variable called
    #             "grade" where you give a percentage.
    #         ''',
    #         messages=[{
    #             "role": "user",
    #             "content":[{"type": "text", "text": f"Question: {request.data.get("question")}\nCorrect answer: {request.data.get("correct_answer")}\nUser answer: {request.data.get("user_answer")}\nPrevious attempts: {request.data.get("attempt_count")}"}]
    #         }]
    # )
    # DFBLUserInteraction.objects.create(
    #         user=request.user,
    #         question=request.data.get("question"),
    #         attempts=request.data.get("attempt_count"),
    #         correct_answer=request.data.get("correct_answer"),
    #         user_answer=request.data.get("user_answer"),
    #         neuro_response=message.content[0].text
    #     )
    # return Response(message.content[0].text, status=status.HTTP_200_OK)

# ------------------------------------------------ Understanding + Problem Solving ------------------------------------------------

@api_view(["POST"])
def understand_problem_solving(request):
    if request.query_params.get('type') == 'explain':
        explain_serializer = UPSSerializer(data=request.data, context={"user": request.user, "type": "explain"})
        if not explain_serializer.is_valid():
            return Response({"Message": explain_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        ups_user_interaction = DFBLUserInteraction.objects.filter(user=request.user)
        interaction_history = []

        if ups_user_interaction.exists():
            if ups_user_interaction.last().question != explain_serializer.validated_data.get("question"):
                ups_user_interaction.delete()
            else:
                # Only add to history if there's a valid neuro_response
                for interaction in ups_user_interaction:
                    if interaction.neuro_response:  # Check if neuro_response is not empty
                        interaction_history.append(
                            {
                                'role': 'user',
                                'content': [{
                                    'type': 'text',
                                    'text': f"Question: {interaction.question}\nExplanation: {interaction.explanation}"
                                }]
                            }
                        )
                        interaction_history.append(
                            {
                                'role': 'assistant',
                                'content': [{
                                    'type': 'text',
                                    'text': interaction.neuro_response
                                }]
                            }
                        )
        interaction_history.append({
            'role': 'user',
            'content': [{
                'type': 'text',
                'text': f"Question: {explain_serializer.validated_data.get("question")}\nExplanation: {explain_serializer.validated_data.get("explanation")}"
            }]
        })
        message = client.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=1000,
            system='''
            You are an expert educator and communication coach. Your task is to grade a student’s explanation of a concept based 
            on how clearly, accurately, and simply they can explain it to a 10-year-old child.
            1.	Clarity (0–4 points):
            •	Uses simple, everyday language
            •	Avoids unnecessary jargon
            •	Sentences are easy to follow
            2.	Accuracy (0–3 points):
            •	Explanation is factually correct
            •	Doesn’t oversimplify in a misleading way
            •	Captures the main idea correctly
            3.	Engagement & Analogy (0–2 points):
            •	Uses relatable examples, comparisons, or metaphors appropriate for a 10-year-old
            •	Keeps a friendly, curious tone
            4.	Completeness (0–1 point):
            •	Includes all key parts of the concept at a basic level
            5. Grade the user's answer on a scale of 0 to 10

        OUTPUT FORMAT:
            •	Score: [total score]
            •	Strengths: [briefly describe what they did well]
            •	Improvements: [briefly describe what to improve]
            •	Suggested improved version (optional): [rewrite their explanation in a more 10-year-old friendly way]
            ''',
            messages=interaction_history
        )

        # Save the interaction with the neuro_response
        DFBLUserInteraction.objects.create(
            user=request.user,
            question=explain_serializer.validated_data.get("question"),
            explanation=explain_serializer.validated_data.get("explanation"),
            neuro_response=message.content[0].text
        )
        return Response(message.content[0].text, status=status.HTTP_200_OK)
    
    elif request.query_params.get('type') == 'connection':
        connection_serializer = UPSSerializer(data=request.data, context={"user": request.user, "type": "connection"})
        if not connection_serializer.is_valid():
            return Response({"Message": connection_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        
        ups_user_interaction = DFBLUserInteraction.objects.filter(user=request.user)
        interaction_history = []
        if ups_user_interaction.exists():
            # Update the model with the question from first user attempt
            interaction_history.append(
                    {
                        'role': 'user',
                        'content': [{
                            'type': 'text',
                            'text': f"Question: {ups_user_interaction.first().question}\nExplanation: {ups_user_interaction.first().explanation}"
                        }]
                    }
                )
            for interaction in ups_user_interaction:
                # Only add to history if solution_summary exists and neuro_response is not empty
                if interaction.solution_summary and interaction.neuro_response:
                    interaction_history.append(
                        {
                            'role': 'user',
                            'content': [{
                                'type': 'text',
                                'text': f"Principles: {interaction.principles}\nSolution Summary: {interaction.solution_summary}"
                            }]
                        }
                    )
                    interaction_history.append(
                        {
                            'role': 'assistant',
                            'content': [{
                                'type': 'text',
                                'text': interaction.neuro_response
                            }]
                        }
                    )

        interaction_history.append({
            'role': 'user',
            'content': [{
                'type': 'text',
                'text': f"Principles: {connection_serializer.validated_data.get('principles')}\nSolution Summary: {connection_serializer.validated_data.get('principles')}"
            }]
        })
        message = client.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=1000,
            system='''
            You are an expert educator and communication coach. Your task is to grade a student’s
            principles and solutions on not only how they are connected to one another, but
            how they are related to the problem. You should give a grade based on the quality
            of the connection and the relevance to the problem. When scoring give either a pass
            or fail. If the user fails, give a detailed explanation of why they failed. This is a follow up question
            after the user answered the question with a explanation (explain the answer like your explaining to a 10-year-old child).
            
            OUTPUT FORMAT:
            •	Score: [total score]
            •	Strengths: [briefly describe what they did well]
            •	Improvements: [briefly describe what to improve]
            ''',
            messages=interaction_history
        )
        
        # Save the interaction with the neuro_response
        # Get question from previous interaction (should exist from explain step)
        question_text = ""
        if ups_user_interaction.exists():
            question_text = ups_user_interaction.first().question
        
        DFBLUserInteraction.objects.create(
            user=request.user,
            question=question_text,
            principles=connection_serializer.validated_data.get('principles'),
            solution_summary=connection_serializer.validated_data.get('solution_summary'),
            neuro_response=message.content[0].text
        )
        return Response(message.content[0].text, status=status.HTTP_200_OK)
    else:
        return Response({'Error': 'Invalid type'}, status=status.HTTP_400_BAD_REQUEST)