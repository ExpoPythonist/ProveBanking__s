__all__ = ['values_to_choices', 'choices_to_values']
def values_to_choices(values):
    '''Given a list of strings, convert them to a choices tuple for the choices 
    attribute for any model Field.'''
    assert isinstance(values, (tuple, list))
    assert len(values) > 0
    for value in values:
        assert isinstance(value, basestring)
        assert len(value) > 0
    assert len(values) == len(set(values)) # Ensure no duplicates

    return tuple( [(value, value) for value in values] )


def choices_to_values(choices):
    '''Gets all the values from the choices attribute for any model Field.'''
    assert isinstance(choices, tuple)
    for choice in choices:
        assert isinstance(choice, tuple)
        assert len(choice) == 2

    return [choice[0] for choice in choices]
