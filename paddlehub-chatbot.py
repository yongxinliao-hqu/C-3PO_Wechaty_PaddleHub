from collections import deque
import os
import asyncio
import cv2
import requests
import random
import json
from hashlib import md5
from PIL import Image
import numpy as np

import random

from wechaty import (
    Contact,
    FileBox,
    Message,
    Wechaty,
    ScanStatus,
)

from wechaty_puppet import MessageType

# Initialize a PaddleHub plato-mini model
import paddlehub as hub
model = hub.Module(name='plato-mini', version='1.0.0')
model._interactive_mode = True
model.max_turn = 10
model.context = deque(maxlen=model.max_turn)

function_chosen = 0

#删掉上次翻译结果文件
def clean_previous_reslults(path):
    for root,dirs,files in os.walk(path): 
        for file in files: 
            if 'translation' in file:
                os.remove(os.path.join(root,file))
#加载每个目标字母的路径到target_letters_list中
def load_target_letters(target_letters_path):
    target_letter_list = []
    for root,dirs,files in os.walk(target_letters_path): 
        for file in files: 
            target_letter_list.append(os.path.join(root,file))
    print("############# target_letter_list #############")
    print("Number of target letters and symbols: " + str(len(target_letter_list)))
    print(target_letter_list)
    return target_letter_list

# 加载源句子的字母到source_letters_list中
def load_source_letters(sentence):
    source_letter_list = list(sentence)
    print("\n############# source_letter_list #############")
    print("Number of source letters: " + str(len(source_letter_list)))
    print(source_letter_list)
    return source_letter_list

# 将source_letters_list中的字母与target_letters_list中的字母进行映射，并存入final_letters_list
def translation(source_letters_list, target_letters_path, target_letters_list):
    final_letters_list = []
    for i in range(len(source_letters_list)):
        y = source_letters_list[i]
        for j in range(len(target_letters_list)):
            x = target_letters_list[j].replace(target_letters_path,'')[0]
            if not x == '_': # 文件名中带"_"的是标点符号，其余是字母
                if x.lower() == y or x.upper() == y: # 不区分大小写
                    final_letters_list.append(target_letters_list[j])
            elif y == ' ' and 'Aurebesh/_blank.png' in target_letters_list[j]:
                final_letters_list.append(target_letters_list[j])
            elif y == ',' and 'Aurebesh/_comma.png' in target_letters_list[j]:
                final_letters_list.append(target_letters_list[j])
            elif y == '.' and 'Aurebesh/_period.png' in target_letters_list[j]:
                final_letters_list.append(target_letters_list[j])
            elif y == '?' and 'Aurebesh/_question_mark.png' in target_letters_list[j]:
                final_letters_list.append(target_letters_list[j])
            elif y == '!' and 'Aurebesh/_exclamation_mark.png' in target_letters_list[j]:
                final_letters_list.append(target_letters_list[j])
            elif y == ':' and 'Aurebesh/_colon.png' in target_letters_list[j]:
                final_letters_list.append(target_letters_list[j])
            elif y == ';' and 'Aurebesh/_semicolon.png' in target_letters_list[j]:
                final_letters_list.append(target_letters_list[j])
            elif y == '-' and 'Aurebesh/_dash.png' in target_letters_list[j]:
                final_letters_list.append(target_letters_list[j])
            elif y == '\'' and 'Aurebesh/_left_single_quotation_mark.png' in target_letters_list[j]:
                final_letters_list.append(target_letters_list[j])
            elif y == '\"' and 'Aurebesh/_left_double_quotation_mark.png' in target_letters_list[j]:
                final_letters_list.append(target_letters_list[j])
            elif y == '(' and 'Aurebesh/_left_parenthesis.png' in target_letters_list[j]:
                final_letters_list.append(target_letters_list[j])
            elif y == ')' and 'Aurebesh/_right_parenthesis.png' in target_letters_list[j]:
                final_letters_list.append(target_letters_list[j])
    print("\n############# final_letters_list #############")
    print(final_letters_list)
    return final_letters_list

