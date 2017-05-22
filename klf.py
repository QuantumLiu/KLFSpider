# -*- coding: utf-8 -*-
"""
Created on Sun May 21 20:29:40 2017

@author: Quantum Liu
"""

import requests
import re
import pickle
import markdown
import codecs
from multiprocessing import Pool,cpu_count,freeze_support
import os
class player():#每个运动员都是一个player类
    def __init__(self,info_dic,info,pic_url):
        self.info_dic=info_dic
        self.info=info
        self.pic_url=pic_url
        self.name=self.info_dic.get('姓名')
        self.dir_name='./'+self.info_dic.get('姓名')
        self.info_file=self.dir_name+'/'+'info.md'
    def mkdir(self):#创建运动员目录
        if not os.path.exists(self.dir_name):
            os.mkdir(self.dir_name)
    def saveimg(self):#保存头像图片
        self.pic_path=self.dir_name+'/'+'head.png'
        data=requests.get(self.pic_url).content
        with open(self.pic_path,'wb') as f:
            f.write(data)
    def saveasmd(self):#生成个人.md文档
        with open(self.info_file,'w',encoding='utf-8') as f:
            head='# '+self.info_dic.get('姓名')
            pic_link='  \r![pic](./head.png)  \r'
            upic_link='  \r![pic]('+self.pic_path+')  \r'
            self.mdtext=head+pic_link+self.info#个人markdown文本内容
            self.umdtext=head+upic_link+self.info#合集的markdown内容
            f.write(self.mdtext)
def player_info(page_text=''):
    info=''
    r_att=r' <li><span>(.*?)</span>'#属性名称正则
    r_name=r'<div class="uk-width-2-3 info"> <h1><img src=".*?">(.*?)</h1> '
    r_gain=r'<h3 class="chengji">(.*?)</h3>'
    r_rank=r'<!-- <h3 class="paiming">(.*?)</h3>'
    r_pic=r'<div class="uk-width-1-3 avatar"> <img src="(.*?)" alt='
    att_list=re.findall(r_att,page_text)[0:8]
    att_list.remove('社交')#社交这一项信息无用
    dic={}.fromkeys(att_list)
    pic_url='http://www.kunlunjue.com'+re.findall(r_pic,page_text)[0]
    name=re.findall(r_name,page_text)[0]
    gain=re.findall(r_gain,page_text)[0]
    rank=re.findall(r_rank,page_text)[0]
    dic['全名']=name
    dic['战绩']=gain
    dic['排名']=rank
    info+='全名:'+name+'  \r'+'战绩:'+gain+'  \r'+'排名:'+rank+'  \r'
    for att in att_list:
        r=r'<li><span>'+att+'</span>([\s\S]*?)</li>'#属性内容正则
        value=re.findall(r,page_text)[0].replace('\n','  \r')#将换行改为markdown格式
        info+=att+':'+value+'  \r'
        dic[att]=value
    return (dic,info,pic_url)
def processing(page_url=''):#想不出函数名的时候就叫它processing吧
    page_text=requests.get(page_url).text
    info_dic,info,pic_url=player_info(page_text=page_text)
    p=player(info_dic,info,pic_url)
    p.mkdir()
    p.saveimg()
    p.saveasmd()
    return p#返回一个player对象
if __name__ == '__main__':
    freeze_support()
    #全体自由搏击选手或者全部项目运动员的索引页的HTML内容
    free_sparring_only=True
    index_root=('http://www.kunlunjue.com/portal/player/player_fall/level/all/national/all/height/all/order/any/desc/des/type/%E8%87%AA%E7%94%B1%E6%90%8F%E5%87%BB/p/' if free_sparring_only else 'http://www.kunlunjue.com/portal/player/player_fall/level/all/national/all/height/all/order/any/desc/des/type/all/p/')
    ran=(26 if free_sparring_only else 37)
    all_page_text=''.join([requests.get(page).text.encode('ISO-8859-1').decode('utf-8') for page in [index_root+str(int(i+1))+'.html' for i in range(ran)]])
    r_player_info_page=r'</a></li><li><a href="(.*?)" title="'#详情页的正则
    info_page_list=['http://www.kunlunjue.com/'+url for url in re.findall(r_player_info_page,all_page_text)]#所有详情页
    pool=Pool(cpu_count())#根据cpu最大线程数创建并行池
    player_list=[]
    for page_url in info_page_list:
        player_list.append(pool.apply_async(processing,(page_url,)))
    pool.close()
    pool.join()
    player_list=[result.get() for result in player_list]
    uni_mdetext=''.join([p.umdtext for p in player_list])#全集的md文本
    with codecs.open('./uni_data.md','w',encoding='utf-8') as f:
        f.write(uni_mdetext)
    htmltext='<meta http-equiv="content-type" content="text/html; charset=UTF-8">  \r'+markdown.markdown(uni_mdetext)
    with codecs.open('./uni_data.html',mode='w',encoding='utf-8') as f:
        f.write(htmltext)
    with open('./players.pkl','wb') as f:#保存运动员player对象的列表
        pickle.dump(player_list,f)