import json
import codecs
import datetime
import os.path
import logging
import argparse
try:
    from instagram_private_api import (
        Client, ClientError, ClientLoginError,
        ClientCookieExpiredError, ClientLoginRequiredError,
        __version__ as client_version)
except ImportError:
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from instagram_private_api import (
        Client, ClientError, ClientLoginError,
        ClientCookieExpiredError, ClientLoginRequiredError,
        __version__ as client_version)


def to_json(python_object):
    if isinstance(python_object, bytes):
        return {'__class__': 'bytes',
                '__value__': codecs.encode(python_object, 'base64').decode()}
    raise TypeError(repr(python_object) + ' is not JSON serializable')


def from_json(json_object):
    if '__class__' in json_object and json_object['__class__'] == 'bytes':
        return codecs.decode(json_object['__value__'].encode(), 'base64')
    return json_object


def onlogin_callback(api, new_settings_file):
    cache_settings = api.settings
    with open(new_settings_file, 'w') as outfile:
        json.dump(cache_settings, outfile, default=to_json)
        print('SAVED: {0!s}'.format(new_settings_file))


if __name__ == '__main__':

    logging.basicConfig()
    logger = logging.getLogger('instagram_private_api')
    logger.setLevel(logging.WARNING)

    # Example command:
    # python examples/savesettings_logincallback.py -u "yyy" -p "zzz" -settings "test_credentials.json"
    parser = argparse.ArgumentParser(description='login callback and save settings demo')
    parser.add_argument('-settings', '--settings', dest='settings_file_path', type=str, required=True)
    parser.add_argument('-u', '--username', dest='username', type=str, required=True)
    parser.add_argument('-p', '--password', dest='password', type=str, required=True)
    parser.add_argument('-debug', '--debug', action='store_true')

    args = parser.parse_args()
    if args.debug:
        logger.setLevel(logging.DEBUG)

    print('Client version: {0!s}'.format(client_version))

    device_id = None
    try:

        settings_file = args.settings_file_path
        if not os.path.isfile(settings_file):
            # settings file does not exist
            print('Unable to find file: {0!s}'.format(settings_file))

            # login new
            api = Client(
                args.username, args.password,
                on_login=lambda x: onlogin_callback(x, args.settings_file_path))
        else:
            with open(settings_file) as file_data:
                cached_settings = json.load(file_data, object_hook=from_json)
            print('Reusing settings: {0!s}'.format(settings_file))

            device_id = cached_settings.get('device_id')
            # reuse auth settings
            api = Client(
                args.username, args.password,
                settings=cached_settings)

    except (ClientCookieExpiredError, ClientLoginRequiredError) as e:
        print('ClientCookieExpiredError/ClientLoginRequiredError: {0!s}'.format(e))

        # Login expired
        # Do relogin but use default ua, keys and such
        api = Client(
            args.username, args.password,
            device_id=device_id,
            on_login=lambda x: onlogin_callback(x, args.settings_file_path))

    except ClientLoginError as e:
        print('ClientLoginError {0!s}'.format(e))
        exit(9)
    except ClientError as e:
        print('ClientError {0!s} (Code: {1:d}, Response: {2!s})'.format(e.msg, e.code, e.error_response))
        exit(9)
    except Exception as e:
        print('Unexpected Exception: {0!s}'.format(e))
        exit(99)

    # Show when login expires
    cookie_expiry = api.cookie_jar.auth_expires
    print('Cookie Expiry: {0!s}'.format(datetime.datetime.fromtimestamp(cookie_expiry).strftime('%Y-%m-%dT%H:%M:%SZ')))


    class User(object):
        username = ""
        userid =""
        profile_img = ""
        following = ""
        followers = ""
        isPrivate =""
        isVerified = ""
        fullName = ""
        bio =""
        isBusiness = ""
        taggedin = ""
        posts =""

        def __init__ (self, userid,username,profile_img,following,followers,isPrivate,isVerified,fullName,bio,isBusiness,taggedin,posts):
            self.userid=userid
            self.username=username
            self.profile_img=profile_img
            self.following=following
            self.followers=followers
            self.isPrivate=isPrivate
            self.isBusiness=isBusiness
            self.isVerified=isVerified
            self.fullName=fullName
            self.bio= bio
            self.taggedin=taggedin
            self.posts=posts

        def to_String(self):
            print("userid : "+str(self.userid))
            print("username : "+self.username)
            print("profile image : "+self.profile_img)
            print("Full Name : "+self.fullName)
            print("Biography : "+self.bio)
            print("followers : "+str(self.followers))
            print("following : "+str(self.following))
            print("post count : "+str(self.posts))
            print("tagged in count : "+str(self.taggedin))
            print("isPrivate : "+str(self.isPrivate))
            print("isVerified : "+str(self.isVerified))
            print("isBusiness : "+str(self.isBusiness))


    def getUserDetails(username):
        result=api.username_info(username)
        user= User(result["user"]["pk"],result["user"]["username"],result["user"]["hd_profile_pic_url_info"]["url"],result["user"]["following_count"],result["user"]["follower_count"],result["user"]["is_private"],result["user"]["is_verified"],result["user"]["full_name"],result["user"]["biography"],result["user"]["is_business"],result["user"]["usertags_count"],result["user"]["media_count"])
        return user


    def find_tagged_posts(userid,searchUser):
            f= open(searchUser+".txt","a+") 
            tagged_posts=[]
            count=0
            res= api.user_feed(userid)
            tagged_posts.extend(res.get("items",[]))
            next_max_id=res.get("next_max_id")
            while next_max_id:
                res=api.user_feed(userid,max_id=next_max_id)
                tagged_posts.extend(res.get("items",[]))
                next_max_id=res.get("next_max_id")

            for i in tagged_posts:
                if "carousel_media" in i:
                    for cm in i["carousel_media"]:
                        # print(cm["image_versions2"]["candidates"][0]["url"])
                        if "usertags" in cm:
                            tag=cm["usertags"]["in"]

                            for u in tag:
                                try:
                                    uname=u.get("user").get("username")
                                except:
                                    uname=""
                                try:
                                    caption=i["caption"]["text"]
                                except:
                                    caption=""
                                if searchUser in uname or searchUser in caption:
                                    f.write(cm["image_versions2"]["candidates"][0]["url"])
                                    count +=1
                    continue


                if "usertags" in i:
                    tag=i["usertags"]["in"]

                    for u in tag:
                        try:
                            uname=u.get("user").get("username")
                        except:
                            uname=""
                        try:
                            caption=i["caption"]["text"]
                        except:
                            caption=""
                        if searchUser in uname or searchUser in caption:
                            for pot in tag:
                                potential_followers.add(u.get("user").get("username"))
                            f.write(i["image_versions2"]["candidates"][0]["url"]+"\n")
                            print (potential_followers)
                            count +=1
                        
            print ("Found "+str(count)+ " matching media")


    


    def get_followers(userid):
        followers=[]
        rank_token = Client.generate_uuid()
        res=api.user_following(userid,rank_token)
        
        followers.extend(res.get("users",[]))
        next_max_id=res.get("next_max_id")
        while next_max_id:
            res=api.user_following(userid,rank_token,max_id=next_max_id)
            followers.extend(res.get("users",[]))
            next_max_id=res.get("next_max_id")
        return followers





    # Call the api
    def find_private_posts(searchUser,searchFor):

        followers=[]
        user=getUserDetails(searchUser)
        print("Searching "+user.username)
        find_tagged_posts(api.user_info(user.userid)["user"]["pk"],searchFor)
        
        followers=get_followers(user.userid)



        

        if followers == []:
            print (searchUser+" is private.. Unable to access followers")
        
        for follower in followers:
            try:
                print("Searching "+follower["username"] + " " +follower ["full_name"] )
                if(follower["is_private"]):
                    print(follower["username"] + " is private.. skipping..")
                    print("\n")
                    continue
                find_tagged_posts(follower["pk"],searchFor)
                print("\n")
            except:
                continue


 

    potential_followers=set()
    searchUser= input("Enter user to search in (public account) : ")
    searchFor = input("Enter user to search for (private account): ")
    find_private_posts(searchUser,searchFor)

    num_photos = sum(1 for line in open('myfile.txt'))
    print("Found "+num_photos+" photos with "+searchFor)
    print("Some other people that might have picture are ")
    for p in potential_followers:
        print(p)
    
    choice = input("Would you like to search these as well? (y/n)")
    if "y" in choice:
        for p in potential_followers:
            find_private_posts(p,searchFor)
    else:
        print("quitting...")



   

