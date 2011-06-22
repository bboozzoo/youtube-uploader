#!/usr/bin/env python

try:
    import gdata.service
    import gdata.youtube
    import gdata.youtube.service
except:
    print 'python-gdata is missing'
    raise SystemExit(1)

import sys
import os.path
from optparse import OptionParser
from datetime import datetime
from getpass import getpass

def _upload_file(url, headers_dict, infile):
    """upload a file to given url using POST method
    
    Arguments:
    - `url`:
    - `headers_dict`:
    - `infile`:
    """
    pass

class YoutubeUploaderError(Exception):
    """error
    """
    pass

class YoutubeUploader(object):
    """simple youtube uploader
    """
    CATEGORIES_SCHEME = "http://gdata.youtube.com/schemas/2007/categories.cat"

    def __init__(self, user=None):
        """
        """
        self._files = []
        self._user = user
        self._yt = None
        self._setup_youtube_service()

    def _setup_youtube_service(self, ):
        """initialize youtube service
        """
        self._yt = gdata.youtube.service.YouTubeService()
        self._yt.ssl = False
        self._yt.client_id = "youtube-uploader"
        self._yt.developer_key = "AI39si5UzNe7Hr2F6ZyyTDp75RIsRttefqnhwLXVF4-6Tf7HZY8cTUvBFN_yTstFVuWpa1PxBpvZQJKM2YgFdPo3ptBUhXl5Nw"
        self._yt.source = "youtube-uploader"
        
    def add_video_file(self, filename):
        """add video file for upload
        """
        self._files.append(filename)
    
    def upload(self, ):
        """
        """
        if not self._files:
            raise YoutubeUploaderError("no files to upload?")

        self._yt_login()
        self._yt_upload()

    def _ask_passwd(self, ):
        """ask for user's password
        """
        return getpass()


    def _yt_login(self, ):
        """log into youtube service
        """
        # get user password
        passwd = self._ask_passwd()
        self._yt.email = self._user
        self._yt.password = passwd
        captcha_response = None
        captcha_token = None
        retry = True
        while retry:
            try:
                print "Login with user %s" % (self._user)
                self._yt.ProgrammaticLogin(captcha_token = captcha_token,
                                           captcha_response = captcha_response)
                retry = False
            except gdata.service.CaptchaRequired:
                print "Open the following URL and provide CAPTCHA response:", self._yt.captcha_url
                captcha_token = self._yt.captcha_token
                captcha_response = raw_input("Response: ")
            except Exception, e:
                raise YoutubeUploaderError("failed to login: " + str(e))
            
        
    def _yt_upload(self, ):
        """perform the upload of all files
        """
        for f in self._files:
            self._yt_upload_single(f)

    def _yt_upload_single(self, filename):
        """upload single video
        
        Arguments:
        - `filename`: video file
        """
        print "uploading %s" % (filename)

        name = os.path.basename(os.path.expanduser(filename))
        gd_media = gdata.media.Group(
            title = gdata.media.Title(text = name),
            private = gdata.media.Private(),
            category = [gdata.media.Category(
                    text="People",
                    scheme = self.CATEGORIES_SCHEME,
                    label="People")]
            )
        gd_video = gdata.youtube.YouTubeVideoEntry(media = gd_media)
        
        url, token = self._yt.GetFormUploadToken(gd_video)
        print url, token

        # upload file
        _upload_file(url, headers, filename)
        
if __name__ == '__main__':
    usage = "usage: %prog -u <user> -f <file> [-f <file>]"
    parser = OptionParser(usage=usage)
    parser.add_option("-f", "--file", dest="file_list", action="append",
                      default=[], help="file to upload")
    parser.add_option("-u", "--user", dest="user", default=None,
                      help="username (required)")
    (options, args) = parser.parse_args()

    if not options.user:
        parser.error("missing username")
        raise SystemExit(1)

    if not options.file_list:
        parser.error("files not provided")
        raise SystemExit(1)

    sizes = [os.path.getsize(f) for f in options.file_list]
    total_size = reduce(lambda x, y: x + y, sizes)
    print "%d files for upload, total size: %.2f MB" % (len(options.file_list),
                                                        total_size / 1024.0 / 1024.0)

    yu = YoutubeUploader(options.user)
    [yu.add_video_file(f) for f in options.file_list]
    yu.upload()
    
