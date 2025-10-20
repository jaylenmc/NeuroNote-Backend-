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
from .models import DFBLUserInteraction

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
                max_tokens=1000,
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
        print(f"Cleaned text: {cleaned_text}")
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

@api_view(["POST"])
def doing_feedback_loop(request):
    dfbl_interaction = DFBLUserInteraction.objects.filter(user=request.user)
    interaction_history = []
    print(f"dfbl_interaction: {dfbl_interaction}")
    print(f"interaction history: {interaction_history}")

    if dfbl_interaction.exists() and request.data.get("attempt_count") > 0:
        conversation_list = list(dfbl_interaction)

        for interaction in conversation_list:
            interaction_history.append(
                {
                    "role": "user", 
                    "content": [{
                        "type": "text", "text": f"Question: {interaction.question}\nCorrect answer: {interaction.correct_answer}\nUser answer: {interaction.user_answer}\nPrevious attempts: {interaction.attempts}"
                    }]
                }
            )
            interaction_history.append(
                {
                    "role": "assistant", 
                    "content": [{
                        "type": "text", "text": interaction.neuro_response
                        }]
                }
            )

        interaction_history.append({"role": "user", "content": [{
            "type": "text", "text": f"Question: {request.data.get("question")}\nCorrect answer: {request.data.get("correct_answer")}\nUser answer: {request.data.get("user_answer")}\nPrevious attempts: {request.data.get("attempt_count")}"
            }]})

        message = client.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=1000,
            system='''
                You are an expert tutor trained in cognitive science and deliberate practice.
                Your goal is to help the user master understanding of a concept or question by giving high-quality,
                critical feedback — without ever revealing the correct answer directly.

                Your behavior and principles:
                    1.	Never give away the correct answer.
                Instead, guide the user through reasoning, point out misconceptions, and challenge their assumptions.
                    2.	Be honest and direct.
                If the user's answer is weak, say so clearly. Never say something is “good” or “almost right” if it’s not.
                    3.	Be specific.
                Identify what exactly is wrong or missing and why it matters.
                    4.	Encourage improvement, not perfection.
                Suggest how to rethink or improve the explanation rather than repeating memorized definitions.
                    5.	Foster deep learning.
                Push the user to connect ideas, use examples, and explain reasoning, not just recall facts..
                    6. Grade the users answer
                Label this grade as "Verdict", give it the value of correct, incorrect or anything between. But have another variable called
                "grade" where you give a percentage.
            ''',
            messages=interaction_history
        )
        DFBLUserInteraction.objects.create(
            user=request.user,
            question=request.data.get("question"),
            attempts=dfbl_interaction.last().attempts + 1,
            correct_answer=request.data.get("correct_answer"),
            user_answer=request.data.get("user_answer"),
            neuro_response=message.content[0].text
        )
        return Response(message.content[0].text, status=status.HTTP_200_OK)

    dfbl_interaction.delete()
    message = client.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=1000,
            system='''
                You are an expert tutor trained in cognitive science and deliberate practice.
                Your goal is to help the user master understanding of a concept or question by giving high-quality,
                critical feedback — without ever revealing the correct answer directly.

                Your behavior and principles:
                    1.	Never give away the correct answer.
                Instead, guide the user through reasoning, point out misconceptions, and challenge their assumptions.
                    2.	Be honest and direct.
                If the user's answer is weak, say so clearly. Never say something is “good” or “almost right” if it’s not.
                    3.	Be specific.
                Identify what exactly is wrong or missing and why it matters.
                    4.	Encourage improvement, not perfection.
                Suggest how to rethink or improve the explanation rather than repeating memorized definitions.
                    5.	Foster deep learning.
                Push the user to connect ideas, use examples, and explain reasoning, not just recall facts..
                    6. Grade the users answer
                Label this grade as "Verdict", give it the value of correct, incorrect or anything between. But have another variable called
                "grade" where you give a percentage out of 100 (this is used for the backend, the user isnt meant to see this)
            ''',
            messages=[{
                "role": "user",
                "content":[{"type": "text", "text": f"Question: {request.data.get("question")}\nCorrect answer: {request.data.get("correct_answer")}\nUser answer: {request.data.get("user_answer")}\nPrevious attempts: {request.data.get("attempt_count")}"}]
            }]
    )
    DFBLUserInteraction.objects.create(
            user=request.user,
            question=request.data.get("question"),
            attempts=request.data.get("attempt_count"),
            correct_answer=request.data.get("correct_answer"),
            user_answer=request.data.get("user_answer"),
            neuro_response=message.content[0].text
        )
    return Response(message.content[0].text, status=status.HTTP_200_OK)