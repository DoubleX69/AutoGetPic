#! /usr/bin/python3

import platform
import urllib
import requests
from requests.adapters import HTTPAdapter
try:
    import cookielib
except:
    import http.cookiejar as cookielib
import re
import time
import os.path
try:
    from PIL import Image
except:
    pass
from bs4 import element
from bs4 import BeautifulSoup
import random
from peewee import *


database = MySQLDatabase('database', **{'host': 'localhost', 'port': 3306, 'user': 'root', 'password': 'password'})

class UnknownField(object):
    def __init__(self, *_, **__): pass

class BaseModel(Model):
    class Meta:
        database = database

class Image(BaseModel):
    get_date = DateTimeField()
    score = IntegerField(null=True)

    class Meta:
        db_table = 'image'    



database.connect()

if platform.system() == 'Windows' :
    path_pre = 'D:/download_pic/'
else :
    path_pre = '/home/download_pic/'


agent   = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:56.0) Gecko/20100101 Firefox/56.0'
headers = {
    "Host": "xxxx.xx",
    "Referer": "https://xxxx.xx/user/login",
    'User-Agent': agent
}

pic_headers = {
    "Host"      : "files.xxxx.xx",
    "Referer"   : "https://xxxx.xx/user/login",
    'User-Agent': agent,
    'Pragma'    : 'no-cache',
    'Cache-Control' : 'no-cache',
}

vote_headers = {
    "Host": "xxxx.xx",
    "Referer": "https://xxxx.xx/user/login",
    'User-Agent': agent
}

timeout = 600
already_cnt =0
get_pic_count = 0;

session = requests.session()
session.cookies = cookielib.LWPCookieJar(filename='cookies')
try:
    session.cookies.load(ignore_discard=True)
except:
    print("Warning:Cookie 未能加载")

session.mount('http://', HTTPAdapter(max_retries=10))
session.mount('https://', HTTPAdapter(max_retries=10))

def sleepSec():
    sec = random.uniform( 20 , 100 )
    time.sleep(sec)
    
def getValidFileName( file_name ):
    unvalid_filename_char={'\\','/',':','*','?','"','<','>','|'}
    
    for c in unvalid_filename_char:
        file_name = file_name.replace( c , '_' )
    
    max_pre_path = path_pre  ;
    max_filename_len = 256 - len(max_pre_path) - 4;
    filename_len = len(file_name)
    
    if filename_len > max_filename_len :
        file_ext = file_name[-4:]
        file_name = file_name[0:max_filename_len] + file_ext
    return file_name
    
def get_authenticity_token():
    '''获取登录需要的token'''
    login_url = "https://xxxx.xx/user/login"
    try:
        login_page= session.get( login_url , headers = headers , timeout = timeout )
    except:
        print("Error: get " , login_url , "timeout")
    soup = BeautifulSoup( login_page.content.decode('utf-8','ignore'),'lxml')
    auth_token = soup.find( 'meta',{'name':'token'} ).get('content')
    #print(auth_token)
    return auth_token
    
def isLogin():
    '''判断是否已经登陆'''
    home_url = "https://xxxx.xx/user/home"
    try:
        home_page = session.get( home_url ,headers = headers , timeout = timeout )
    except:
        print("Error:get " , home_url , "timeout")
    soup = BeautifulSoup( home_page.content.decode('utf-8','ignore'),'lxml')
    my_profile = soup.find('li',text='My Profile')
    if my_profile:
        return True
    else:
        return False
        
        
def Login():
    '''登陆网站'''
    login_url = 'https://xxxx.xx/user/authenticate'
    auth_token = get_authenticity_token()
    post_data = {
        'authenticity_token' : auth_token,
        'url'                : '',  
        'user[name]'         : 'user_name',
        'user[password]'     : 'password',
        'commit'             : 'Login',
    }
    headers["Referer"] = "https://xxxx.xx/user/login"
    try:
        login_page = session.post( login_url , data=post_data,headers=headers ,timeout = timeout )
    except:
        print("Login Fail!!!")
    session.cookies.save()
  
def getScore( score ):
    try :
        score = int(score)
        if score > 50:
            my_score =  '3';
        else :
            my_score =  random.choice ( ['1', '2'] )
    except:
        my_score =  random.choice ( ['1', '2'] )
    
    return my_score
        
  
def insertImageDB( id , score ):
    try:
        id = int(id)
        score = int(score)
        Image.create(id=id,score=score)
        print("Info: insert p" , id , "to database success")
        return True 
    except:
        print("Error: insert p" , id , "to database fail!!")
        return False

def selectFromDbById( id ):
    try :
        id = int(id)
        ret =  Image.select().where( Image.id == id )
        if len(ret) > 0:
            print("Info: p",id,"is in database")
            return True
        else :
            return False
    except:
        print(" Error:Find p",id," Fail!!")
        return False   
        
def getMoePic():
    for p in range(1,30,1) :
        if already_cnt < 40:
            getPostPic(p)
        else:
            break;
    print("Info： ======= 这次一共获取了",get_pic_count,"张图片 ============")
                
   
