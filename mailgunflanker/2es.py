
from flanker.addresslib import address
from flanker import mime
import os
import json

from base64 import b64encode


emails_path= os.getenv('EMAILS_PATH', "/var/mailgunflanker")
elasticsearch_url = os.getenv('ELASTICSEARCH', "http://localhost:9200")
email_index = os.getenv('ELASTICSEARCH_INDEX', "mailgunflanker")

from elasticsearch import Elasticsearch
es = Elasticsearch([elasticsearch_url])
es.indices.create(index=email_index, ignore=400)

id=0

for root, dirs, files in os.walk(emails_path):
    for file in files:
        id=id+1
        filefullname = os.path.join(root, file)
        message_string = open(filefullname,"rb").read()
        msg = mime.from_string(message_string)
        # add email to elasticsearch
        doc ={}
        doc['subject']=msg.clean_subject
        doc['headers']=[ [header, str(value)] for header, value in  msg.headers.items()]


        if(msg.content_type.is_multipart()):
           doc["parts"]=[]
           doc["attachments"]=[]
           for part in msg.parts:
              if(part.content_type and str(part.content_type).startswith("text/")):
                 doc["parts"].append(
                    {
                       "body":part.body,
                       "headers":[[header, str(value)] for header, value in  part.headers.items()],
                       "content_type":str(part.content_type)
                    }
                 )
              elif(part.body is not None):
                 doc["attachments"].append(
                    {
                       "body": b64encode(part.body),
                       "headers":[[header, str(value)] for header, value in  part.headers.items()],
                       "content_type":str(part.content_type)
                    }
                 )
        else:
           doc['content_type']=str(msg.content_type)
           if (msg.content_type and str(msg.content_type).startswith("text/")):
             doc['body'] =  msg.body
           else:
              doc['binbody'] = msg.body

        res = es.index(index=email_index, doc_type='email', id=id, body=doc)



