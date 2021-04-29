import dbm
import sys
import os

files = os.listdir(sys.argv[1])

master = dbm.open('master.db', 'w')

for db in files:
    try:
        db_ = dbm.open(sys.argv[1] + "/" + db, 'r')
    except:
        continue

    for key in db_.keys():
        if key not in master or (key in master and len(master[key]) < len(db_[key])):
            master[key] = db_[key]

    print("Done ", db)

master.close()