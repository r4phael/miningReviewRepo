import simplejson
import urllib
from changeUtilMOD import *

fileChange = open('/home/r4ph/Downloads/detail.json').read()[4:]

change = simplejson.loads(fileChange)


commentInlinesList = []
commentInlinesJson = change['revisions']

url = 'http://review.couchbase.org/changes/104697/revisions/%s/comments'

for k,v in (commentInlinesJson.items()):

    commentInlineObject = InlineComments()
    commentInlineObject.patchSetNum = commentInlinesJson[k]['_number']
    fileComments = urllib.urlopen(url % str(commentInlineObject.patchSetNum)).read()[4:]
    inlineComments = simplejson.loads(fileComments)

    if (len(inlineComments)>0):
        for i in range(0, len(inlineComments['/COMMIT_MSG'])):
            message = inlineComments['/COMMIT_MSG'][i]
            # Some data has 'author' key, but some not.
            # And in the datas have the 'author' key, some have an empty value, and some have values.
            # So it should be checked.
            if ('author' not in message.keys()) or (not message['author']):
                commentInlineObject.authorAccountId = ''
                commentInlineObject.authorName = ''
                commentInlineObject.authorUserName = ''
                commentInlineObject.email = ''
            else:
                commentInlineObject.authorAccountId = message['author']['_account_id']
                if 'name' in message['author'].keys():
                    commentInlineObject.authorName = message['author']['name']
                if 'username' in message['author'].keys():
                    commentInlineObject.authorUserName = message['author']['username']
                if 'email' in message['author'].keys():
                    commentInlineObject.email = message['author']['email']

            commentInlineObject.message = message['message']
            commentInlineObject.updatedTime = message['updated']
            commentInlineObject.unresolved = message['unresolved']

        atts = vars(commentInlineObject)
        print ', '.join("%s: %s" % item for item in atts.items())



