from numpy import rec
import pymongo

class DB:

    def __init__(self, host, db, collection, user=None, password=None):

        MONGODB_TIMEOUT = 1000
        MONGODB_SOCKETTIMEOUT = 3000
        if user and password:
            uri = 'mongodb://' + user + ':' + password + '@' + host + ':27017' + '/Crudo'
        else:
            uri = "mongodb://" + host + ":27017/"
        self.client = pymongo.MongoClient(uri, connectTimeoutMS=MONGODB_TIMEOUT, socketTimeoutMS=MONGODB_SOCKETTIMEOUT)
        self.db = self.client[db]
        self.collection = self.db[collection]
        self.pdf_collection = self.db["pdfs_done"]

    def insert(self, object):

        if type(object) != list:
            object = [object]
        for record in object:
            if not self.exists(record):
                self.collection.insert_one(record)

    def exists(self, object):
        
        record = self.collection.find_one( {"actor": object["actor"], "demandado": object["demandado"], "juzgado": object['juzgado'], "expediente": object["expediente"], "materia": object["materia"], "fecha": object["fecha"] } )
        if record:
            return True
        return False

    def check_pdf(self, pdf):
        if self.pdf_collection.find_one( {"pdf": pdf}):
            return True
        return False

    def insert_pdf(self, pdf):
        if not self.check_pdf(pdf):
            self.pdf_collection.insert_one({ "pdf": pdf})