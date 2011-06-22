#!/usr/bin/env python

try:
    import gdata.service
    import gdata.youtube
    import gdata.youtube.service
except:
    print 'python-gdata is missing'
    raise SystemExit(1)

try:
    import pycurl
except:
    print 'pycurl is missing'
    raise SystemExit(1)

import sys
import os.path
import StringIO
from optparse import OptionParser
from datetime import datetime
from getpass import getpass

def _upload_file(url, items_dict, infile):
    """upload a file to given url using POST method
    
    Arguments:
    - `url`:
    - `headers_dict`:
    - `infile`:
    """
    def progress(download_t, download_d, upload_t, upload_d):
#        print "dt: {} dd: {} ut: {} ud: {}".format(download_t,
#                                                   download_d,
#                                                   upload_t,
#                                                   upload_d)
        if upload_t:
            perc = 100.0 * upload_d / upload_t
            fname = os.path.basename(infile)
            sys.stdout.write("{} {:3.0f} % {:d}/{:d} \r".format(fname,
                                                                perc,
                                                                int(upload_d),
                                                                int(upload_t)))
            sys.stdout.flush()

    c = pycurl.Curl()
    url = url + "?nexturl=http://google.com"
    c.setopt(pycurl.URL, url)
    # pretend we're doing browser upload
    items = items_dict.items()
    items.append((os.path.basename(infile), 
                  (pycurl.FORM_FILE, infile)))
    c.setopt(pycurl.HTTPPOST, items)

    # progress
    c.setopt(pycurl.NOPROGRESS, 0)
    c.setopt(pycurl.PROGRESSFUNCTION, progress)

    # need to check header if redirection to nexturl was ok
    header = StringIO.StringIO()
    c.setopt(pycurl.HEADERFUNCTION, header.write)
    # upload
    c.perform()
    # newline after showing progress
    print "\n"

    hlines = header.getvalue().splitlines()
    # look for location
    hentries = dict([line.split(":", 1) for line in hlines if ":" in line])
    if not "Location" in hentries:
        raise YoutubeUploaderError("Location not found in header??")
    loc = hentries["Location"]
    loc_param = loc.split("?", 1)[1]
    get_dict = dict([entry.split("=") for entry in loc_param.split("&") if "=" in entry])
    if not "status" in get_dict:
        raise YoutubeUploaderError("status missing from Location: " 
                                   + hentries["Location"])
    status = int(get_dict["status"])

    # HTTP return needs to be 302 and status from Location needs to be 200
    if c.getinfo(pycurl.HTTP_CODE) != 302 or \
            status != 200:
        return False

    return True

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
                print "--- Login with user %s" % (self._user)
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
        print "--- Uploading %s" % (filename)

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
        #print url, token

        # upload file
        if _upload_file(url, {"token" : token } , filename):
            print "   done"
        else:
            print "   failed"
        
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
    
