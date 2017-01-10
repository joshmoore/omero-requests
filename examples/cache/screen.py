import logging
import argparse
import sys

from orequests import OmeroRequests


PAGE = 200

PLATES_URL = "/webclient/api/plates/?id={screen_id}&page=0&group=3"
RUNS_URL = "/webclient/api/plate_acquisitions/?id={plate_id}&page=0&group=3"
WELLS_IMAGES_URL = "/webgateway/plate/{plate_id}/{run_id}/"

METADATA_URL = "/webclient/metadata_details/{type}/{id}/?index={field}"
MAP_URL = "/webclient/api/annotations/?type=map&{type}={id}"


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--screen", action="store", type=long)
    parser.add_argument("-f", "--fields", action="store", type=int)

    parser.add_argument("-H", "--domain", action="store", type=str)
    parser.add_argument("-U", "--username", action="store", type=str)
    parser.add_argument("-P", "--password", action="store", type=str)
    parser.add_argument("-T", "--token", action="store", type=str)

    args = parser.parse_args(sys.argv[1:])
    domain = args.domain
    screen_id = args.screen
    try:
        fields = args.fields
    except:
        fields = None
    try:
        username = args.username
        password = args.password
    except:
        username = None
        password = None

    try:
        token = args.token
    except:
        token = None

    LOG_FILENAME = 'cache-screen-%s.log' % screen_id
    logging.basicConfig(filename=LOG_FILENAME, level=logging.DEBUG)

    with OmeroRequests() as oreq:
        oreq.configure(domain)
        oreq.connect(token=token, username=username, password=password)

        _url = oreq.prepare_url(PLATES_URL, {'screen_id': screen_id})
        grsps = oreq.async_requests(urls=[_url])

        for grsp in grsps:
            for pl in grsp.json()['plates']:
                plate_id = pl['id']
                child_count = fields or pl['childCount']
                child_count = 1 if child_count == 0 else child_count
                plateurl = []
                for run_id in xrange(0, child_count):
                    _u = oreq.prepare_url(
                        WELLS_IMAGES_URL,
                        {'plate_id': plate_id, 'run_id': run_id})
                    plateurl.append(_u)
                grsps2 = oreq.async_requests(urls=plateurl)

                gridurls = []
                for grsp2 in grsps2:
                    for row in grsp2.json()['grid']:
                        for cell in row:
                            if cell is not None:
                                well_id = cell['wellId']
                                image_id = cell['id']
                                thumb_url = cell['thumb_url']
                                field = cell['field']
                                _u = oreq.prepare_url(thumb_url,
                                                      no_prefix=True)
                                gridurls.append(_u)
                                _u = oreq.prepare_url(
                                    METADATA_URL,
                                    {'type': 'well', 'id': well_id,
                                     'field': field})
                                gridurls.append(_u)
                                _u = oreq.prepare_url(
                                    MAP_URL,
                                    {'type': 'image', 'id': image_id})
                                gridurls.append(_u)
                oreq.async_requests(urls=gridurls)
