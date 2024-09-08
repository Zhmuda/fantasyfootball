import requests
import psycopg2
from db_manager import DBManager

class PlayerManager:
    def __init__(self, db_manager: DBManager):
        self.db = db_manager

    def fetch_image_as_bytes(self, url):
        response = requests.get(url)
        return response.content

    def count_points_for_match(self, position, minutes_played, yellow_cards, red_cards, goals_scored, goals_assisted, from_bench_or_not, played_clean_sheet, player_saves, penalty_won, goals_conceded):
        counter = 0
        if minutes_played > 0:
            counter += 1
        if minutes_played >= 60:
            counter += 1
        if from_bench_or_not is False and minutes_played > 89 and (position == "M" or position == "F"):
            counter += 1
        if goals_scored is not None:
            goals_scored_points = {"G": 6, "D": 6, "M": 5, "F": 4}
            counter += goals_scored_points.get(position, 0) * goals_scored
        if goals_assisted > 0:
            counter += 3
        if played_clean_sheet:
            if minutes_played >= 60:
                clean_sheet_points = {"G": 4, "D": 4, "M": 1}
                counter += clean_sheet_points.get(position, 0)
        if yellow_cards > 0:
            counter -= 1
        if red_cards > 0:
            counter -= 3
        if penalty_won:
            counter += 2
        if player_saves and position == "G":
            counter += (player_saves // 3) * 1
        if goals_conceded:
            counter -= (goals_conceded // 2)
        return counter

    def insert_player(self, player_id, team_id, player_name, player_photo_url, position, minutes_played, yellow_cards, red_cards, goals_scored, goals_assisted, from_bench_or_not, skip_next_match_or_not, played_clean_sheet, player_saves, penalty_won, goals_conceded, last_round_points, total_points):
        player_photo_bytes = self.fetch_image_as_bytes(player_photo_url)
        self.db.execute_non_query("""
            INSERT INTO TeamPlayers (player_id, team_id, player_name, player_photo, position, minutes_played, yellow_cards, red_cards, goals_scored, goals_assisted, from_bench_or_not, skip_next_match_or_not, played_clean_sheet, player_saves, penalty_won, goals_conceded, last_round_points, total_points)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (player_id) DO UPDATE SET
                team_id = EXCLUDED.team_id,
                player_name = EXCLUDED.player_name,
                player_photo = EXCLUDED.player_photo,
                position = EXCLUDED.position,
                minutes_played = EXCLUDED.minutes_played,
                yellow_cards = EXCLUDED.yellow_cards,
                red_cards = EXCLUDED.red_cards,
                goals_scored = EXCLUDED.goals_scored,
                goals_assisted = EXCLUDED.goals_assisted,
                from_bench_or_not = EXCLUDED.from_bench_or_not,
                skip_next_match_or_not = EXCLUDED.skip_next_match_or_not,
                played_clean_sheet = EXCLUDED.played_clean_sheet,
                player_saves = EXCLUDED.player_saves,
                penalty_won = EXCLUDED.penalty_won,
                goals_conceded = EXCLUDED.goals_conceded,
                last_round_points = EXCLUDED.last_round_points,
                total_points = TeamPlayers.total_points + EXCLUDED.total_points
        """, (player_id, team_id, player_name, psycopg2.Binary(player_photo_bytes), position, minutes_played, yellow_cards, red_cards, goals_scored, goals_assisted, from_bench_or_not, skip_next_match_or_not, played_clean_sheet, player_saves, penalty_won, goals_conceded, last_round_points, total_points))
