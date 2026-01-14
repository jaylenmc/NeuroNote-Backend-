import re
import json

def clean_claude_response(content):
    if isinstance(content, list) and hasattr(content[0], 'text'):
        raw_text = content[0].text
    else:
        return {"Error": "Unsupported content format"}

    # Extract JSON code blocks
    json_blocks = re.findall(r'```json\n(.*?)\n```', raw_text, re.DOTALL)

    # Parse each block
    parsed = []
    for block in json_blocks:
        try:
            parsed.append(json.loads(block))
        except json.JSONDecodeError as e:
            print(f"Failed to parse: {e}\n{block}")
    
    return parsed

def validate_dfbl_response(response):
    try:
        response = response.strip()
        if response.startswith("'") and response.endswith("'"):
            response = response[1:-1]
        response = response.replace("\\'", "'")
        data = json.loads(response)
    except json.JSONDecodeError:
        raise ValueError("Feedback not formatted properly")

    if "feedback" not in data or "decision" not in data:
        print(f"Data: {data}")
        raise ValueError("feedback and/or decision keys not found in response")
    
    if data['decision'] not in ["Pass", "Fail"]:
        print(f"Data: {data['decision'] == "Fail"}")
        raise ValueError("Pass and/or Fail not found in decision")

    if not data['feedback'].startswith("<main>") and not data['feedback'].endswith("</main"):
        print(f"Data: {data['feedback']}")
        raise ValueError("Feedback doesn't start or end with <main> tag")

    tags = re.findall(r"</?([a-z]+)>", data['feedback'])
    allowed_tags = [
        "main", "p", "strong", "h1", "h2", "h3", "h4", "h5", "h6", "ul", "ol", "li", "a", "img", 
        "br", "hr", "blockquote", "div", "span", "table", "thead", "tbody", "tfoot", "tr", "th", 
        "td", "code"
        ]
    
    for tag in tags:
        if tag not in allowed_tags:
            raise ValueError("Missing or invalid HTML tag")

    return data

def validate_quiz_generation(quiz_response):
    try:
        response = quiz_response.strip()
        if response.startswith("'") and response.endswith("'"):
            response = response[1:-1]
        json_response = json.loads(response)
    except json.JSONDecodeError:
        raise ValueError("Quiz not formatted properly")
    
    if not all([key for key in ['quiz_title', 'quiz_subject', 'quiz_type', 'questions'] if key in json_response]):
        raise ValueError("Missing required keys in response")
    
    if not json_response['quiz_title']:
        json_response['quiz_title'] = "Generated Quiz"
    
    if not json_response['quiz_subject']:
        json_response['quiz_subject'] = 'Untitled'

    if not json_response['quiz_type']:
        raise ValueError("Quiz type not provided")
    
    for q, i in enumerate(json_response['questions']):
        if not q['question']:
            raise ValueError(f"Question {i} missing a question value")
        
        if not q['question_type']:
            raise ValueError(f"Question {i} is missing 'question type' value")

        if q['question_type'] == 'wr':
            if not q['answer']:
                raise ValueError(f"Question {i} is missing answer value")
        elif q['question_type'] == 'mc':
            if not q['answers']:
                raise ValueError(f"Question {i} is missing 'answers' key")
            
            for a in q['answers']:
                if not a['answer']:
                    raise ValueError(f"'answer' value is missing for an answer in question {i}'")

                if not a['is_correct']:
                    raise ValueError(f"'is_correct' value is missing for an answer in question {i}")
    
    return json_response