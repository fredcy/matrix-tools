import argparse
import datetime
import json
import os
import requests
import sys

Host = "https://ostez.com"
Room_Id = "!KNlqwBRiVdbAwkVpKO%3Amatrix.org"
Token = ""


def getfrom(host, token, room, marker):
    path = "/_matrix/client/r0/rooms/" + room + "/messages"
    params = {'from': marker, 'limit': '200', 'dir': 'b', 'access_token': token}

    url = host + path

    r = requests.get(url, params=params)
    if r.status_code != 200:
        print("bad response code:", r.status_code, locals())
        return

    jbody = r.json()
    print(json.dumps(jbody, indent=4))

    end = jbody['end']
    print(end)

    for m in jbody['chunk']:
        a = datetime.datetime.fromtimestamp(m['origin_server_ts'] / 1000)
        print(a)

    return end


def getmarker(host, token, room):
    path = "/_matrix/client/r0/rooms/" + room + "/messages"
    params = {'access_token': token}
    url = host + path

    r = requests.get(url, params=params)
    if r.status_code != 200:
        print("bad response code:", r.status_code, locals())
        return

    jbody = r.json()
    print(json.dumps(jbody, indent=4))
    return jbody['end']


def main(host, token, room, marker):
    while marker:
        nextmarker = getfrom(host, token, room, marker)
        if nextmarker == marker:
            print("next marker same as current; reached end?", marker)
            return
        marker = nextmarker


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Sync room history. Access token expected in $AUTH_TOKEN.',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--host', help='matrix host URL', default=Host)
    parser.add_argument('--room', help='internal room_id', default=Room_Id)
    parser.add_argument('--marker', help='marker token from /messages response', \
                        default=None)
    args = parser.parse_args()

    token = os.getenv("AUTH_TOKEN")
    if not token:
        print("Error: AUTH_TOKEN not set")
        sys.exit(1)

    marker = args.marker or getmarker(args.host, token, args.room)
    
    main(args.host, token, args.room, marker)

