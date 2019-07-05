#!/usr/bin/env python
# -*- coding: utf-8 -*-

#from __future__ import print_function
import get_NHL_stats as gs
import pandas as pd

def get_career_stats(start, end, regularSeason):

    # Get skater and goalie stats, combine them in a dataframe.
    skaters = gs.get_skater_stats(start, end, regularSeason)
    skaters = skaters[["playerName", "playerPositionCode", "playerNationality", "playerHeight", "playerWeight",
                       "playerId", "gamesPlayed", "goals", "assists", "points", "pointsPerGame",
                       "playerBirthCity", "playerBirthCountry", "playerBirthDate"]]

    goalies = gs.get_goalie_stats(start, end, regularSeason)
    goalies = goalies[["playerName", "playerPositionCode", "playerNationality", "playerHeight", "playerWeight",
                       "playerId", "gamesPlayed", "shotsAgainst", "saves", "shutouts", "savePctg",
                       "playerBirthCity", "playerBirthCountry", "playerBirthDate"]]

    all_stats = pd.concat([skaters, goalies], axis=0, sort=False)
    all_stats = all_stats.sort_values("playerName")
    all_stats.fillna(0, inplace=True)

    # all_stats = all_stats.rename(columns={"playerName": "PlayerName", "playerPositionCode": "Pos",
    #                                   "playerNationality": "Nationality", "playerHeight": "Ht", "playerWeight": "Wt",
    #                                   "playerId": "PlayerID", "gamesPlayed": "GamesPlayed", "goals": "Goals",
    #                                   "assists": "Assists", "points": "Points", "pointsPerGame": "PPG",
    #                                   "playerBirthCity": "BirthCity", "playerBirthCountry": "BirthCountry",
    #                                   "playerBirthDate": "BirthDate"})

    return all_stats

def update_team_names(df):
    # Update names of relocated franchises.
    df.loc[df["team.name"]=="Winnipeg Jets (1979)", "team.name"] = "Arizona Coyotes"
    df.loc[df["team.name"]=="Hartford Whalers", "team.name"] = "Carolina Hurricanes"
    df.loc[df["team.name"]=="Phoenix Coyotes", "team.name"] = "Arizona Coyotes"
    df.loc[df["team.name"]=="Atlanta Thrashers", "team.name"] = "Winnipeg Jets"

    return df

def set_statuses(df):
    df.loc[df["team.name"] != df["teamName"], "status"] = "other_team"
    df.loc[df["team.name"] == df["teamName"], "status"] = "active"
    df.loc[df["teamName"].isnull(), "status"] = "inactive"

    max_year = df["year"].max()
    df["gpPerYear"] = df["gamesPlayed"] / (max_year - df["year"] + 1)
    df["gpClass"] = 1
    df.loc[df["gpPerYear"]>=20, "gpClass"] = 2
    df.loc[df["gpPerYear"]>=40, "gpClass"] = 3
    df.loc[df["gpPerYear"]>=60, "gpClass"] = 4

    df["ppgClass"] = 1
    df.loc[df["pointsPerGame"]>=0.25, "ppgClass"] = 2
    df.loc[df["pointsPerGame"]>=0.5, "ppgClass"] = 3
    df.loc[df["pointsPerGame"]>=0.75, "ppgClass"] = 4
    df.loc[df["pointsPerGame"]>=1.0, "ppgClass"] = 5

    return df

def clean_data(df):
    df.loc[df["birthCity"].isnull(), "birthCity"] = df["playerBirthCity"]
    df.loc[df["birthCountry"].isnull(), "birthCountry"] = df["playerBirthCountry"]
    df.loc[df["birthDate"].isnull(), "birthDate"] = df["playerBirthDate"]
    df.loc[df["nationality"].isnull(), "nationality"] = df["playerNationality"]
    df.loc[df["playerId"].isnull(), "playerId"] = df["nhlPlayerId"]
    df.loc[df["position"].isnull(), "position"] = df["primaryPosition.abbreviation"]
    df.loc[df["position"].isnull(), "position"] = "U"

    # Fix incorrect float types as integers
    int_columns = ["weight", "playerHeight", "playerWeight", "playerId", 'gamesPlayed', 'goals', 'assists', 'points',
                   'shotsAgainst', 'saves', 'shutouts', 'jerseyNumber']
    for col in int_columns:
        df[col].fillna(0, inplace=True)
        df[col] = df[col].astype('int64')

    return df

