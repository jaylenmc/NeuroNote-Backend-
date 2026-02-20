import anthropic
import re
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from flashcards.models import Card, Deck
from datetime import date
from .services import clean_claude_response, validate_dfbl_response, validate_quiz_generation
from rest_framework.decorators import permission_classes, api_view
import json
import tiktoken
import os
from .models import DFBLUserInteraction, UPSUserInteraction
from .serializers import DFBLSerializer, TestGenerator

client = anthropic.Anthropic(
    api_key=os.environ.get("ANTHROPIC_KEY")
) 
print(f"---------------------------------- Client: {client.api_key} ----------------------------------")

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
    
# ------------------------------------------------ Quiz Generator ------------------------------------------------
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_quiz(request):
    serializer = TestGenerator(data=request.data) 
    serializer.is_valid(raise_exception=True)
    validated_data = serializer.validated_data

    prompt = f"""
    Make a quiz about: {validated_data.get('user_prompt')}.
    With the preferred quiz type as {validated_data.get("preferred_quiz_type", "written/multiple choice")}.
    Create this quiz with {validated_data.get("question_num", "5")} number of questions.
    """

    try:
        message = client.messages.create(
            model = "claude-sonnet-4-6",
            max_tokens=5000,
            temperature = 1,
            system = """
            You are a professor who's making a quiz for their student that challenges and pushes them to their limits,

            1. Always produce exactly the number of questions requested.
            2. Only return valid JSON, no quotes, no explanations.
            3. Quiz types:
                - mc = multiple choice
                - wr = written
                - wrmc = both
            4. Multiple choice answers must have at least 3 options.
            5. Multiple choice answers must include 'is_correct' exactly "True" or "False".
            6. Written questions must include the key 'answer'.

            Expected JSON response format:
            {
                "quiz_title": "insert title",
                "quiz_subject": "insert subject of quiz",
                "quiz_type": "mc or wr or wrmc",
                "questions": [
                    {
                        "question": "insert question",
                        "answer (if wr (written) question type)": "insert answer",
                        "question_type": "wr"
                    },
                    {
                        "question": "insert question",
                        "answers (if mc (multiple choice) question type)": [
                            {"answer": "insert answer", "is_correct": "True or False"},
                            {"answer": "insert answer", "is_correct": "True or False"},
                            {"answer": "insert answer", "is_correct": "True or False"},
                            ...
                        ],
                        "question_type": "mc"
                    }, ...
            }

            """,
            messages = [
                {'role': 'user', 'content': prompt}
            ]
        )
        response = validate_quiz_generation(message.content[0].text)
        merged_data = {**validated_data, **response}
        serialized = TestGenerator(data=merged_data, context={"user": request.user})
        serialized.is_valid(raise_exception=True)
        serialized.save()
        return Response(serialized.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"Error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

# ------------------------------------------------ Doing + Feedback Loop ------------------------------------------------

class DoingFeedbackLoop(APIView):
    def get(self, request, card_id): 
        dfbl_interaction = DFBLUserInteraction.objects.filter(user=request.user, card_id=card_id)

        if dfbl_interaction.exists():
            return Response(dfbl_interaction.last().attempts, status=status.HTTP_200_OK)
        
        return Response({"attempts: 1"}, status=status.HTTP_200_OK)

    def post(self, request, card_id=None):
        dfbl_serializer = DFBLSerializer(data=request.data, context={"request": request})

        if not dfbl_serializer.is_valid():
            return Response({'Message': dfbl_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        validated_data = dfbl_serializer.validated_data
        card = Card.objects.filter(id=validated_data.get("card").id)

        if not card:
            return Response({'Message': 'Card not found'}, status=status.HTTP_400_BAD_REQUEST)

        card_instance = card.first()
        tutor_style_descriptions = {
            "strict": "A no-nonsense tutor who challenges you and pushes you hard.",
            "friendly": "A warm, casual tutor who explains things gently and encourages you.",
            "professional": "A polished, classroom-style instructor with clear reasoning.",
            "speed_run": "Fast-paced, optimized explanations focusing on efficiency.",
            "socratic": "A question driven tutor that guides you to discover the answer.",
            "supportive": "A motivational guide who reassures you and celebrates progress."
        }

        if validated_data.get("layer") == 1:
            system = f"""
                You are an AI study tutor. Adopt the following tutor style: {tutor_style_descriptions.get(validated_data.get("tutor_style"))}

                Layer 1 - Recognition: The user must identify what the question refers to when prompted, without needing detail, structure, or justification.

                What a good answer looks like
                •	Short
                •	Informal is fine
                •	Names or points to the concept correctly
                •	No explanation required

                CRITICAL:
                - If you give examples and the user uses one of the examples as an answer mark you must Fail them.
                - If you dont live up to the tutor style you adopt, your response is invalid and must be regenerated.

                Your goal:
                - Judge whether the user understands the core idea.

                Evaluate the user's answer to:
                "{card_instance.question}"

                User's answer:
                "{validated_data.get('user_answer')}"

                ABSOLUTE OUTPUT RULES (NON-NEGOTIABLE):
                - Output MUST be valid JSON
                - Output MUST start with '{' and end with '}'
                - NO markdown
                - NO backticks
                - NO commentary outside JSON
                - ONLY the keys: "feedback" and "decision"
                - Values MUST be strings
                - HTML is allowed ONLY inside string values
                - If rules are broken, regenerate internally until valid
                - Wrap the response in single quotes

                Allowed HTML tags in feedback:
                - <main>
                - <p>
                - <strong>
                - <h1>, <h2>, <h3>, <h4>, <h5>, <h6>
                - <ul>
                - <ol>
                - <li>
                - <a>
                - <img>
                - <br>
                - <hr>
                - <blockquote>
                - <div>
                - <span>
                - <table>
                - <thead>
                - <tbody>
                - <tfoot>
                - <tr>
                - <th>
                - <td>
                - <code> (for code blocks)

                OUTPUT FORMAT (EXACT):
                {{"feedback": "<main>...</main>","decision": "<Pass or Fail>"}}

                Feedback:
                - Teach the topic a little, base the teaching off the tutor style you adopt. 
                - Do NOT give the correct answer.
            """

        elif validated_data.get("layer") == 2:
            system = f"""
                You are an AI study tutor. Adopt the following style: {tutor_style_descriptions.get(validated_data.get("tutor_style"))}

                CRITICAL:
                - If you dont live up to the tutor style you adopt, your response is invalid and must be regenerated.
                - If you give examples and the user uses one of the examples as an answer mark you must Fail them.

                Layer 2 – Structure: The user must explain the essential parts or rules that make the concept what it is.
                
                What a good answer looks like
                •	Mentions key components
                •	Describes what must exist for the concept to work
                •	Still concise, but more detailed than Recognition

                Your goal:
                - Go deeper into the concept.
                - Introduce key details, reasoning, or underlying mechanisms.
                - Keep it concise; avoid overwhelming the user.

                Evaluate the user's answer to: "{card_instance.question}"
                User's answer: "{validated_data.get('user_answer')}"

                ABSOLUTE OUTPUT RULES (NON-NEGOTIABLE):
                - Output MUST be valid JSON
                - Output MUST start with '{' and end with '}'
                - NO markdown
                - NO backticks
                - NO commentary outside JSON
                - ONLY the keys: "feedback" and "decision"
                - Values MUST be strings
                - HTML is allowed ONLY inside string values
                - If rules are broken, regenerate internally until valid
                - Wrap the response in single quotes

                Allowed HTML tags in feedback:
                - <main>
                - <p>
                - <strong>
                - <h1>, <h2>, <h3>, <h4>, <h5>, <h6>
                - <ul>
                - <ol>
                - <li>
                - <a>
                - <img>
                - <br>
                - <hr>
                - <blockquote>
                - <div>
                - <span>
                - <table>
                - <thead>
                - <tbody>
                - <tfoot>
                - <tr>
                - <th>
                - <td>
                - <code> (for code blocks)

                OUTPUT FORMAT (EXACT):
                {{"feedback": "<main>...</main>","decision": "<Pass or Fail>"}}

                Feedback:
                - Layer 2 explanation focusing on the structure of the concept, base the explanation off the tutor style you adopt.
                - Contrast explanation for common misconceptions
            """

        else:
            system = f"""
                You are an AI study tutor. Adopt the following style: {tutor_style_descriptions.get(validated_data.get("tutor_style"))}

                Layer 3 – Implication: Reasoning about what follows from the concept being true — consequences, effects, or constraints.

                CRITICAL:
                - If you dont live up to the tutor style you adopt, your response is invalid and must be regenerated.
                - If you give examples and the user uses one of the examples as an answer mark you must Fail them.

                What a good answer looks like
                •	Uses cause -> effect reasoning
                •	Explains what the concept enables or limits
                •	May reference outcomes, tradeoffs, or behavior

                Your goal:
                - Know this is the most important layer because its where connections are made. Make sure the user has a strong answer.

                Evaluate the user's answer to: "{card_instance.question}"
                User's answer: "{validated_data.get('user_answer')}"

                ABSOLUTE OUTPUT RULES (NON-NEGOTIABLE):
                - Output MUST be valid JSON
                - Output MUST start with '{' and end with '}'
                - NO markdown
                - NO backticks
                - NO commentary outside JSON
                - ONLY the keys: "feedback" and "decision"
                - Values MUST be strings
                - HTML is allowed ONLY inside string values
                - If rules are broken, regenerate internally until valid
                - Wrap the response in single quotes

                Allowed HTML tags in feedback:
                - <main>
                - <p>
                - <strong>
                - <h1>, <h2>, <h3>, <h4>, <h5>, <h6>
                - <ul>
                - <ol>
                - <li>
                - <a>
                - <img>
                - <br>
                - <hr>
                - <blockquote>
                - <div>
                - <span>
                - <table>
                - <thead>
                - <tbody>
                - <tfoot>
                - <tr>
                - <th>
                - <td>
                - <code> (for code blocks)

                OUTPUT FORMAT (EXACT):
                {{"feedback": "<main>...</main>","decision": "<Pass or Fail>"}}

                Feedback:
                - Layer 3 explanation focusing on the implication of the concept, base the explanation off the tutor style you adopt.
                - Contrast explanation for common misconceptions
            """

        dfbl_interaction = DFBLUserInteraction.objects.filter(user=request.user).order_by('created_at')
        interaction_history = []

        if dfbl_interaction.exists():

            if card_instance.question.lower() == dfbl_interaction.last().card.question.lower() and dfbl_interaction.last().layer == validated_data.get('layer'):

                validated_data['attempts'] = dfbl_interaction.last().attempts + 1

                for interaction in dfbl_interaction:
                    interaction_history.append({
                        'role': 'user',
                        'content': [{
                            'type': 'text',
                            'text': f"Question: {interaction.card.question}\nCorrect answer: {interaction.card.answer}\nUser answer: {interaction.user_answer}\nCurrent attempt: {validated_data['attempts']}"
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
                validated_data['attempts'] = 1
                dfbl_interaction.delete()
        else:
            validated_data['attempts'] = 1

        interaction_history.append({
                'role': 'user',
                'content': [{
                    'type': 'text',
                    'text': f"Question: {card_instance.question}\nCorrect answer: {card_instance.answer}\nUser answer: {validated_data.get('user_answer')}\nCurrent attempt: {validated_data['attempts']}"
                }]
            })

        message = client.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=3000,
            system=system,
            messages=interaction_history
        )
        validated_response = validate_dfbl_response(message.content[0].text)
        if isinstance(validated_response, ValueError):
            return Response({"Message": "Feedback not formatted properly, try again"}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        validated_data['neuro_response'] = validated_response['feedback']
        dfbl_serializer.save(validated_data=validated_data)

        return Response(message.content[0].text, status=status.HTTP_200_OK)

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