# 目标字母图像拼接
def join_letters(letter_each_line, final_letters_list):   
    line_count = 0 # 总行数
    ims = [] # 图片list
    letter_total = len(final_letters_list) # 总字母数
    width = 150 # 单幅图像宽
    height = 108 # 单幅图像高
    
    # 打印待拼接图片数量
    print("\n############# number of letters to join #############")
    print("Number of letters to join: " + str(letter_total))
    
    # 依据每行字母数计算总行数
    if letter_total % letter_each_line == 0:
        line_count = int(letter_total / letter_each_line)
    else:
        line_count = int(letter_total / letter_each_line + 1)
    
    # 获取所有字母图像，转化为同一尺寸
    for i in range (letter_total):
        im_list = [Image.open(final_letters_list[i])] 
        #图片转化为相同的尺寸
        for im in im_list:
            new_img = im.resize((width, height), Image.BILINEAR)
            ims.append(new_img)
    
    # 创建一个大空白图（最终输出图片）
    result = Image.new(ims[0].mode, (width * letter_each_line, height * line_count))
    
    # 创建每一行的空白长图
    for i in range (line_count):
        result_a_line = Image.new(ims[0].mode, (width * letter_each_line, height ))
        # 拼接每一行的图片
        for j in range (letter_each_line):
            if i*letter_each_line+j < len(ims):
                result_a_line.paste(ims[i*letter_each_line+j], box=(j * width,0))
        # 将每一行的图片拼入最终输出图片
        result.paste(result_a_line, box=(0,i*height))
   
   
    # 打印最终输出图片大小
    print("\n############# result size #############")
    print(result.size)
    
    # 保存最终输出图片
    result.save('./image/translation.png')

# 配置参数：appid, appkey, url
appid = 'your own appid'
appkey = 'your own appkey'
endpoint = 'http://api.fanyi.baidu.com'
path = '/api/trans/vip/translate'
url = endpoint + path

# Generate salt and sign
def make_md5(s, encoding='utf-8'):
    return md5(s.encode(encoding)).hexdigest()

salt = random.randint(32768, 65536)

# 翻译英文到中文
def translate_en_to_zh(query):
    # For list of language codes, please refer to `https://api.fanyi.baidu.com/doc/21`
    from_lang = 'en'
    to_lang =  'zh'
    sign = make_md5(appid + query + str(salt) + appkey)

    # Build request
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    payload = {'appid': appid, 'q': query, 'from': from_lang, 'to': to_lang, 'salt': salt, 'sign': sign}

    # Send request
    r = requests.post(url, params=payload, headers=headers)
    result = r.json()
    
    # Show response
    print(json.dumps(result, indent=4, ensure_ascii=False))
    return result

# 翻译英文到中文
def translate_zh_to_en(query):
    # For list of language codes, please refer to `https://api.fanyi.baidu.com/doc/21`
    from_lang = 'zh'
    to_lang =  'en'
    sign = make_md5(appid + query + str(salt) + appkey)

    # Build request
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    payload = {'appid': appid, 'q': query, 'from': from_lang, 'to': to_lang, 'salt': salt, 'sign': sign}

    # Send request
    r = requests.post(url, params=payload, headers=headers)
    result = r.json()
    
    # Show response
    print(json.dumps(result, indent=4, ensure_ascii=False))
    return result

# 判断字符串的语言（中文或者英文）
def is_contains_chinese(strs):
    for _char in strs:
        if '\u4e00' <= _char <= '\u9fa5':
            return True
    return False

# 设置Aurebesh字母文件夹路径
aurebesh_letters_path = 'Aurebesh/'
    
# 加载每个Aurebesh字母的路径到aurebesh_letters_list中
aurebesh_letters_list = load_target_letters(aurebesh_letters_path)

# 执行翻译
def do_translation(original_sentence,letter_each_line):
    # letter_each_line 每行字母数量
    # 判断是句子否包含中文
    if is_contains_chinese(original_sentence):
        translation_result = translate_zh_to_en(original_sentence)
        processed_sentence = translation_result['trans_result'][0]['dst']
    else:
        processed_sentence = original_sentence
        
    # 加载源句子的字母到english_letters_list中
    english_letters_list = load_source_letters(processed_sentence)
        
    # 将english_letters_list中的字母与aurebesh_letters_list中的字母进行映射，并存入translation_letters_list
    translation_letters_list = translation(english_letters_list, aurebesh_letters_path, aurebesh_letters_list)
    
    # translation_letters_list中的字母图像进行拼接
    
    join_letters(letter_each_line, translation_letters_list)
        
    # 显示源文字和最终翻译结果
    print("\n############# source sentence #############")
    print("original: " + original_sentence)
    print("processed: " + processed_sentence)


