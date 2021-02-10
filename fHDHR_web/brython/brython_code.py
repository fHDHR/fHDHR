from browser import document, bind  # alert, window
from browser.widgets.dialog import InfoDialog
import json


@bind("#epg_chan_map", "click")
def epg_chan_map(event):
    channel_id = str(event.currentTarget.value)
    chanlist = epg_chanmap_data(document.select(".epg_channels"), channel_id)
    postForm = epg_chan_map_postform(chanlist)
    postForm.submit()
    event.preventDefault()


def epg_chan_map_postform(chanlist):
    origin = document["origin"].value
    postForm = document.createElement('form')
    postForm.method = "POST"
    postForm.action = "/api/epg?method=map&redirect=/guide?source=%s" % origin
    postForm.setRequestHeader = "('Content-Type', 'application/json')"

    postData = document.createElement('input')
    postData.type = 'hidden'
    postData.name = "channels"
    postData.value = json.dumps(chanlist)

    postForm.appendChild(postData)
    document.body.appendChild(postForm)
    return postForm


def epg_chanmap_data(items, channel_id):

    chanlist = []
    chandict = {}

    for element in items:
        if element.name == "id":
            if len(chandict.keys()) >= 2 and "id" in list(chandict.keys()):
                chanlist.append(chandict)
            chandict = {"id": element.value}
        if element.name != "id":
            chandict[element.name] = element.value

    chanlist = [x for x in chanlist if x["id"] == channel_id]

    return chanlist


@bind("#settings_help", "click")
def settings_help(event):
    config_id = str(event.currentTarget.value)
    help_info = help_data(document.select(".help"), config_id)

    config_message = ""
    for config_item in ["Description", "Valid Options", "Default Value"]:
        if help_info[0][config_item]:
            config_message += "%s: %s\n" % (config_item, help_info[0][config_item])

    InfoDialog(config_id, config_message, ok="Got it")


def help_data(items, help_id):

    helplist = []
    helpdict = {}

    for element in items:
        if element.name == "id":
            if len(helpdict.keys()) >= 2 and "id" in list(helpdict.keys()):
                helplist.append(helpdict)
            helpdict = {"id": element.value}
        if element.name != "id":
            helpdict[element.name] = element.value

    helplist = [x for x in helplist if x["id"] == help_id]

    return helplist


def chan_edit_data(items, channel_id):

    chanlist = []
    chandict = {}

    for element in items:
        if element.name == "id":
            if len(chandict.keys()) >= 2 and "id" in list(chandict.keys()):
                chanlist.append(chandict)
            chandict = {"id": element.value}
        if element.type == "checkbox":
            if element.name in ["enabled"]:
                save_val = element.checked
            else:
                save_val = int(element.checked)
        else:
            save_val = element.value
        if element.name != "id":
            cur_value = element.placeholder
            if element.type == "checkbox":
                if element.name in ["enabled"]:
                    cur_value = element.placeholder
                else:
                    cur_value = int(element.placeholder)
            if str(save_val) != str(cur_value):
                chandict[element.name] = save_val

    if channel_id != "all":
        chanlist = [x for x in chanlist if x["id"] == channel_id]

    return chanlist


def chan_edit_id(evt):
    for child in evt.currentTarget.children:
        try:
            id = child.id
        except AttributeError:
            id = None
        if id:
            return id
    return None


def chan_edit_postform(chanlist):
    origin = document["origin"].value
    postForm = document.createElement('form')
    postForm.method = "POST"
    postForm.action = "/api/channels?method=modify&origin=%s&redirect=/channels_editor?origin=%s" % (origin, origin)
    postForm.setRequestHeader = "('Content-Type', 'application/json')"

    postData = document.createElement('input')
    postData.type = 'hidden'
    postData.name = "channels"
    postData.value = json.dumps(chanlist)

    postForm.appendChild(postData)
    document.body.appendChild(postForm)
    return postForm


@bind("#Chan_Edit_Reset", "submit")
def chan_edit_reset(evt):
    channel_id = chan_edit_id(evt)
    chanlist = chan_edit_data(
                              document.select(".reset"),
                              str(channel_id).replace("reset_", ""))
    postForm = chan_edit_postform(chanlist)
    postForm.submit()
    evt.preventDefault()


@bind("#Chan_Edit_Modify", "submit")
def chan_edit_modify(evt):
    channel_id = chan_edit_id(evt)
    chanlist = chan_edit_data(
                              document.select(".channels"),
                              str(channel_id).replace("modify_", ""))
    postForm = chan_edit_postform(chanlist)
    postForm.submit()
    evt.preventDefault()


@bind("#Chan_Edit_Enable_Toggle", "click")
def chan_edit_enable(event):
    enable_bool = bool(int(document["enable_button"].value))
    for element in document.get(selector='input[type="checkbox"]'):
        if element.name == "enabled":
            element.checked = enable_bool
            element.value = enable_bool

    if not enable_bool:
        document["enable_button"].value = "1"
        document["enable_button"].text = "Enable All"
    else:
        document["enable_button"].value = "0"
        document["enable_button"].text = "Disable All"


@bind("#Chan_Edit_Favorite_Toggle", "click")
def chan_edit_favorite(event):
    enable_bool = bool(int(document["favorite_button"].value))
    for element in document.get(selector='input[type="checkbox"]'):
        if element.name == "favorite":
            element.checked = enable_bool
            element.value = int(enable_bool)

    if not enable_bool:
        document["favorite_button"].value = "1"
        document["favorite_button"].text = "Favorite All"
    else:
        document["favorite_button"].value = "0"
        document["favorite_button"].text = "Unfavorite All"
