class AnswerType(object):
    code = None
    name = None

    def __init__(self, definitions):
        self.definitions = definitions

    def get_default_definitions(self):
        raise NotImplemented('Implement in the base class')

    def get_score_from_answer(self, answer):
        raise NotImplemented('Implement in the base class')

    def is_valid_answer(self, answer):
        raise NotImplemented('Implement in the base class')

    #TODO: add functions that will power form fields


class NumericAnswer(AnswerType):
    code = 1
    name = 'Numeric'

    def get_default_definitions(self):
        return {
            1: 1,
            2: 2,
            3: 3,
            4: 4,
            5: 5
        }

    def get_score_from_answer(self, answer):
        return self.definitions[answer]

    def is_valid_answer(self, answer):
        return answer in self.definitions


class BooleanAnswer(AnswerType):
    code = 2
    name = 'Boolean'


class ChoiceAnswer(AnswerType):
    code = 3
    name = 'Choice'


def as_choices():
    return [(A.code, A.name,) for A in [NumericAnswer, BooleanAnswer, ChoiceAnswer]]


def get(code):
    return {A.code: A for A in [NumericAnswer, BooleanAnswer, ChoiceAnswer]}[code]
