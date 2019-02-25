from SQLConnectorMOD import *
from objectsMOD import *
import urllib
import simplejson


class ChangeUtil:

    def __init__(self, host, user, password, dbName, hasDB, status, urlComments):
        # For create database and tables and save datas to database.
        self.sqlConnector = MysqlDBConnector(host, user, password, dbName, hasDB, status)
        self.urlComments = None

    def getStart(self):
        startpoint = self.sqlConnector.getStartPoint()
        return startpoint

    """
        This function converts json string to object classes.
        And save object classes to database.
        """

    def convertToBeans(self, changeJson, urlComments):

        # Url of InlineComments:
        self.urlComments = urlComments
        # Convert json string to a list of Change object.
        changeList = self.convertChange(changeJson)
        # Save Change objects to database.
        self.sqlConnector.saveChanges(changeList)

    """
        This function converts json string to Change object.
        """

    def convertChange(self, changeJson):
        # A list of Change objects
        changeList = []
        for change in changeJson:
            print('Number of Changes .... ' + str(len(changeList)))
            changeObj = Change()
            changeObj.uniqueChangeId = change['id']
            changeObj.changeId = change['change_id']
            # change id number
            changeObj.changeIdNum = change['_number']
            changeObj.project = change['project']
            changeObj.branch = change['branch']
            # topic
            if 'topic' in change.keys():
                changeObj.topic = change['topic']
            else:
                changeObj.topic = ''
            # Some data has no owner information.
            # If there was no owner information, set the authorId as ''.
            if not change['owner']:
                changeObj.authorAccountId = ''
            # If there has owner infromation, set the authorId as the author's id.
            else:
                changeObj.authorAccountId = change['owner']['_account_id']
            changeObj.createdTime = change['created']
            # updatedTime
            if 'updated' in change.keys():
                changeObj.updatedTime = change['updated']
            else:
                changeObj.updatedTime = ''
            changeObj.status = change['status']
            # mergeable
            if 'mergeable' in change.keys():
                changeObj.mergeable = change['mergeable']
            else:
                changeObj.mergeable = ''
            # Get a list of Revision objects.
            changeObj.revisions = self.convertRevisions(change)
            # Get a list of History objects.
            changeObj.histories = self.convertHistories(change)
            changeList.append(changeObj)
        return changeList

    """
        This fuction converts the json string to Revision object.
        """

    def convertRevisions(self, change):
        revisionList = []
        revisionsJson = change['revisions']
        for key, revision in revisionsJson.iteritems():
            revisionObj = Revision()
            revisionObj.revisionId = key
            if 'commit' in revision.keys():
                revisionObj.subject = revision['commit']['subject']
                revisionObj.message = revision['commit']['message']
                revisionObj.authorUsername = revision['commit']['author']['name']
                revisionObj.createdTime = revision['commit']['author']['date']
                revisionObj.committerUsername = revision['commit']['committer']['name']
                revisionObj.committedTime = revision['commit']['committer']['date']
                revisionObj.patchSetNum = revision['_number']
                revisionObj.ref = revision['ref']
            if 'fetch' in revision.keys():
                if 'git' in revision['fetch'].keys():
                    revisionObj.git = revision['fetch']['git']['url']
                else:
                    revisionObj.git = ''
                if 'repo' in revision['fetch'].keys():
                    revisionObj.repo = revision['fetch']['repo']['url']
                else:
                    revisionObj.repo = ''
                if 'anonymous http' in revision['fetch'].keys():
                    revisionObj.http = revision['fetch']['anonymous http']['url']
                elif 'http' in revision['fetch'].keys():
                    revisionObj.http = revision['fetch']['http']['url']
                else:
                    revisionObj.http = ''
                if 'ssh' in revision['fetch'].keys():
                    revisionObj.ssh = revision['fetch']['ssh']['url']
                else:
                    revisionObj.ssh = ''
            if 'files' in revision.keys():
                revisionObj.files = self.convertFiles(revision)

            # Get Comments Inlines of each revision
            revisionObj.inlineComments = self.convertCommentsIlines(change['_number'], revision['_number'])

            # Get a list of File objects.
            revisionList.append(revisionObj)
        return revisionList


    def convertCommentsIlines(self, changeNumber, revisioNumber):
            commentInlinesList = []
            fileComments = urllib.urlopen(self.urlComments % (changeNumber, revisioNumber)).read()[4:]
            inlineCommentsJson = simplejson.loads(fileComments)

            for key, comments in inlineCommentsJson.iteritems():
                    for i in (range(0, len(comments))):
                            message = comments[i]
                            commentInlineObject = InlineComments()
                            # Some data has 'author' key, but some not.
                            # And in the datas have the 'author' key, some have an empty value, and some have values.
                            # So it should be checked.
                            if (not message['author']):
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
                            commentInlineObject.commentId = message['id']
                            commentInlineObject.file = key
                            commentInlineObject.line = message['line']
                            atts = vars(commentInlineObject)
                            # print ', '.join("%s: %s" % item for item in atts.items())
                            commentInlinesList.append(commentInlineObject)

            return commentInlinesList

    """
        This function converts the json string to File object.
        """

    def convertFiles(self, revision):
        fileList = []
        fileJson = revision['files']
        for fileName, fileInfo in fileJson.iteritems():
            fileObj = File()
            fileObj.fileName = fileName
            # Some data has 'lines_inserted' key, but some data did not have.
            # So it should be checked.
            if 'lines_inserted' in fileInfo.keys():
                fileObj.linesInserted = fileInfo['lines_inserted']
            # Same as above, it should be checked.
            if 'lines_deleted' in fileInfo.keys():
                fileObj.linesDeleted = fileInfo['lines_deleted']
            fileList.append(fileObj)
        return fileList

    """
        This function converts json string to History object.
        """

    def convertHistories(self, change):
        historyList = []
        historiesJson = change['messages']
        for i in range(0, len(historiesJson)):
            historyObj = History()
            message = historiesJson[i]
            historyObj.historyId = message['id']
            # Some data has 'author' key, but some not.
            # And in the datas have the 'author' key, some have an empty value, and some have values.
            # So it should be checked.
            if ('author' not in message.keys()) or (not message['author']):
                historyObj.authorAccountId = ''
                historyObj.authorName = ''
                historyObj.authorUserName = ''
                historyObj.email = ''
            else:
                historyObj.authorAccountId = message['author']['_account_id']
                if 'name' in message['author'].keys():
                    historyObj.authorName = message['author']['name']
                if 'username' in message['author'].keys():
                    historyObj.authorUserName = message['author']['username']
                if 'email' in message['author'].keys():
                    historyObj.email = message['author']['email']

            historyObj.message = message['message']
            historyObj.createdTime = message['date']
            if '_revision_number' in message.keys():
                historyObj.patchSetNum = message['_revision_number']

            else:
                if len(historiesJson) > 1:
                    if i is 0:
                        historyObj.patchSetNum = 0
                    else:
                        historyObj.patchSetNum = historyList[i - 1].patchSetNum
                else:
                    historyObj.patchSetNum = 0

            historyList.append(historyObj)
        return historyList