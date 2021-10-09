"""
The script allows user to delete selected partition_ids from existing LDM
databases.
Example:
    $ python3 filter_partitions.py -i PATH_TO_DB/common.db3 -p "769,770,771,772,773,779,780,781,783,784"
"""
from argparse import ArgumentParser
import sqlite3


def main():
    parser = ArgumentParser(description="Filter partitions ids.")
    parser.add_argument("-i", "--input", type=str, dest="input",
                        help="Path to source DB", required=True)
    parser.add_argument("-p", "--partitions", type=str, dest="partitions",
                        help="Comma-separated list of partitions", required=True)
    parser.add_argument("-e", "--exclude_tables", type=str,
                        dest="exclude_tables", required=False,
                        help="Comma-separated tables which be ignored")
    args = parser.parse_args()
    conn = sqlite3.connect(args.input)
    cursor = conn.cursor()
    print("Getting list of tables...")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [table[0] for table in cursor]
    print("Available tables:")
    print(tables)
    print("-" * 90)
    print("Removing...")
    excluded_tables = args.exclude_tables.split(",")
    for table in tables:
        if table in excluded_tables:
            print("Skipped table %s" % (table))
            continue
        print("Processed: '%s'" % table)
        try:
            cursor.execute("DELETE FROM %s WHERE PARTITION_ID NOT IN (%s)" %
                           (table, args.partitions))
        except Exception as err:
            print("WARNING: table %s - %s" % (table, err))
    conn.commit()
    print("Set 'PRAGMA vacuum'")
    conn.execute("VACUUM")

    conn.close()


if __name__ == "__main__":
    main()
