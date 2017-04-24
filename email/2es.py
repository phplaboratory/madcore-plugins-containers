
from flanker.addresslib import address
from flanker import mime
import os

for root, dirs, files in os.walk("/Users/polfilm/.mail/account/allmail/cur"):
    for file in files:
        filefullname = os.path.join(root, file)
        message_string = open(filefullname,"rb").read()
        msg = mime.from_string(message_string)
        print len(msg.headers)


