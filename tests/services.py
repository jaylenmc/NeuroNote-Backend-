from .models import Answer

def patch_quiz(question, question_obj):
    if question.get('question_type') == 'MC':
        for answer in question['answers']:
            if 'id' in answer and question_obj.answers.filter(id=answer['id']).exists():
                answer_obj = question_obj.answers.get(id=answer['id'])
                answer_obj.answer_input = answer.get('answer_input', answer_obj.answer_input)
                answer_obj.is_correct = answer.get('is_correct', answer_obj.is_correct)
                answer_obj.save()
            else:
                Answer.objects.create(
                    question=question_obj,
                    answer_input=answer.get('answer_input', 'Untitled Answer'),
                    is_correct=answer.get('is_correct', False)
                )
    elif question.get('question_type') == 'WR':
        if 'id' in question['answers'] and question_obj.answers.filter(id=question['answers'].get('id')).exists():
            answer_obj = question_obj.answers.get(id=question['answers'].get('id'))
            answer_obj.answer_input = question.get('answer_input', answer_obj.answer_input)
            answer_obj.is_correct = question.get('is_correct', answer_obj.is_correct)
            answer_obj.save()
        else:
            Answer.objects.create(
                question=question_obj,
                answer_input=question.get('answer_input', 'Untitled Answer'),
                is_correct=question.get('is_correct', False)
            )