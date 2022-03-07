import ast
import xml.etree.ElementTree
import json

UNARY_OPS = (ast.UAdd, ast.USub)
BINARY_OPS = (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod)


"""Various Tools for fHDHR Usage."""


def checkattr(inst_obj, attrcheck):

    # Quick check of hasattr
    if hasattr(inst_obj, attrcheck):
        return True

    # Check if attribute is in dir list
    if attrcheck in [x for x in dir(inst_obj) if not x.startswith("__")]:
        return True

    return False


def is_jsonable(x):
    try:
        json.dumps(x)
        return True
    except Exception:
        return False


def inlist_match(searchterm, termlist):
    for termlist_item in termlist:
        if termlist_item.lower() == str(searchterm).lower():
            return termlist_item, True
    return searchterm, False


def channel_sort(channel_list):
    """Take a list of channel number strings and sort the Numbers and SubNumbers"""

    chan_dict_list_split = {}
    for number in channel_list:

        if number and (isint(number) or isfloat(number)):

            if "." in number:
                subnumber = number.split(".")[1]
            else:
                subnumber = None
            prinumber = number.split(".")[0]

        else:
            prinumber, subnumber = None, None

        chan_dict_list_split[number] = {"number": prinumber, "subnumber": subnumber}

    return sorted(chan_dict_list_split, key=lambda i: (int(chan_dict_list_split[i]['number'] or 0), int(chan_dict_list_split[i]['subnumber'] or 0)))


def sub_el(parent, sub_el_item_name, text=None, **kwargs):
    el = xml.etree.ElementTree.SubElement(parent, sub_el_item_name, **kwargs)
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


def closest_int_from_list(lst, K):
    return lst[min(range(len(lst)), key=lambda i: abs(lst[i]-K))]


def hours_between_datetime(first_time, later_time):
    timebetween = first_time - later_time
    return (timebetween.total_seconds() / 60 / 60)


def humanized_filesize(size, decimal_places=2):
    for unit in ['B', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB', 'YiB']:
        if size < 1024.0 or unit == 'YiB':
            break
        size /= 1024.0
    return f"{size:.{decimal_places}f} {unit}"
