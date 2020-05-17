import json
from websocket import create_connection
import random
import time
random.seed(time.time())
import requests
import signal

timeout_seconds = 300

# https://stackoverflow.com/questions/2281850/timeout-function-if-it-takes-too-long-to-finish
class timeout:
    def __init__(self, seconds=1, error_message='Timeout'):
        self.seconds = seconds
        self.error_message = error_message
    def handle_timeout(self, signum, frame):
        raise TimeoutError(self.error_message)
    def __enter__(self):
        signal.signal(signal.SIGALRM, self.handle_timeout)
        signal.alarm(self.seconds)
    def __exit__(self, type, value, traceback):
        signal.alarm(0)


### /Applications/Chromium.app/Contents/MacOS/Chromium
#  --incognito
# --remote-debugging-port=9333
# --user-data-dir=./tmpChrome

def fetch_content_with_status(given_url):
    returnHTML = "<body not available>"
    status = None
    headers = "<headers not available>"
    finalURL = "<url not available>"

    # Keep initiating until we know the chrome instance is running
    while True:
        try:
            main_debug_url = json.loads(requests.get("http://localhost:9333/json/version").text)['webSocketDebuggerUrl']
            break
        except:
            pass

    main_debug = create_connection(main_debug_url)
    myID = random.randint(0, 1000)
    create_bc = """
    {"id": """ + str(myID) + """, "method": "Target.createBrowserContext", "params": {}}
    """
    main_debug.send(create_bc)
    while True:
        msg = json.loads(main_debug.recv())
        if 'id' in msg:
            if msg['id'] == myID:
                bcID = (msg['result']['browserContextId'])
                break

    myID = random.randint(0, 1000)
    params = {'browserContextId': bcID, 'url': 'about:blank'}
    create_target = {'id': myID, 'method': 'Target.createTarget', 'params': params}
    main_debug.send(json.dumps(create_target))
    while True:
        msg = json.loads(main_debug.recv())
        if 'id' in msg:
            if msg['id'] == myID:
                targetID = (msg['result']['targetId'])
                break
    # print(targetID, bcID)

    # We want a page to open and finish loading within the timeout.
    all_msgs = []
    try:
        with timeout(seconds=timeout_seconds):

            target_debug = create_connection('ws://localhost:9333/devtools/page/' + targetID)

            # Send request to open URL in browser
            enable_network = """
            {"id": 1, "method": "Network.enable", "params": {}}
            """

            enable_page = """
            {"id": 2, "method": "Page.enable", "params": {}}
            """

            enable_dom = """
            {"id": 3, "method": "DOM.enable", "params": {}}
            """

            params = {'url': given_url}
            page_navigate = json.dumps({'id': 4, 'method': 'Page.navigate', 'params': params})

            close_target = json.dumps({'id': 5, 'method': 'Target.closeTarget', 'params': {'targetId': targetID}})

            sends = [enable_network, enable_dom, enable_page, page_navigate]
            for send in sends:
                target_debug.send(send)
            results = []

            # Get reqID first
            while True:
                msg = json.loads(target_debug.recv())
                all_msgs.append(msg)
                if 'method' in msg and msg['method'] == "Network.requestWillBeSent":
                    assert msg['params']['documentURL'] == msg['params']['request']['url']
                    reqID = msg['params']['requestId']
                    break
                elif 'error' in msg and msg['id'] == 4:
                    # If navigation failed
                    raise ValueError

            # Get all other messages till loading is finished
            while True:
                msg = json.loads(target_debug.recv())
                all_msgs.append(msg)
                results.append(msg)

                # Always break if loading failed or finished
                if 'method' in msg and msg['method'] == "Page.domContentEventFired":
                    break
                elif 'method' in msg and msg['method'] == "Network.loadingFailed":
                    if msg['params']['requestId'] == reqID:
                        break

                # Save headers at right time
                if 'method' in msg and msg['method'] == "Network.responseReceived":
                        if msg['params']['requestId'] == reqID:
                            headers = json.loads(json.dumps(msg['params']['response']['headers']).lower())
                            finalURL =  msg['params']['response']['url']

            # Check load status
            for r in results:
                if 'method' in r and 'params' in r and r['params']['requestId'] == reqID:
                    if r['method'] == 'Network.loadingFailed':
                        status = r['params']['errorText']
                        break
                    elif r['method'] == 'Network.responseReceived':
                        status = r['params']['response']['status']
                        break

            # Continue only if the page was successfully loaded
            if (type(status) == int) and status < 400:
                # This works even in headless
                key_down = """
                {"id": 22222, "method": "Input.synthesizeScrollGesture", "params": {"x": 0, "y": 0, "yDistance": -500, "xDistance": 150}}
                """
                target_debug.send(key_down)
                while True:
                    msg = json.loads(target_debug.recv())
                    all_msgs.append(msg)
                    if 'id' in msg and msg['id'] == 22222:
                        break

                get_dom_doc = """
                {"id": 7, "method": "DOM.getDocument", "params": {}}
                """
                get_dom = """
                {"id": 8, "method": "DOM.getOuterHTML", "params": {"nodeId": 1}}
                """
                target_debug.send(get_dom_doc)
                target_debug.send(get_dom)
                while True:
                    msg = json.loads(target_debug.recv())
                    all_msgs.append(msg)
                    if 'id' in msg and msg['id'] == 8:
                        returnHTML = msg['result']['outerHTML']
                        break
            # Clean up
            target_debug.send(close_target)
            target_debug.close()
    except ValueError:
        status = "<navigate error>"
        headers = "<headers not available>"
        finalURL = "<url not available>"
        returnHTML = "<body not available>"
    except TimeoutError:
        print("**-** fetch_content_with_status() timeout:", given_url)
        for msg in all_msgs:
            print("**;**", msg)
        status = "<timeout error>"
        headers = "<headers not available>"
        finalURL = "<url not available>"
        returnHTML = "<body not available>"

    myID = random.randint(0, 1000)
    params = {'browserContextId': bcID}
    delete_bc = {'id': myID, 'method': 'Target.disposeBrowserContext', 'params': params}
    main_debug.send(json.dumps(delete_bc))
    main_debug.close()

    # print(all_msgs)

    return ((type(status) == int) and status < 400), status, finalURL, headers, returnHTML.encode()


# https://www.verycloud.cn/node/261
# print(fetch_content_with_status("http://mashablsaddasdse.com"))
