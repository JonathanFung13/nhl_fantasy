#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
#import lxml.html
from pprint import pprint
#from sys import exit
import json
#import csv
import pandas as pd

def get_string_season(season):
    return str(season - 1) + str(season)


def get_skater_stats(season):
    stringSeason = get_string_season(season)
    req = 'http://www.nhl.com/stats/rest/skaters?isAggregate=false&reportType=basic&isGame=false' + \
            '&reportName=skatersummary&sort=[{"property":"points","direction":"DESC"}]&cayenneExp=gameTypeId=2' + \
            'and seasonId%3E=' + stringSeason + 'and seasonId%3C=' + stringSeason
    resp_json = requests.get(req).text
    leaders = json.loads(resp_json)['data']

    skaters = pd.DataFrame(data=leaders)
    skaters = skaters[['playerId', 'playerPositionCode', 'playerName', 'points']]
    maskForwards = skaters['playerPositionCode'] != 'D'
    skaters.loc[maskForwards, 'playerPositionCode'] = 'F'

    return skaters

def get_goalie_stats(season):
    stringSeason = get_string_season(season)
    req = 'http://www.nhl.com/stats/rest/goalies?isAggregate=false&reportType=goalie_basic&isGame=false' +\
          '&reportName=goaliesummary&sort=[{"property":"saves","direction":"DESC"}]&cayenneExp=gameTypeId=2' +\
          ' and seasonId%3E=' + stringSeason + 'and seasonId%3C=' + stringSeason
    resp_json = requests.get(req).text
    leaders = json.loads(resp_json)['data']

    goalies = pd.DataFrame(data=leaders)





print(get_skater_stats(2018))


