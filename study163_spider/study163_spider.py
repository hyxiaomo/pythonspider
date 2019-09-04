
# coding: utf-8

# In[1]:


import requests
import datetime
import time
import os
from pyquery import PyQuery as pq
import pandas as pd
import numpy as np
import re


# In[2]:


def get_course_headers_json(url_1,headers):
    html_1=requests.get(url_1,headers=headers)
    doc=pq(html_1.text)
    items_1=doc('.inn').items()
    for item in items_1:
        category1_name=item('a[target="_blank"]').attr('data-name')  #第一级类别
        category1_href=item('a[target="_blank"]').attr('href')
        category_index=category1_name+u'_类目框'
        if re.match('^/category.*',str(category1_href)):
            #print(category1_name,category1_href)
            #print('----------------------------')
            param='a[data-index="%s"]' %category_index   #注意不能直接把参数代入到属性值中，那样做其实就是把变量加入到字符串中
            items_2=doc('.links p a').items()
            for dd in items_2:
                category2_name=dd(param).attr('data-name')#最小类别
                category2_href=dd(param).attr('href')
                if re.match('^/category.*',str(category2_href)):
                    category_url='https://study.163.com'+str(category2_href)
                    course_headers={
                        'authority': 'study.163.com',
                        'method': 'POST',
                        'path': '/p/search/studycourse.json',
                        'scheme': 'https',
                        'accept': 'application/json',
                        'accept-encoding': 'gzip, deflate, br',
                        'accept-language': 'zh-CN,zh;q=0.9',
                        'content-length': '162',
                        'content-type': 'application/json',
                        'origin':'https://study.163.com',
                        'referer': category_url,
                        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36'
                    }
                    if category2_name not in ['公务员','教师教职','事业单位','社工等其他公职']:
                        category_id=re.findall('https://study.163.com/category/(\d*)',category_url)[0]
                    else:
                        id_dic={'公务员':'400000001365005','教师教职':'400000001367004','事业单位':'400000001377002','社工等其他公职':'400000001375003'}
                        category_id=id_dic.get(category2_name)
                    course_json={
                            'activityId': '0',
                            'frontCategoryId':category_id,
                            'keyword': '',
                            'orderType': '90',
                            'pageIndex': '1',
                            'pageSize': '50'
                    }
                    yield{
                        'category1_name':category1_name,
                        'category2_name':category2_name,
                        'course_headers':course_headers,
                        'course_json':course_json
                    }


# In[3]:


def get_course(per_course):
    course_url='https://study.163.com/p/search/studycourse.json'
    course_response=requests.post(course_url,headers=per_course.get('course_headers'),json=per_course.get('course_json')).json()
    #有些小类别没有课程
    if course_response.get('result').get('query') is not None:
        totlePageCount=course_response.get('result').get('query').get('totlePageCount')
        new_category_id=per_course.get('course_json').get('frontCategoryId')
        df_course=pd.DataFrame()
        courseID_list=[]
        for page in range(1,totlePageCount+1):
            new_course_json={
                'activityId': '0',
                'frontCategoryId':new_category_id,
                'keyword': '',
                'orderType': '90',
                'pageIndex': page,
                'pageSize': '50',
            }
            new_course_response=requests.post(course_url,headers=per_course.get('course_headers'),json=per_course.get('course_json')).json()
            lists=new_course_response.get('result').get('list')
            for per in lists:
                courseId=per.get('courseId')
                courseID_list.append(courseId)
                course={}
                course['课程名']=per.get('productName')
                course['讲师']=per.get('lectorName')
                course['课程价格(原价)']=per.get('originalPrice')
                course['课程价格(现价)']=per.get('discountPrice')
                course['课程学过人数']=per.get('learnerCount')
                course['课程ID']=courseId
                course['爬取时间']=time.strftime('%Y-%m-%d',time.localtime(time.time()))
                df_course=df_course.append(course,ignore_index=True)
    else:
        df_course=None
        courseID_list=None
    return df_course,courseID_list


# In[4]:


def get_comment(per_course):
    df1,idlist=get_course(per_course)
    if df1 is not None:
        df2=pd.DataFrame()
        for ID in idlist:
            comment_url='https://study.163.com/dwr/call/plaincall/AskCommentBean.getOnePageComment.dwr'
            comment_headers={
            'content-type': 'text/plain',
            'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'
            }
            comment_data={
            'callCount':'1',
            'scriptSessionId':'${scriptSessionId}190',
            'httpSessionId':'1a444f6986eb42458d4402f29fa05c20',
            'c0-scriptName':'AskCommentBean',
            'c0-methodName':'getOnePageComment',
            'c0-id':'0',
            'c0-param0':'string:'+str(ID),#每个课程ID不同
            'c0-param1':'number:30',
            'c0-param2':'number:1',#页码
            'batchId':'1560762770083'#任意时间戳(最好是最新的时间)
            }
            comment_response=requests.post(comment_url,data=comment_data,headers=comment_headers).content.decode("unicode_escape")
            allPageCount=int(re.findall('totlePageCount=(.*?);',comment_response)[0])
            date_list=[]
            for comment_page in range(1,allPageCount+1):
                new_comment_data={
                'callCount':'1',
                'scriptSessionId':'${scriptSessionId}190',
                'httpSessionId':'1a444f6986eb42458d4402f29fa05c20',
                'c0-scriptName':'AskCommentBean',
                'c0-methodName':'getOnePageComment',
                'c0-id':'0',
                'c0-param0':'string:'+str(ID),#每个课程ID不同
                'c0-param1':'number:30',
                'c0-param2':'number:'+str(comment_page),#页码
                'batchId':'1558168893181'#任意时间戳
                }
                comment_response=requests.post(comment_url,data=new_comment_data,headers=comment_headers).content.decode("unicode_escape")
                c_time=re.findall('gmtCreate=(.*?);',comment_response)
                #print(allPageCount,comment_url,new_comment_data,comment_headers)
                if len(c_time) != 0:
                    date_list.append(min(c_time))
                else:
                    date_list.append(np.nan)
            min_comment_date=min(date_list)
            if min_comment_date == min_comment_date:
                timeArray=time.localtime(int(min_comment_date)/1000)
                comment_date=time.strftime('%Y-%m-%d %H:%M:%S',timeArray)
            else:
                comment_date=None
            comment={}
            comment['课程ID']=ID
            comment['最早评论时间']=comment_date
            df2=df2.append(comment,ignore_index=True)
        df=pd.merge(df1,df2,on='课程ID',how='left')
    else:
        df=None
    return df


# In[5]:


def main():
    url_1='https://study.163.com/'
    headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'}
    for per_course in get_course_headers_json(url_1,headers):   
        file_name='D:\\老板\\老板\\需要爬取的数据\\网易云\\'+str(per_course.get('category1_name'))+'\\' #文件保存路径
        if '/' in file_name:
            file_name=file_name.replace('/','')
        if not os.path.exists(file_name): 
            os.mkdir(file_name)
        file_path='{}.{}'.format(file_name+str(per_course.get('category2_name')),'csv')
        if  '/' in file_path:
            file_path=file_path.replace('/','')
        try:
            data=get_comment(per_course)
        except Exception as e:
            print(per_course.get('category1_name'),per_course.get('category2_name'),e)
        if data is not None:
            data.drop(['课程ID'],axis=1,inplace=True)
            data.to_csv(file_path,index=False,encoding='utf_8_sig')
            print(per_course.get('category1_name'),per_course.get('category2_name'),'ok')
        else:
            continue


# In[6]:


if __name__ == '__main__':
    main()

