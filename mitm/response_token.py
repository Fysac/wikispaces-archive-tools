import re

def response(flow):
    if 'Content-Type' in flow.response.headers and 'text/html' in flow.response.headers['Content-Type']:
        flow.response.text = re.sub('\?responseToken=\w+&amp;', '?', flow.response.text)
        flow.response.text = re.sub('&amp;responseToken=\w+', '', flow.response.text)
        flow.response.text = re.sub('\?responseToken=\w+', '', flow.response.text)
