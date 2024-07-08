import hashlib
import os
import sqlite3

from youtube.items import YoutubeItem
from youtube.utils.util import Util


class SqliteDao:
    def __init__(self, name=None, path=None):
        file_path = None
        if name:
            name = Util.replace_name(name)
            file_path = f"./resource/database_{name}.db"
        elif path:
            file_path = path
        self.table_name = "t_data"
        status = not os.path.exists(file_path)
        self.connect = sqlite3.connect(file_path)
        self.cursor = self.connect.cursor()
        if status:
            self.cursor.execute(f"""
                        CREATE TABLE {self.table_name} (
                        "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                        "videoId" text,
                        "title" text,
                        "title_hash" text,
                        "lengthText" text,
                        "status" integer DEFAULT 0
                    );""")
            self.connect.commit()

    def insert(self, item: YoutubeItem):
        sql = f"""
            insert into 
                {self.table_name}(videoId,title,title_hash,lengthText)
            values (
                "{item["videoId"]}",
                "{item["title"]}",
                "{hashlib.md5(item["title"].encode("utf-8")).hexdigest()}",
                "{item["lengthText"]}"
            )
        """

        self.cursor.execute(sql)
        self.connect.commit()

    def update(self, id):
        sql = f"""
            update 
                {self.table_name}
            set 
                status = 1
            where
                id = {id}
        """
        self.cursor.execute(sql)
        self.connect.commit()

    def select_all(self):
        sql = f"""
            select 
                id,videoId,title,title_hash
            from
                {self.table_name}
            where 
                status = 0
        """
        self.cursor.execute(sql)
        return self.cursor.fetchall()

    def close(self):
        self.cursor.close()
        self.connect.close()
