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


def scrape_agency(agency, browser):
    '''
    scrapes all agencies and saves new results to db
    '''
    slack_results = []
    gmaps = googlemaps.Client(key=settings.GMAPS_KEY)

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
        nextPage = settings.AGENCIES[agency]['url'] + nextPageLink
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

    # selects all links which havent been scrapped yet
    sql = 'select link,id from realitky WHERE realitky."isChecked" = \'FALSE\' AND link LIKE \'%{}%\''.format(settings.AGENCIES[agency]['url'])
    cur.execute(sql)
    to_check = cur.fetchall()

    # scrapes new entry and returns all results for it
    for data in to_check:
        browser.get(data[0])
        time.sleep(8)
        locationRegexp = re.compile(r'{}'.format(settings.AGENCIES[agency]['locationRegexp']))
        location = locationRegexp.findall(browser.page_source)
        location = location[0]
        location = location.replace('Panorama', '')

        priceRegexp = re.compile(r'{}'.format(settings.AGENCIES[agency]['priceRegexp']))
        price = priceRegexp.findall(browser.page_source)
        price = price[0]

        sizeRegexp = re.compile(r'{}'.format(settings.AGENCIES[agency]['sizeRegexp']))
        size = sizeRegexp.findall(browser.page_source)
        size = size[0]

        try:
            distance, duration = check_maps(location, gmaps)
        except Exception:
            print("Error: ", sys.exc_info()[0])
            traceback.print_exc()
            distance, duration = 'N/A', 'N/A'

        try:
            cur.execute(
                'UPDATE  realitky SET location=%s, "isChecked"=%s, price=%s, distance=%s, duration=%s, size=%s  WHERE id=%s',
                (location, 'TRUE', price, distance, duration, size, data[1]))
            entry = data[0] + '\nPrice: ' + price + '\nSize: ' + size + '\nLocation: ' + location + '\nDistance: ' + distance + '\nDuration: ' + duration
            con.commit()

        except psycopg2.IntegrityError:
            print('Not working: ' + data[0])
            con.commit()
        slack_results.append(entry)

    return slack_results


def do_scrape():
    '''
    Runs scrapper and returns new results to slack
    '''

    sc = SlackClient(settings.SLACK_TOKEN)
    browser_window = webdriver.Firefox()

    all_results = []
    for agency in settings.AGENCIES:
        all_results += scrape_agency(agency, browser_window)

    browser_window.quit()
    print("{}: Got {} new results".format(time.ctime(), len(all_results)))

    # send each result to slack

    for result in all_results:
        send_to_slack(sc, result)
