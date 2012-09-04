import readline
from nested.plugins.calculator.engine import evaluate, ParseException

if __name__ == '__main__':
    input_string = ''
    while input_string != 'quit':
        if input_string:
            try:
                result = evaluate(input_string)
                print(result)
            except ParseException as err:
                print('\n'.join([err.line, ' ' * (err.column - 1) + '^', str(err)]))

        try:
            input_string = raw_input('> ')
        except Exception:
            break

    print 'Good bye!'
