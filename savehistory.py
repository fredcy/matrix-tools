import argparse
import datetime
import json
import os
import psycopg2
import requests
import sys

Host = "https://matrix.org"
Room_Id = "!XBHXetkKeLSOaFJiaH%3Amatrix.org"


def getfrom(conn, host, token, room, marker):
    path = "/_matrix/client/r0/rooms/" + room + "/messages"
    params = {'from': marker, 'limit': '200', 'dir': 'b', 'access_token': token}

    url = host + path

    r = requests.get(url, params=params)
    if r.status_code != 200:
        print("bad response code:", r.status_code, locals())
        return

    jbody = r.json()
    #print(json.dumps(jbody, indent=4))

    end = jbody['end']
    print(end)

    cur = conn.cursor()

    for m in jbody['chunk']:
        content = json.dumps(m['content'])
        ts = datetime.datetime.fromtimestamp(m['origin_server_ts'] / 1000)
        try:
            cur.execute('insert into events (ts, event_id, sender, content, type, room_id) values (%s, %s, %s, %s, %s, %s)',
                        (ts, m['event_id'], m['sender'], content, m['type'], m['room_id']))
        except psycopg2.IntegrityError:
            print("ignoring duplicate")
            conn.rollback()
        else:
            conn.commit()
            print(ts)

    cur.close()
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


def main(host, token, room):
    pgurl = os.getenv("PG_URI")
    if not pgurl:
        print("Error: PG_URL not set")
        return
    
    conn = psycopg2.connect(pgurl)
    print(conn)

    marker = getmarker(host, token, room)

    while marker:
        nextmarker = getfrom(conn, host, token, room, marker)
        if nextmarker == marker:
            print("next marker same as current; reached end?", marker)
            return
        marker = nextmarker


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Sync room history. Access token expected in $AUTH_TOKEN.',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--host', help='matrix host URL', default=Host)
    parser.add_argument('--room', help='internal room_id', default=Room_Id)
    args = parser.parse_args()

    token = os.getenv("AUTH_TOKEN")
    if not token:
        print("Error: AUTH_TOKEN not set")
        sys.exit(1)

    main(args.host, token, args.room)
