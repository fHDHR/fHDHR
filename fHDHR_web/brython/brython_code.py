from browser import document, bind  # alert, window


@bind("#enable_button", "click")
def enable_all(event):
    for element in document.get(selector='input[type="checkbox"]'):
        if element.name.endswith("enabled"):
            if document["enable_button"].value == "0":
                element.checked = False
                element.value = False
            else:
                element.checked = True
                element.value = True

    if document["enable_button"].value == "0":
        document["enable_button"].value = "1"
        document["enable_button"].text = "Enable All"
    else:
        document["enable_button"].value = "0"
        document["enable_button"].text = "Disable All"


@bind("#chanSubmit", "submit")
def submit_fixup(evt):
    for element in document.get(selector='input[type="checkbox"]'):
        if element.name.endswith("enabled"):
            if element.checked is False:
                element.checked = True
                element.value = False
            if element.name.endswith("favorite"):
                if element.checked is False:
                    element.checked = True
                    element.value = 0

    items = document.select(".channels")
    chanlist = []
    chandict = {}

    for element in items:
        if element.name == "id":
            if len(chandict.keys()):
                chanlist.append(chandict)
            chandict = {}
        chandict[element.name] = element.value
        element.clear()

    postForm = document.createElement('form')
    postData = document.createElement('input')
    postForm.method = "POST"
    postForm.action = "/api/channels?method=modify&redirect=/channels_editor"
    postForm.setRequestHeader = "('Content-Type', 'application/json')"
    postData.name = "channels"
    postData.value = chanlist
    postForm.appendChild(postData)

    document.body.appendChild(postForm)

    postForm.submit()

    evt.preventDefault()
