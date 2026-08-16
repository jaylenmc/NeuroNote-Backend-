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

def validate_quiz_generation(response):
    print(response.startswith("```json"), response.endswith("```"))
    try:
        if response.startswith("```json") and response.endswith("```"):
            response = response[7:-3]
        print(response)
        json_response = json.loads(response)
    except json.JSONDecodeError:
        raise ValueError("Quiz not formatted properly")
    
    if not all([key in json_response for key in ['quiz_title', 'quiz_subject', 'quiz_type', 'questions']]):
        raise ValueError("Missing required keys in response")
    
    if not json_response['quiz_title']:
        json_response['quiz_title'] = "Generated Quiz"
    
    if not json_response['quiz_subject']:
        json_response['quiz_subject'] = 'Untitled'

    if not json_response['quiz_type']:
        raise ValueError("Quiz type not provided")
    
    if not any(quiz_type == json_response['quiz_type'] for quiz_type in ['mc', 'wr', 'wrmc']):
        raise ValueError("Quiz type expects either one of these values: 'mc', 'wr', 'wrmc'")
    
    for i, question in enumerate(json_response['questions']):
        if not question['question']:
            raise ValueError(f"Question {i} missing a question value")
        
        if not question['question_type']:
            raise ValueError(f"Question {i} is missing 'question type' value")
        
        if json_response['quiz_type'] == 'wr':
            if question['question_type'] == json_response['quiz_type']:
                if 'answer' not in question:
                    raise ValueError(f"Question {i} does't have 'answer' key")
                if not question['answer']:
                    raise ValueError(f"Question {i} is missing answer value")
            else:
                    raise ValueError("Question type doesn't match quiz type")
        elif json_response['quiz_type'] == 'mc':
            if question['question_type'] == json_response['quiz_type']:
                if 'answers' not in question:
                    raise ValueError(f"Question {i} missing 'answers' key")
                if not question['answers']:
                    raise ValueError(f"Question {i} is missing 'answers' key")
                
                for answer in question['answers']:
                    if not answer['answer']:
                        raise ValueError(f"'answer' value is missing for an answer in question {i}'")

                    if not answer['is_correct']:
                        raise ValueError(f"'is_correct' value is missing for an answer in question {i}")
                    
                    if not any([answer['is_correct'] != bool_val for bool_val in ['True', 'False']]):
                        raise ValueError(f"Question {i} is missing boolen value in answer is_correct key")
            else:
                raise ValueError("Question type doesn't match quiz type")
        elif json_response['quiz_type'] == 'wrmc':
            question_type_list = []
            if question['question_type'] == 'wr':
                if 'answer' not in question:
                    raise ValueError(f"Question {i} does't have 'answer' key")
                if not question['answer']:
                    raise ValueError(f"Question {i} is missing answer value")
                question_type_list.append(question['question_type'])
                
            if question['question_type'] == 'mc':
                if 'answers' not in question:
                    raise ValueError(f"Question {i} missing 'answers' key")
                if not question['answers']:
                    raise ValueError(f"Question {i} is missing 'answers' key")
                
                for answer in question['answers']:
                    if not answer['answer']:
                        raise ValueError(f"'answer' value is missing for an answer in question {i}'")

                    if not answer['is_correct']:
                        raise ValueError(f"'is_correct' value is missing for an answer in question {i}")
                    
                    if not any([answer['is_correct'] != bool_val for bool_val in ['True', 'False']]):
                        raise ValueError(f"Question {i} is missing boolen value in answer is_correct key")
                question_type_list.append(question['question_type'])
                if not 'mc' in question_type_list and 'wr' in question_type_list:
                    raise ValueError("Missing either 'wr' or 'mc' question type for 'wrmc' quiz")

    return json_response