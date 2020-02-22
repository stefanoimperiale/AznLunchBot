import pymongo


class MongoHandler:
    def __init__(self, cluster: str, user: str, db_pass: str):
        self.client = pymongo.MongoClient(
            f"mongodb+srv://{user}:{db_pass}@{cluster}-xdema.mongodb.net/test?retryWrites=true&w=majority")

    def get_db(self, db_name):
        return self.client[db_name]

    @staticmethod
    def get_collection(db, collection):
        return db[collection]
