from datetime import datetime, timedelta
import requests
from player_manager import PlayerManager
from team_manager import TeamManager

class MatchManager:
    def __init__(self, db_manager):
        self.db = db_manager
        self.player_manager = PlayerManager(db_manager)
        self.team_manager = TeamManager(db_manager)

    def get_yesterday_date(self):
        return datetime.now().date() - timedelta(days=1)

    def check_and_fetch_yesterday_matches(self):
        print('Делаю запрос в БД...')
        yesterday = self.get_yesterday_date()
        print(yesterday)
        fixtures = self.db.execute_query("""
            SELECT fixture_id
            FROM Matches
            WHERE DATE(fixture_datetime) = %s AND played_or_not = TRUE
        """, (yesterday,))

        if fixtures:
            print(f'Вчера было сыгранно несколько матчей. Начинаю добавлять статистику по ним...')
            for fixture in fixtures:
                fixture_id = fixture[0]
                self.get_players_statictics_from_current_fixture(fixture_id)
        else:
            print(f'Вчера не было матчей')

    def insert_match(self, home_team_id, away_team_id, fixture_id, league_round, full_score_home, full_score_away, home_team_res, away_team_res, played_or_not, fixture_datetime):
        self.db.execute_non_query("""
            INSERT INTO Matches (home_team_id, away_team_id, fixture_id, league_round, full_score_home, full_score_away, home_team_res, away_team_res, played_or_not, fixture_datetime)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (home_team_id, away_team_id, fixture_id, league_round, full_score_home, full_score_away, home_team_res, away_team_res, played_or_not, fixture_datetime))

    def find_matches(self):
        print('Делаю запрос матчей...')
        leagues = ["235"]
        season = '2024'

        for league_id in leagues:
            url = "https://v3.football.api-sports.io/fixtures"
            querystring = {"league": league_id, "season": season}
            headers = {'x-apisports-key': "AP"}

            response = requests.get(url, headers=headers, params=querystring)
            data = response.json()

            c = 0
            for info in data['response']:
                home_team_id = info['teams']['home']['id']
                home_team = info['teams']['home']['name']
                home_logo = info['teams']['home']['logo']
                home_team_winner = info['teams']['home']['winner']

                away_team_id = info['teams']['away']['id']
                away_team = info['teams']['away']['name']
                away_team_winner = info['teams']['away']['winner']
                away_logo = info['teams']['away']['logo']

                fixture_id = info['fixture']['id']
                fixture_datetime = datetime.fromisoformat(info['fixture']['date'].replace("Z", "+00:00"))

                league_round = info['league']['round']
                full_score_home = info['score']['fulltime']['home']
                full_score_away = info['score']['fulltime']['away']

                c += 1
                if c > 24:
                    break
                else:
                    played_or_not = not (home_team_winner is None and away_team_winner is None and full_score_home is None and full_score_away is None)
                    home_team_res = home_team_winner is True
                    away_team_res = away_team_winner is True

                    # Вставляем команды в таблицу Teams
                    self.team_manager.insert_team(home_team_id, home_team, home_logo)
                    self.team_manager.insert_team(away_team_id, away_team, away_logo)

                    # Вставляем матч в таблицу Matches
                    self.insert_match(home_team_id, away_team_id, fixture_id, league_round, full_score_home, full_score_away, home_team_res, away_team_res, played_or_not, fixture_datetime)

                    print(f'======= ДОБАВЛЯЮ МАТЧ ===========')
                    print(f'{league_round} Матч между {home_team} и {away_team} добавлен в базу данных.')

                    if played_or_not and (away_team_id==597 or home_team_id==597):
                        self.get_players_statictics_from_current_fixture(fixture_id, full_score_home, full_score_away)

                    print(f'======= МАТЧ УСПЕШНО ДОБАВЛЕН ===========')

    def get_players_statictics_from_current_fixture(self, fixture_id, full_score_home, full_score_away):
        url = "https://v3.football.api-sports.io/fixtures/players"
        querystring = {"fixture": fixture_id}
        headers = {'x-apisports-key': "API"}
        response = requests.get(url, headers=headers, params=querystring)
        data = response.json()

        correct_score = 0
        for info in data['response']:
            team_id = info['team']['id']
            correct_score += 1
            if correct_score == 1:
                print(f'--- Добавляю статистику игроков из {team_id} ---')
                conceded_goals = full_score_away

            elif correct_score == 2:
                print(f'--- Добавляю статистику игроков из {team_id} ---')
                conceded_goals = full_score_home

            for add_info in info['players']:
                player_id = add_info['player']['id']
                player_name = add_info['player']['name']
                player_photo_url = add_info['player']['photo']

                #print(player_id, player_name)
                for stats_info in add_info['statistics']:
                    minutes_played = stats_info['games'].get('minutes', 0)
                    position = stats_info['games']['position']
                    from_bench_or_not = stats_info['games']['substitute']
                    yellow_cards = stats_info['cards']['yellow']
                    red_cards = stats_info['cards']['red']
                    goals_scored = stats_info['goals']['total']
                    goals_assisted = stats_info['goals']['assists']
                    penalty_won = stats_info['penalty']['won']
                    goals_conceded = stats_info['goals'].get('conceded')
                    player_saves = stats_info['goals'].get('saves')
                    played_clean_sheet = None

                    if minutes_played is None:
                        minutes_played = 0
                    if goals_assisted is None:
                        goals_assisted = 0

                    skip_next_match_or_not = False
                    if yellow_cards > 1 and red_cards == 1:
                        yellow_cards = 0
                        skip_next_match_or_not = True

                    if position == "G":
                        GK_not_clean = False
                        player_saves = stats_info['goals']['saves']
                        played_clean_sheet = stats_info['goals']['conceded']
                        goals_conceded = stats_info['goals']['conceded']

                        if played_clean_sheet > 0:
                            played_clean_sheet = False
                            GK_not_clean = True
                        else:
                            played_clean_sheet = True

                    if GK_not_clean and (position == "D" or position == "M"):
                        played_clean_sheet = False
                        if position == "D":
                            goals_conceded = conceded_goals

                    total_round_points = self.player_manager.count_points_for_match(position, minutes_played,
                                                                                    yellow_cards, red_cards,
                                                                                    goals_scored, goals_assisted,
                                                                                    from_bench_or_not,
                                                                                    played_clean_sheet, player_saves,
                                                                                    penalty_won, goals_conceded)
                    last_round_points = total_round_points
                    total_points = total_round_points

                    self.player_manager.insert_player(player_id, team_id, player_name, player_photo_url, position,
                                                      minutes_played, yellow_cards, red_cards, goals_scored,
                                                      goals_assisted, from_bench_or_not, skip_next_match_or_not,
                                                      played_clean_sheet, player_saves, penalty_won, goals_conceded,
                                                      last_round_points, total_points)
                    print(f'Игрок {player_name} из {team_id} сыгравший {fixture_id} успешно добавлен в БД')
                    print(f'================')