async def on_message(msg: Message):
   
    # 语种
    language_chosen = 'Aurebesh'
    
    # 聊天对象列表
    star_war_charater_name_list = ['Master Yoda','Anakin Skywalker','Qui-Gon jinn']
    star_war_charater_icon_list = ['StarWarsCharater/MasterYoda.png','StarWarsCharater/AnakinSkywalker.png','StarWarsCharater/Qui-GonJinn.png']
   
    """
    Message Handler for the Bot
    """
    global function_chosen
    
    print("====================== function_chosen 进入on message:" + str(function_chosen))
    
    if isinstance(msg.text(), str) and len(msg.text()) > 0 and msg._payload.type == MessageType.MESSAGE_TYPE_TEXT:
        if function_chosen == 1:
            if msg.text() == "称号":
                function_chosen = 2
                print("====================== function_chosen 专属星际名称:" + str(function_chosen))
                await msg.say('你好，请输入你的名字')
            elif msg.text() == "返回":
                function_chosen = 3
                print("====================== function_chosen:" + str(function_chosen))
                await msg.say('星际通讯器正在启动中 \n 回复“通讯”启动星际通讯器 \n 回复“称号”获得专属星际名称 \n 回复“返回”回到功能菜单')
            else:
                bot_response = model.predict(data=msg.text())[0]
                    
                do_translation(msg.text(),10)
                file_box_aurebesh_in = FileBox.from_file('./image/translation.png')
                await msg.say('人类语言翻译中...')
                await msg.say(file_box_aurebesh_in)
                    
                await msg.say('发送' + language_chosen + '语并等待回复...')
                do_translation(bot_response,10)
                file_box_aurebesh_out = FileBox.from_file('./image/translation.png')
                await msg.say(file_box_aurebesh_out)
                await msg.say(language_chosen + '语言翻译中...')
                await msg.say(star_war_charater_name_list[1] + "：" + bot_response )  # Return the text generated by PaddleHub chatbot
        elif function_chosen == 2:
            if msg.text() == "通讯":
                function_chosen = 1
                print("====================== function_chosen 启动星际通讯器:" + str(function_chosen))
                the_random_number = random.randint(0,len(star_war_charater_name_list) - 1)
                await msg.say('您这次的通讯对象是：\n'+ star_war_charater_name_list[the_random_number]+ ' \n正在转接中...')
                file_box_charater = FileBox.from_file(star_war_charater_icon_list[the_random_number])
                await msg.say(file_box_charater)
                await msg.say('成功接通' +star_war_charater_name_list[the_random_number] )
            elif msg.text() == "返回":
                function_chosen = 3
                print("====================== function_chosen:" + str(function_chosen))
                await msg.say('星际通讯器正在启动中 \n 回复“通讯”启动星际通讯器 \n 回复“称号”获得专属星际名称 \n 回复“返回”回到功能菜单')
            else:
                do_translation(msg.text(),5)
                file_box_aurebesh_name = FileBox.from_file('./image/translation.png')
                await msg.say('你的星际姓名是：')
                await msg.say(file_box_aurebesh_name)
        elif msg.text() == "1" or msg.text() == "通讯":
            function_chosen = 1
            print("====================== function_chosen 启动星际通讯器:" + str(function_chosen))
            the_random_number = random.randint(0,len(star_war_charater_name_list) - 1)
            await msg.say('您这次的通讯对象是：\n'+ star_war_charater_name_list[the_random_number]+ ' \n正在转接中...')
            file_box_charater = FileBox.from_file(star_war_charater_icon_list[the_random_number])
            await msg.say(file_box_charater)
            await msg.say('成功接通' +star_war_charater_name_list[the_random_number] )
        elif msg.text() == "2" or msg.text() == "称号":
            function_chosen = 2
            print("====================== function_chosen 专属星际名称:" + str(function_chosen))
            await msg.say('你好，请输入你的名字')
        elif msg.text() == "3" or msg.text() == "返回":
            function_chosen = 3
            print("====================== function_chosen:" + str(function_chosen))
            await msg.say('星际通讯器正在启动中 \n 回复“通讯”启动星际通讯器 \n 回复“称号”获得专属星际名称 \n 回复“返回”回到功能菜单')
        else:
            await msg.say('星际通讯器正在启动中 \n 回复“通讯”启动星际通讯器 \n 回复“称号”获得专属星际名称 \n 回复“返回”回到功能菜单')
    
async def on_scan(
        qrcode: str,
        status: ScanStatus,
        _data,
):
    """
    Scan Handler for the Bot
    """
    print('Status: ' + str(status))
    print('View QR Code Online: https://wechaty.js.org/qrcode/' + qrcode)


async def on_login(user: Contact):
    """
    Login Handler for the Bot
    """
    print(user)
    # TODO: To be written


async def main():
    """
    Async Main Entry
    """
    #
    # Make sure we have set WECHATY_PUPPET_SERVICE_TOKEN in the environment variables.
    #
    if 'WECHATY_PUPPET_SERVICE_TOKEN' not in os.environ:
        print('''
            Error: WECHATY_PUPPET_SERVICE_TOKEN is not found in the environment variables
            You need a TOKEN to run the Python Wechaty. Please goto our README for details
            https://github.com/wechaty/python-wechaty-getting-started/#wechaty_puppet_service_token
        ''')
    bot = Wechaty()

    bot.on('scan',      on_scan)
    bot.on('login',     on_login)
    bot.on('message',   on_message)

    await bot.start()

asyncio.run(main())
