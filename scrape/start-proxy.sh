#!/bin/bash

mitmdump --listen-host 127.0.0.1 --listen-port "$1" -s mitm/response_token.py -s mitm/farewell.py -s mitm/subscription_expired.py
