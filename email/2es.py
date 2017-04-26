
from flanker.addresslib import address
from flanker import mime
import os
import json

for root, dirs, files in os.walk("/Users/polfilm/.mail/account/allmail/cur"):
    for file in files:
        filefullname = os.path.join(root, file)
        message_string = open(filefullname,"rb").read()
        msg = mime.from_string(message_string)
        print
        print "SUBJECT: {0}".format(msg.clean_subject)
        for header, value in msg.headers.iteritems():
            print "    HEADER {0}".format(header)
            print "    VALUE  {0}".format(value)
            print


