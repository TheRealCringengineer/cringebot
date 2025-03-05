import pymongo
from typing_extensions import is_protocol
from pymongo import MongoClient
import logging

import os
from dotenv import load_dotenv
load_dotenv()

class Database():

    def __init__(self) -> None:
        username = os.getenv("MONGO_INITDB_ROOT_USERNAME")
        password = os.getenv("MONGO_INITDB_ROOT_PASSWORD")
        self.client = MongoClient(f"mongodb://{username}:{password}@mongodb:27017/")
        self.db = self.client["cringebot_db"]
        self.leaderboard = self.db["leaderboard"]
        logging.info("Database is created")

    # Leaderboard

    def winner_exist(self, username):
        record = {
            "username" : username
        }
        res = self.leaderboard.find_one(record)

        return res is not None

    def clear_all_winners(self):
        self.leaderboard.update_many({}, {"$set" : {"is_last_winner" : False, "score" : 1000}})

    def get_first_place(self):
        return self.leaderboard.find().sort("score", pymongo.ASCENDING).limit(1)

    def update_winner(self):

        first = self.get_first_place()
        if first is None:
            return

        self.clear_all_winners()

        record = {
            "id" : first[0]["id"]
        }

        user = self.leaderboard.find_one(record)

        if not user:
            return

        old_count = user["count"]

        update_record = {
            "$set" : {"count" : old_count+1,"username" : first[0]["username"] , "is_last_winner" : True}
        }
        self.leaderboard.update_one(record, update_record)

    def update_score(self, id, username, score):
        record = {
            "id" : id 
        }

        user = self.leaderboard.find_one(record)

        if not user:
            return

        best_score = float(score) if float(score) < float(user["score"]) else float(user["score"])

        update_record = {
            "$set" : {"score" : best_score, "username" : username}
        }
        self.leaderboard.update_one(record, update_record)

    def is_not_empty(self):
        users = self.leaderboard.count_documents({})
        return users > 0

    def get_last_winner(self):

        winner = self.leaderboard.find_one({"is_last_winner" : True})
        if not winner:
            return None

        return winner["username"]

    def add_leaderboard_user(self, id, username):
        if self.winner_exist(username):
            return

        record = {
            "id" : id,
            "username" : username,
            "count" : 0,
            "score" : 1000,
            "is_last_winner" : False
        }
        self.leaderboard.insert_one(record)

    def get_my_place(self, id):
        leaderboard = self.leaderboard.find().sort("score", pymongo.ASCENDING)
        if leaderboard is None:
            return None

        index = 1
        for user in leaderboard:
            if user["id"] == id:
                return index, user["score"], user["count"]
            index += 1
        return None


    def get_leaderboard(self):
        return self.leaderboard.find().sort("score", pymongo.ASCENDING)

