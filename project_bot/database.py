from typing_extensions import is_protocol
from pymongo import MongoClient
import logging

from dotenv import load_dotenv
load_dotenv()

class Database():

    def __init__(self) -> None:
        self.client = MongoClient(f"mongodb://{os.getenv("MONGO_INITDB_ROOT_USERNAME")}:{os.getenv("MONGO_INITDB_ROOT_PASSWORD")}@mongodb:27017/")
        self.db = self.client["cringebot_db"]
        self.users = self.db["users"]
        self.leaderboard = self.db["leaderboard"]
        self.projects = self.db["projects"]
        logging.info("Database is created")

    def get_language(self, id) -> str:
        record = {
            "id" : id
        }
        res = self.users.find_one(record)

        if res is None:
            return ""

        return res["language"]

    def is_user_exist(self, id) -> bool:
        record = {
            "id" : id
        }
        res = self.users.find_one(record)

        return res is not None

    def get_unique_count(self) -> int:
        return self.users.count_documents({})

    def update_language(self, id, lang):
        if self.is_user_exist(id):
            record = {
                "id" : id
            }
            update_record = {
                "$set" : {"language" : lang}
            }
            self.users.update_one(record, update_record)

    def add_new_user(self, id, username, lang) -> bool:

        if self.is_user_exist(id):
            logging.error(f"User {username} exist")
            return False

        record = {
            "id" : id,
            "username" : username,
            "language" : lang
        }
        self.users.insert_one(record)
        return True

    def is_project_exist(self, name) -> bool:
        record = {
            "name" :name 
        }
        res = self.projects.find_one(record)

        return res is not None

    def is_cached(self, name) -> bool:
        record = {
            "name" :name 
        }
        res = self.projects.find_one(record)
        if not res:
            return False
        if not res["cache"] or len(res["cache"]) == 0:
            return False

        return True


    def update_project(self, project_name, project_text, project_file):
        if self.is_project_exist(project_name):
            record = {
                "name" : project_name
            }
            update_record = {
                "$set" : {"text" : project_text, "file" : project_file}
            }
            self.projects.update_one(record, update_record)
            self.clear_cache(project_name)

    def create_project(self, project_name, project_text, project_file) -> bool:
        
        if self.is_project_exist(project_name):
            logging.error(f"Project {project_name} exist. Updating...")
            return False

        record = {
            "name" : project_name,
            "text" : project_text,
            "file" : project_file,
            "cache" : None
        }

        self.projects.insert_one(record)
        return True

    def get_projects(self):
        return self.projects.find()

    def clear_cache(self, project_name):
        if self.is_project_exist(project_name):
            record = {
                "name" : project_name
            }
            update_record = {
                "$set" : {"cache" : ""}
            }
            self.projects.update_one(record, update_record)

    def set_cache_if_not_exist(self, project_name, project_cache):
        if not self.is_cached(project_name):
            record = {
                "name" : project_name
            }
            update_record = {
                "$set" : {"cache" : project_cache}
            }
            self.projects.update_one(record, update_record)

    # Leaderboard

    def winner_exist(self, username):
        record = {
            "username" : username
        }
        res = self.leaderboard.find_one(record)

        return res is not None

    def update_winner(self, username):
        record = {
            "username" : username
        }

        user = self.leaderboard.find_one(record)

        if not user:
            return

        old_count = user["count"]

        update_record = {
            "$set" : {"count" : old_count+1}
        }
        self.leaderboard.update_one(record, update_record)

    def add_leaderboard_user(self, username):
        if self.winner_exist(username):
            return

        record = {
            "username" : username,
            "count" : 0
        }
        self.leaderboard.insert_one(record)

    def add_winner(self, username):
        if self.winner_exist(username):
            self.update_winner(username) 
            return

        record = {
            "username" : username,
            "count" : 1
        }
        self.leaderboard.insert_one(record)
