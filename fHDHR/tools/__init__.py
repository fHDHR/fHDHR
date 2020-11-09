import ast
import requests
import xml.etree.ElementTree

UNARY_OPS = (ast.UAdd, ast.USub)
BINARY_OPS = (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod)


def sub_el(parent, name, text=None, **kwargs):
    el = xml.etree.ElementTree.SubElement(parent, name, **kwargs)
    if text:
        el.text = text
    return el


def xmldictmaker(inputdict, req_items, list_items=[], str_items=[]):
    xml_dict = {}

    for origitem in list(inputdict.keys()):
        xml_dict[origitem] = inputdict[origitem]

    for req_item in req_items:
        if req_item not in list(inputdict.keys()):
            xml_dict[req_item] = None
        if not xml_dict[req_item]:
            if req_item in list_items:
                xml_dict[req_item] = []
            elif req_item in str_items:
                xml_dict[req_item] = ""

    return xml_dict


def is_arithmetic(s):
    def _is_arithmetic(node):
        if isinstance(node, ast.Num):
            return True
        elif isinstance(node, ast.Expression):
            return _is_arithmetic(node.body)
        elif isinstance(node, ast.UnaryOp):
            valid_op = isinstance(node.op, UNARY_OPS)
            return valid_op and _is_arithmetic(node.operand)
        elif isinstance(node, ast.BinOp):
            valid_op = isinstance(node.op, BINARY_OPS)
            return valid_op and _is_arithmetic(node.left) and _is_arithmetic(node.right)
        else:
            raise ValueError('Unsupported type {}'.format(node))

    try:
        return _is_arithmetic(ast.parse(s, mode='eval'))
    except (SyntaxError, ValueError):
        return False


def isint(x):
    try:
        a = float(x)
        b = int(a)
    except ValueError:
        return False
    else:
        return a == b


def isfloat(x):
    try:
        float(x)
    except ValueError:
        return False
    else:
        return True


def hours_between_datetime(first_time, later_time):
    timebetween = first_time - later_time
    return (timebetween.total_seconds() / 60 / 60)


def humanized_time(countdownseconds):
    time = float(countdownseconds)
    if time == 0:
        return "just now"
    year = time // (365 * 24 * 3600)
    time = time % (365 * 24 * 3600)
    day = time // (24 * 3600)
    time = time % (24 * 3600)
    time = time % (24 * 3600)
    hour = time // 3600
    time %= 3600
    minute = time // 60
    time %= 60
    second = time
    displaymsg = None
    timearray = ['year', 'day', 'hour', 'minute', 'second']
    for x in timearray:
        currenttimevar = eval(x)
        if currenttimevar >= 1:
            timetype = x
            if currenttimevar > 1:
                timetype = str(x+"s")
            if displaymsg:
                displaymsg = str(displaymsg + " " + str(int(currenttimevar)) + " " + timetype)
            else:
                displaymsg = str(str(int(currenttimevar)) + " " + timetype)
    if not displaymsg:
        return "just now"
    return displaymsg
    # just for ignoring a pep error
    year, day, hour, minute, second


class WebReq():
    def __init__(self):
        self.session = requests.Session()
        self.exceptions = requests.exceptions