def getPostPic( page = 1 ):
    '''爬取图片''' 
    time.sleep(random.uniform( 5 , 60 ))
    post_url = 'https://xxxx.xx/post?page=' + str(page)
    headers["Referer"] = "hhttps://xxxx.xx/user/home"

    try:
        post_page = session.get( post_url , headers=headers , timeout = timeout)
    except:
        print("Error:get post page fail!!")
        return
    soup = BeautifulSoup( post_page.content.decode('utf-8','ignore'),'lxml')
    post_list = soup.find('ul',{'id':'post-list-posts'})
    all_pic = post_list.find_all('li')
    print("Info:获取第",page,"页 post page")
    for pic in all_pic :
        pic_title = pic.find('img',{'class':'preview'}).get('title')
        pattern = '^Rating: (\w+) Score: (\w+) Tags: (.*?) User: (\w+)$'
        s = re.match(pattern,pic_title)
        if s :
            pic_rate = s.group(1)
            pic_score = s.group(2)
            pic_tag = s.group(3)
            pic_user = s.group(4)
        else :
            pic_rate = 'Safe'
            pic_score = 20
            pic_tag = 'tagme'
            pic_user = 'user'
        try:
            pic_score = int(pic_score)
        except:
            pic_score = 20
        id = pic.get('id')
        id = id[1:]     #移除id前的p字符
        headers["Referer"] = post_url
        parseShowPage( id , pic_rate , pic_score )
        #print("Sleep.....")
        sleepSec()
        #print("Sleep Done.....")
    print("Info:第",page,"页图片已全部获取")       
 
def getDownloadURL( show_soup ):
    '''获取图片的下载url'''
    download_soup = show_soup.find_all('a',text=re.compile("Download"))
    image_soup = show_soup.find_all('a',text=re.compile("Image"))
    if len(download_soup) == 2:
        pic_soup = download_soup[1]
    elif len(download_soup) == 1:
        pic_soup = download_soup[0]
    elif len(image_soup) > 0 :
        pic_soup = image_soup[0]
    else:
        pic_soup = None
    
    if pic_soup :
        return pic_soup.get('href')
    else :
        return None
        
    

    
def parseShowPage( id , rating , score ):
    print("Info:进入 " , id , "页面")  
    show_url  = 'https://xxxx.xx/post/show/' + str(id)
    try:
        show_page = session.get( show_url , headers=headers , timeout = timeout )
    except:
        print("Error:get " , show_url , " timeout")
        return
    show_soup = BeautifulSoup(show_page.content.decode('utf-8','ignore'),'lxml')
    global already_cnt;
    global get_pic_count;
    if isAlreadyGet( show_soup ,id ) :
        print('Warning:p',id,'is already Get .')
        already_cnt = already_cnt + 1
        return 
    else :
        get_pic_count = get_pic_count + 1;

    auth_token = show_soup.find( 'meta',{'name':'token'} ).get('content')
    pic_url = getDownloadURL( show_soup )
    if pic_url:
        pic_name = pic_url.split('/')[-1]
    else :
        print("Error:Can't Find p" , id , "Download URL!!")
        return 
    pic_name = urllib.parse.unquote(pic_name)
    pic_name = getValidFileName( pic_name )
    if rating == 'Rank' :
        path = path_pre + 'Rank/' + pic_name
    else :
        path = path_pre + pic_name          
    pic_headers["Referer"] = show_url
    print("Info:获取图片中..........")
    try:
        pic_img = session.get( pic_url , headers=pic_headers , timeout = (timeout*3) )
    except:
        print(" Error:get image timeout!!!")
        return 
    print("Info:写入图片..........")  

    with open( path , 'wb' ) as f:
        f.write(pic_img.content)
        f.close()
    
    myscore = getScore( score )
    if insertImageDB( id , myscore ) :
        voteScore( id , myscore , auth_token )   
    else :
        voteScore( id , '3' , auth_token )
    
  
def voteScore( id , score , auth_token ):
    '''投票给图片'''
    my_score = str(score)    
    vote_data = {
        'id':id,
        'score':my_score,
    }
    vote_url = 'https://xxxx.xx/post/vote.json'
    vote_headers["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"
    vote_headers["Content-Length"] = "17"
    vote_headers["X-CSRF-Token"] =  auth_token
    print("info : vote " , my_score , "to p" , id )
    time.sleep(random.uniform( 5 , 60 ))
    try:
        vote_page = session.post( vote_url , data = vote_data , headers=vote_headers , timeout = timeout )
    except:
        print("Error : vote timeout!!!")
  
def isAlreadyGet( show_soup , show_id ) :
    '''判断是否已经获取了此id的图片'''
    if selectFromDbById( show_id ):
        return True
    else :
        favorited_soup = show_soup.find('span',{'id':'favorited-by'})
        flag_soup = favorited_soup('a',text='user_name')
        if flag_soup :
            return True
        else :
            return False
    

if __name__ == '__main__':
    print(">>>>>>>>> 开始运行 <<<<<<<<<")
    if isLogin():
        print("Info:已经登陆")
    else:
        print("Info:正在登陆")
        time.sleep( random.uniform( 3 , 10 ) )
        Login()
    getMoePic()
    
    
    
    
