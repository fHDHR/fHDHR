import os
import sys
import ast
import requests
import xml.etree.ElementTree
import m3u8

UNARY_OPS = (ast.UAdd, ast.USub)
BINARY_OPS = (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod)


def clean_exit():
    sys.stderr.flush()
    sys.stdout.flush()
    os._exit(0)


def m3u8_beststream(m3u8_url):
    bestStream = None
    videoUrlM3u = m3u8.load(m3u8_url)
    if len(videoUrlM3u.playlists) > 0:
        for videoStream in videoUrlM3u.playlists:
            if bestStream is None:
                bestStream = videoStream
            elif ((videoStream.stream_info.resolution[0] > bestStream.stream_info.resolution[0]) and
                  (videoStream.stream_info.resolution[1] > bestStream.stream_info.resolution[1])):
                bestStream = videoStream
            elif ((videoStream.stream_info.resolution[0] == bestStream.stream_info.resolution[0]) and
                  (videoStream.stream_info.resolution[1] == bestStream.stream_info.resolution[1]) and
                  (videoStream.stream_info.bandwidth > bestStream.stream_info.bandwidth)):
                bestStream = videoStream
        if bestStream is not None:
            return bestStream.absolute_uri
    else:
        return m3u8_url


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


class WebReq():
    def __init__(self):
        self.session = requests.Session()
