import re

# Change status 402 -> 200 for expired wikis. This tells wget that it should follow links on the page.

def response(flow):
    if flow.response.status_code == 402:
        flow.response.status_code = 200
