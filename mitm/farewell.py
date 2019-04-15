import re

#farewell_re = 'ws.common.addNotice\("<script type=\\"text\\\/javascript\\">function wsDismissBanner\(\) { ws.common.removeNotice\(\);  ws.cookie.set\(\\"wsFirstPartShutdownSecondReminder\\", 1, {expires: 365 \* 86400, domain: \\".wikispaces.com\\"}\); return false;}\$\(\\".ui-pnotify-closer\\"\).remove\(\);<\\\/script><i class=\\"fa fa-times fa-fw ws-close\\" onclick=\\"wsDismissBanner\(\);\\"><\\\/i>It\\\u2019s time to say farewell\\\u2026.. All free and classroom Wikis will become inaccessible at the end of this month. You must ensure any data that you require is exported before July 31st, 2018. For more information on how to do this, click <a href=\'http:\\\/\\\/helpcenter.wikispaces.com\\\/customer\\\/en\\\/portal\\\/articles\\\/2920537-classroom-and-free-wikis\' target=\'_top\'>HERE<a\\\/> ", "warning"\);'

farewell_re = 'ws\.common\.addNotice\('

def response(flow):
    if 'Content-Type' in flow.response.headers and 'text/html' in flow.response.headers['Content-Type']:
        flow.response.text = re.sub(farewell_re, '// ws.common.addNotice(', flow.response.text)
