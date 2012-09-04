# -*- coding:utf-8 -*-
#
# Copyright (C) 2006 Steven Siew
# Copyright (C) 2011, 2012 Carlos Jenkins <carlos@jenkins.co.cr>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Simple math parser. Adapted from
http://pyparsing.wikispaces.com/file/detail/SimpleCalc.py by Steven Siew
"""

from __future__ import division

import re
import math
from pyparsing import Word, alphas, ParseException, Literal, CaselessLiteral
from pyparsing import Combine, Optional, nums, Or, Forward, ZeroOrMore
from pyparsing import StringEnd, alphanums

__all__ = ['evaluate', 'ParseException']

########################
# PARSER               #
########################

# Parser stacks
expr_stack = []
var_stack  = []

# Parser functions
def push_first(str, loc, toks):
    """
    Parser push function.
    """
    expr_stack.append(toks[0])

def assign_var(str, loc, toks):
    """
    Parser assign variable function.
    """
    var_stack.append(toks[0])

# Grammar definition
point       = Literal('.')
e           = CaselessLiteral('e')
plusorminus = Literal('+') | Literal('-')
number      = Word(nums)
integer     = Combine(Optional(plusorminus) + number)
floatnumber = Combine(integer + Optional(point + Optional(number)) +
                      Optional(e + integer))

ident  = Word(alphas,alphanums + '_')

plus   = Literal('+')
minus  = Literal('-')
mult   = Literal('*')
div    = Literal('/')
lpar   = Literal('(').suppress()
rpar   = Literal(')').suppress()
addop  = plus | minus
multop = mult | div
expop  = Literal('^')
assign = Literal('=')

expr   = Forward()
atom   = ((e | floatnumber | integer | ident).setParseAction(push_first) |
            (lpar + expr.suppress() + rpar))

factor = Forward()
factor << atom + ZeroOrMore((expop + factor).setParseAction(push_first))

term = factor + ZeroOrMore((multop + factor).setParseAction(push_first))
expr << term + ZeroOrMore((addop + term).setParseAction(push_first))
bnf = Optional((ident + assign).setParseAction(assign_var)) + expr

pattern =  bnf + StringEnd()


########################
# EVALUATOR            #
########################

# Map operator symbols to functions
opn = { '+' : (lambda a, b: a + b),
        '-' : (lambda a, b: a - b),
        '*' : (lambda a, b: a * b),
        '/' : (lambda a, b: a / b),
        '^' : (lambda a, b: a ** b)}

# Context variables
variables = {}

def evaluate_stack(s):
    """
    Recursive function that evaluates the stack.
    """
    op = s.pop()
    if op in '+-*/^':
        op2 = evaluate_stack(s)
        op1 = evaluate_stack(s)
        return opn[op](op1, op2)
    elif op == 'pi':
        return math.pi
    elif op == 'e':
        return math.e
    elif re.search('^[a-zA-Z][a-zA-Z0-9_]*$', op):
        if variables.has_key(op):
            return variables[op]
        else:
            return 0
    elif re.search('^[-+]?[0-9]+$', op):
        return long(op)
    else:
        return float(op)

def evaluate(input_string):
    """
    Parse and evaluate a string.
    """
    if not input_string:
        return ''

    # Reset expr_stack and var_stack
    global expr_stack
    global var_stack
    expr_stack = []
    var_stack  = []

    # Parse the input string
    pattern.parseString(input_string)
    # Calculate result
    result = evaluate_stack(expr_stack)
    # Store a copy in ans
    variables['ans'] = result
    # Assign result to a variable if required
    if len(var_stack) == 1:
        variables[var_stack.pop()] = result
    return result

