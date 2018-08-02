import settings


def check_maps(destination_location, gmaps):
    '''
    calculates distance and duration using google maps api
    '''

    source_location = 'Deutsche Boerse, Praha'
    result = gmaps.distance_matrix(source_location, destination_location, mode='driving')
    distance = result['rows'][0]['elements'][0]['distance']['text']
    duration = result['rows'][0]['elements'][0]['duration']['text']

    return distance, duration


def send_to_slack(sc, result):
    '''
    sends results to slack
    '''

    sc.api_call(
        "chat.postMessage", channel=settings.SLACK_CHANNEL, text=result,
        username='pybot', icon_emoji=':robot_face:'
    )

