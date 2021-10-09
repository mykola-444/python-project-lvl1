import sqlite3
from argparse import ArgumentParser
from datetime import datetime


def preprocess(func):
    def wrapped(*args, **kwargs):
        args[0].conn.execute("ATTACH '{}' as dba".format(args[0].new))
        args[0].conn.execute("PRAGMA journal_mode=OFF")
        args[0].conn.execute("PRAGMA synchronisation=OFF")
        f = func(*args, **kwargs)
        args[0].conn.commit()
        args[0].conn.execute("detach database dba")
        return f
    return wrapped


class Merger:
    def __init__(self, main, new, partition_file):
        self.main = main
        self.init_connection()
        self.conn.execute("PRAGMA page_size=10240;")
        self.conn.execute("PRAGMA cache_size=10000;")
        self.new = new
        self.partitions = self.__get_partitions(partition_file)

    def init_connection(self):
        self.conn = sqlite3.connect(self.main)

    def __get_partitions(self, partition_file):
        with open(partition_file, "r") as f_:
            return f_.read().strip()

    @preprocess
    def __delete(self):
        for row in self.conn.execute("SELECT * FROM sqlite_master WHERE type='table'"):
            print("Deletion from: ", row[1])
            query = "DELETE FROM {0} WHERE PARTITION_ID IN ({1})".format(row[1], self.partitions)
            try:
                self.conn.execute(query)
            except Exception:
                pass

    @preprocess
    def __insert(self):
        for row in self.conn.execute("SELECT * FROM dba.sqlite_master WHERE type='table'"):
            print("Insert to: ", row[1])
            query = "INSERT INTO {0} SELECT * FROM dba.{0}".format(row[1])
            self.conn.execute(query)

    @preprocess
    def __remove_duplicates(self):
        for row in self.conn.execute(
                "SELECT * FROM dba.sqlite_master WHERE type='table' AND sql NOT LIKE '%PARTITION_ID%'"):
            print("Remove duplications from: ", row[1])
            query = """
DELETE FROM {0}
WHERE rowid NOT IN (
  SELECT MIN(rowid)
  FROM {0}
  GROUP BY {1}
)
            """.format(row[1], row[4].split(" ")[3][1:])
            self.conn.execute(query)

    def merge_databases(self):
        print(datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
        self.__delete()
        print(datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
        self.__insert()
        print(datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
        self.__remove_duplicates()
        print(datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
        self.conn.close()


def main():
    parser = ArgumentParser(description="Merge databases")
    parser.add_argument("-m", "--main", type=str, dest="main",
                        help="Path to the main database",
                        required=True)
    parser.add_argument("-n", "--new", type=str, dest="new",
                        help="Path to the new database",
                        required=True)
    parser.add_argument("-p", "--partition_file", type=str, dest="partition_file",
                        help="Partition file",
                        required=True)
    options = parser.parse_args()
    merger = Merger(options.main, options.new, options.partition_file)
    merger.merge_databases()


if __name__ == "__main__":
    main()
