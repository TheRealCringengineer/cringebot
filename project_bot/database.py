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


    def update_project(self, project_name, project_text_ru, project_text_eng, project_file):
        if self.is_project_exist(project_name):
            record = {
                "name" : project_name
            }
            update_record = {
                "$set" : {"text_ru" : project_text_ru, "text_eng" : project_text_eng,"file" : project_file}
            }
            self.projects.update_one(record, update_record)
            self.clear_cache(project_name)

    def create_project(self, project_name, project_text_ru, project_text_eng, project_file) -> bool:
        
        if self.is_project_exist(project_name):
            logging.error(f"Project {project_name} exist. Updating...")
            return False

        record = {
            "name" : project_name,
            "text_ru" : project_text_ru,
            "text_eng" : project_text_eng,
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