def reduce_columns(df):
    # columns = ['amateurLeague.link', 'amateurLeague.name', 'amateurTeam.link', 'amateurTeam.name', 'birthCity', 'birthCountry', 'birthDate', 'birthStateProvince', 'draftStatus', 'firstName', 'fullName', 'height', 'id', 'lastName', 'link', 'nationality', 'nhlPlayerId', 'pickInRound', 'pickOverall', 'primaryPosition.abbreviation', 'primaryPosition.code', 'primaryPosition.name', 'primaryPosition.type', 'prospect.fullName', 'prospect.id', 'prospect.link', 'prospectCategory.id', 'prospectCategory.name', 'prospectCategory.shortName', 'round', 'shootsCatches', 'team.id', 'team.link', 'team.name', 'weight', 'year', 'name_lower', 'playerName', 'playerPositionCode', 'playerNationality', 'playerHeight', 'playerWeight', 'playerId', 'gamesPlayed', 'goals', 'assists', 'points', 'pointsPerGame', 'playerBirthCity', 'playerBirthCountry', 'playerBirthDate', 'shotsAgainst', 'saves', 'shutouts', 'savePctg', 'fullName_y', 'jerseyNumber', 'position', 'teamName', 'Status', 'gpPerYear', 'gpClass', 'ppgClass']
    columns = ['year', 'round', 'pickInRound', 'pickOverall', 'team.name', 'prospect.fullName',
               'position', 'nationality', 'height', 'weight', 'playerHeight', 'playerWeight',
               'birthCity', 'birthCountry', 'birthDate',
               'amateurLeague.name', 'amateurTeam.name', 'playerId',
               'gamesPlayed', 'goals', 'assists', 'points', 'pointsPerGame',
               'shotsAgainst', 'saves', 'shutouts', 'savePctg', 'jerseyNumber', 'teamName',
               'status', 'gpPerYear', 'gpClass', 'ppgClass']

    df = df[columns]
    return df

def main():
    start_season = 1995
    end_season = 2019
    regular_season = True

    if False:
        drafts = gs.get_drafts(start_season, end_season) # Takes a loonnnggg time to run
        players = get_career_stats(start_season, end_season, regular_season)
        rosters = gs.get_rosters()

        gs.save_csv("drafts.csv", drafts)
        gs.save_csv("players.csv", players)
        gs.save_csv("rosters.csv", rosters)
    else:
        drafts = gs.load_csv("drafts.csv")
        players = gs.load_csv("players.csv")
        rosters = gs.load_csv("rosters.csv")

    drafts = update_team_names(drafts)
    drafts = drafts.sort_values(["team.name", "year", "round"], ascending=[1, 0, 1])

    # Merge all data into one dataframe
    drafts['name_lower'] = drafts['prospect.fullName'].str.lower()
    players['name_lower'] = players['playerName'].str.lower()
    rosters['name_lower'] = rosters['fullName'].str.lower()
    draft_data = pd.merge(drafts, players, how="left", on="name_lower", sort=False, suffixes=("", "_x"))
    draft_data = pd.merge(draft_data, rosters, how="left", on="name_lower", sort=False, suffixes=("", "_y"))

    # Update positions and set statuses for each filter in the visuzalization.  Then get rid of unneeded columns.
    draft_data = set_statuses(draft_data)
    draft_data = clean_data(draft_data)
    draft_data = reduce_columns(draft_data)

    gs.save_csv("draft_data.csv", draft_data)


if __name__ == "__main__":
    main()