import datetime
from datetime import timezone



def diff_timestamp(date,time):
    timestamp1 = datetime.datetime.now().timestamp()
    timestamp2 = datetime.datetime.strptime(date+" "+time,"%d-%m-%y %H:%M")
    timestamp2 = datetime.datetime.timestamp(timestamp2)
    diff = timestamp2 - timestamp1
    return int(diff)

# dt.replace(tzinfo=timezone.utc)
# d1 = "05-05-21"
# t1 = "21:28"
# ts1 = diff_timestamp(d1,t1)
# print(int(ts1))