from slackclient import SlackClient
from selenium import webdriver
from _iteration_utilities import unique_everseen
import googlemaps
import psycopg2
import re
import time
import traceback
import sys
from utilities import *
import settings
import unidecode

def scrape_agency(agency, browser):
    '''
    scrapes all agencies and saves new results to db
    '''
    slack_results = []
    slack_results_trains = []
    slack_result_lands = []
    gmaps = googlemaps.Client(key=settings.GMAPS_KEY)

    # initialize browser
    browser.get(settings.AGENCIES[agency]['browserLink'])

    linkRegexp = re.compile(r'' + settings.AGENCIES[agency]['linkRegexp'] + '')

    # gets list of all entries on first 2 pages of agency website
    linkMatch = []
    for i in range(1, 2):
        html_source = browser.page_source
        time.sleep(10)
        linkMatch += linkRegexp.findall(html_source)
        nextPageRegexp = re.compile(r'{}'.format(settings.AGENCIES[agency]['nextPageRegexp']))
        nextPageLink = nextPageRegexp.findall(html_source)
        nextPageLink = nextPageLink[0].replace('"', '')
        if 'BEZREALITKY' not in agency:
            nextPage = settings.AGENCIES[agency]['url'] + nextPageLink
        else:
            nextPage = nextPageLink

        browser.get(nextPage)

    linkMatch = list(unique_everseen(linkMatch))
    final_links = [settings.AGENCIES[agency]['url'] + x for x in linkMatch]

    # connects to db, saves all new links
    try:
        con = psycopg2.connect("dbname = \'{}\' user = \'{}\' password = \'{}\'".format(settings.DB_NAME, settings.DB_USER, settings.DB_PASSWORD))
        cur = con.cursor()
    except Exception as exc:
        print("Error: ", sys.exc_info()[0])
        traceback.print_exc()

    for links in final_links:
        try:
            cur.execute('INSERT INTO realitky (link) VALUES (\'{}\')'.format(links))
            con.commit()
        except psycopg2.IntegrityError:
            con.commit()

    # selects all links which haven't been scrapped yet
    sql = 'select link,id from realitky WHERE realitky."isChecked" = \'FALSE\' AND link LIKE \'%{}%\''.format(settings.AGENCIES[agency]['url'])
    cur.execute(sql)
    to_check = cur.fetchall()

    # scrapes new entry and returns all results for it
    for data in to_check:
        browser.get(data[0])
        time.sleep(8)
        locationRegexp = re.compile(r'{}'.format(settings.AGENCIES[agency]['locationRegexp']))
        location = locationRegexp.findall(browser.page_source)
        try:
            location = location[0]
        except Exception:
            location = 'N/A'
            # traceback.print_exc()
            continue

        location = location.replace('Panorama', '')  # exception for sreality, which sometimes adds word panorama

        separator = 'okres'
        location = location.split(separator, 1)[0]

        location = unidecode.unidecode(location)
        location = location.lower()

        priceRegexp = re.compile(r'{}'.format(settings.AGENCIES[agency]['priceRegexp']))
        price = priceRegexp.findall(browser.page_source)
        price = price[0]

        if price == "Cena na vyžádání":
            continue

        # sizeRegexp = re.compile(r'{}'.format(settings.AGENCIES[agency]['sizeRegexp']))
        # size = sizeRegexp.findall(browser.page_source)
        # size = size[0]

        try:
            distance, duration = 'x km', 'x minutes'
        except Exception:
            print("Error: ", sys.exc_info()[0])
            traceback.print_exc()
            distance, duration = 'N/A', 'N/A'

        try:
            cur.execute(
                'UPDATE  realitky SET location=%s, "isChecked"=%s, price=%s, distance=%s, duration=%s  WHERE id=%s',
                (location, 'TRUE', price, distance, duration, data[1]))
            entry = data[0] + '\nPrice: ' + price  + '\nLocation: ' + location + '\nDistance: ' + distance + '\nDuration: ' + duration
            con.commit()

        except psycopg2.IntegrityError:
            print('Not working: ' + data[0])
            con.commit()

        if 'lands' in agency:
            if any(city in location for city in settings.CITIES):
                slack_result_lands.append(entry)
                continue

            else:
                continue

        # send to slack only desired cities

        if any(city in location for city in settings.CITIES):
            slack_results_trains.append(entry)
            continue
        else:
            continue

    return slack_results, slack_results_trains, slack_result_lands


def do_scrape():
    '''
    Runs scrapper and returns new results to slack
    '''

    sc = SlackClient(settings.SLACK_TOKEN)
    browser_window = webdriver.Firefox()

    all_results = []
    all_results_trains = []
    all_results_lands = []
    for agency in settings.AGENCIES:
        if 'IDNES' in agency:
            continue
        default_result, train_result, land_result = scrape_agency(agency, browser_window)
        all_results += default_result
        all_results_trains += train_result
        all_results_lands += land_result

    browser_window.quit()
    print("{}: Got {} new results".format(time.ctime(), (len(all_results_lands) + len(all_results_trains))))

    # send each result to slack

    # for result in all_results:
    #    trains = 'no_trains'
    #    send_to_slack(sc, result, trains)

    for result in all_results_trains:
        trains = 'trains'
        send_to_slack(sc, result, trains)

    for result in all_results_lands:
        trains = 'lands'
        send_to_slack(sc, result, trains)


