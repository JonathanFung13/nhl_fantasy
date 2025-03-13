#!/usr/bin/env python
# -*- coding: utf-8 -*-
# from __future__ import print_function
import requests
import json
import logging

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
    response = requests.get(url)
    if not response.ok:
        raise Exception("Could not complete request for: " + url)

    response_txt = response.text
    data = json.loads(response_txt)

    if "success" in data: # Note there is no success key in response
        raise Exception("Could not complete request for: " + url)

    return data

def get_skater_stats(start, end, regular_season=True):
    start = get_string_season(start)
    end = get_string_season(end)
    type = get_game_type(regular_season)

    base_url = 'https://api.nhle.com/stats/rest/en/skater/summary?isAggregate=false&isGame=false&' + \
          'sort=[{\"property\":\"lastName\",\"direction\":\"ASC_CI\"},' + \
          '{\"property\":\"skaterFullName\",\"direction\":\"ASC_CI\"},' + \
          '{\"property\":\"playerId\",\"direction\":\"ASC\"}]'

    limit, offset, skaters = 100, 0, []
    while True:
        params = '&start={}&limit={}&factCayenneExp=gamesPlayed>=1&cayenneExp=gameTypeId={} and seasonId<={} and seasonId>={}'.format(offset, limit, type, end, start)
        url = base_url + params
        logging.debug(url)
        response = request_json(base_url + params)

        if len(response.get('data')) > 0:
            skaters += response.get('data')
            offset += limit
        else:
            break

    # skaters = pd.DataFrame(skaters)

    return skaters

def get_goalie_stats(start, end, regular_season=True):
    start = get_string_season(start)
    end = get_string_season(end)
    type = get_game_type(regular_season)

    limit, offset, goalie_data = 100, 0, []
    while True:
        url = f'https://api.nhle.com/stats/rest/en/goalie/summary?isAggregate=false&isGame=false&sort=%5B%7B%22property%22:%22saves%22,%22direction%22:%22DESC%22%7D,%7B%22property%22:%22playerId%22,%22direction%22:%22ASC%22%7D%5D&start={offset}&limit={limit}&cayenneExp=gameTypeId={type}%20and%20seasonId%3C={start}%20and%20seasonId%3E={end}'
        logging.debug(url)
        response = request_json(url)

        if len(response.get('data')) > 0:
            goalie_data += response.get('data')
            offset += limit
        else:
            break

    # goalies = pd.DataFrame(goalie_data)

    return goalie_data

def get_rosters():
    # req = "https://statsapi.web.nhl.com/api/v1/teams?expand=team.roster"
    # #"https://records.nhl.com/site/api/player/byTeam/5?include=id&include=firstName&include=lastName&include=sweaterNumber&include=position&include=height&include=weight&include=birthDate&include=birthCountry&include=birthCity&include=birthStateProvince&include=onRoster"
    # roster_data = request_json(req)

    rosters = []
    # for teams in roster_data["teams"]:
    #     for players in teams["roster"]["roster"]:
    #         if "jerseyNumber" in players:
    #             number = players["jerseyNumber"]
    #         else:
    #             number = 0
    #
    #         rosters.append({
    #             "fullName": players["person"]["fullName"],
    #             "jerseyNumber": number,
    #             "position": players["position"]["abbreviation"],
    #             "teamName": teams["name"]
    #         })
    #
    # rosters = pd.DataFrame.from_records(rosters)
    # rosters = rosters.sort_values("fullName")

    return rosters

# def get_prospect_info(link):
#     if link[-4:] == "null":
#         return {}
#
#     req = "https://statsapi.web.nhl.com" + link
#     prospect_data = request_json(req)
#
#     if 'prospects' in prospect_data and len(prospect_data['prospects']) > 0:
#         return prospect_data['prospects'][0]
#     else:
#         return {}

# def get_drafts(start, end):
#     req = "https://statsapi.web.nhl.com/api/v1/draft/"
#     players = []
#
#     for draft_year in range(start, end):
#         draft_data = request_json(req+str(draft_year))
#         draft = pd.DataFrame(data=draft_data["drafts"])
#
#         for rounds in draft["rounds"]:
#             for round in rounds:
#                 for pick in round["picks"]:
#                     logging.debug(draft_year, pick["prospect"]["fullName"], pick["prospect"]["link"])
#                     player_details = get_prospect_info(pick["prospect"]["link"])
#                     players.append({**pick, **player_details})
#
#     drafts = pd.DataFrame.from_records(pd.json_normalize(players))
#
#     return drafts

# def save_csv(filename, df):
#     if not os.path.isdir(OUTPUT_FOLDER):
#         os.makedirs(OUTPUT_FOLDER)
#
#     df.to_csv(os.path.join(OUTPUT_FOLDER, filename), index=False)
#
# def load_csv(filename):
#
#     df_filename = os.path.join(OUTPUT_FOLDER, filename)
#     if not os.path.isfile(df_filename):
#         raise Exception(filename + " not found.")
#
#     df = pd.read_csv(df_filename)
#     return df

if __name__ == "main":
    logging.info("Please run one of the other .py files.")
