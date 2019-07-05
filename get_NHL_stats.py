#!/usr/bin/env python
# -*- coding: utf-8 -*-
# from __future__ import print_function
import requests
import json
import pandas as pd
from pandas.io.json import json_normalize
import os

OUTPUT_FOLDER = "output"

def get_string_season(season):
    return str(season - 1) + str(season)

def get_game_type(regular_season=True):
    if regular_season: # regular season =2, playoffs = 3
        gametype = 2
    else:
        gametype = 3

    return gametype

def request_json(url):
    resp_json = requests.get(url).text
    data = json.loads(resp_json)

    if "success" in data: # Note there is no success key in response
        raise Exception("Could not complete request for: " + url)
    return data

def get_skater_stats(start, end, regular_season=True):
    start = get_string_season(start)
    end = get_string_season(end)
    type = get_game_type(regular_season)

    req = "http://www.nhl.com/stats/rest/skaters?isAggregate=true&reportType=basic&isGame=false" + \
          '&reportName=skatersummary&sort=[{"property":"points","direction":"DESC"}]&cayenneExp=gameTypeId=' + \
          str(type) + "and seasonId%3E=" + start + "and seasonId%3C=" + end
    skater_data = request_json(req)
    skaters = pd.DataFrame(data=skater_data["data"])

    return skaters

def get_goalie_stats(start, end, regular_season=True):
    start = get_string_season(start)
    end = get_string_season(end)
    type = get_game_type(regular_season)

    req = "http://www.nhl.com/stats/rest/goalies?isAggregate=true&reportType=goalie_basic&isGame=false" +\
          '&reportName=goaliesummary&sort=[{"property":"saves","direction":"DESC"}]&cayenneExp=gameTypeId=' + \
          str(type) + "and seasonId%3E=" + start + "and seasonId%3C=" + end
    goalie_data = request_json(req)
    goalies = pd.DataFrame(data=goalie_data["data"])

    return goalies

def get_rosters():
    req = "https://statsapi.web.nhl.com/api/v1/teams?expand=team.roster"
    roster_data = request_json(req)

    rosters = []
    for teams in roster_data["teams"]:
        for players in teams["roster"]["roster"]:
            if "jerseyNumber" in players:
                number = players["jerseyNumber"]
            else:
                number = 0

            rosters.append({
                "fullName": players["person"]["fullName"],
                "jerseyNumber": number,
                "position": players["position"]["abbreviation"],
                "teamName": teams["name"]
            })

    rosters = pd.DataFrame.from_records(rosters)
    rosters = rosters.sort_values("fullName")

    return rosters

def get_prospect_info(link):
    if link[-4:] == "null":
        return {}

    req = "https://statsapi.web.nhl.com" + link
    prospect_data = request_json(req)

    if 'prospects' in prospect_data and len(prospect_data['prospects']) > 0:
        return prospect_data['prospects'][0]
    else:
        return {}

def get_drafts(start, end):
    req = "https://statsapi.web.nhl.com/api/v1/draft/"
    players = []

    for draft_year in range(start, end):
        draft_data = request_json(req+str(draft_year))
        draft = pd.DataFrame(data=draft_data["drafts"])

        for rounds in draft["rounds"]:
            for round in rounds:
                for pick in round["picks"]:
                    print(draft_year, pick["prospect"]["fullName"], pick["prospect"]["link"])
                    player_details = get_prospect_info(pick["prospect"]["link"])
                    players.append({**pick, **player_details})

    drafts = pd.DataFrame.from_records(json_normalize(players))

    return drafts

def save_csv(filename, df):
    if not os.path.isdir(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)

    df.to_csv(os.path.join(OUTPUT_FOLDER, filename), index=False)

def load_csv(filename):

    df_filename = os.path.join(OUTPUT_FOLDER, filename)
    if not os.path.isfile(df_filename):
        raise Exception(filename + " not found.")

    df = pd.read_csv(df_filename)
    return df