#!/usr/bin/python3
# -*- coding=utf-8 -*-
from ctypes import *  
import os
import time  
from pyaudio import PyAudio, paInt16 
import numpy as np 
import time
from glob import glob
import wave
import re
import sys

 # 调用动态链接库  
dll = cdll.LoadLibrary( "libs/x64/libmsc.so")  
 #登录参数，apppid一定要和你的下载SDK对应  
login_params = b"appid = 5d162b2b, work_dir = ."  
#login_params = stringutils.getLoginParams()
   
FRAME_LEN = 640  # Byte  
   
MSP_SUCCESS = 0  
# 返回结果状态  
MSP_AUDIO_SAMPLE_FIRST = 1  
MSP_AUDIO_SAMPLE_CONTINUE = 2  
MSP_AUDIO_SAMPLE_LAST = 4  
MSP_REC_STATUS_COMPLETE = 5  
 # 你的语音文件路径  
filename = "example.wav"  
   
class Msp:  
    def __init__(self):  
        pass  
   
    def login(self):  
        ret = dll.MSPLogin(None, None, login_params)  
        # print('MSPLogin =>', ret)  
   
    def logout(self):  
        ret = dll.MSPLogout()  
        # print('MSPLogout =>', ret)  
   
    def isr(self, audiofile, session_begin_params):  
        ret = c_int()  
        sessionID = c_voidp()  
        dll.QISRSessionBegin.restype = c_char_p  
        sessionID = dll.QISRSessionBegin(None, session_begin_params, byref(ret))  
        print('QISRSessionBegin => sessionID:', sessionID, 'ret:', ret.value)  
   
        # 每秒【1000ms】  16000 次 * 16 bit 【20B】 ，每毫秒：1.6 * 16bit 【1.6*2B】 = 32Byte  
        # 1帧音频20ms【640B】 每次写入 10帧=200ms 【6400B】  
   
        piceLne = FRAME_LEN * 20  
       # piceLne = 1638*2  
        epStatus = c_int(0)  
        recogStatus = c_int(0)  
   
        wavfile = open(audiofile,'rb')
        wavData = wavfile.read(piceLne)

       # wavData = wData[0].tostring()
        ret = dll.QISRAudioWrite(sessionID, wavData, len(wavData), MSP_AUDIO_SAMPLE_FIRST, byref(epStatus), byref(recogStatus)) 
        print('len(wavData):', len(wavData), 'QISRAudioWrite ret:', ret, 'epStatus:', epStatus.value, 'recogStatus:', recogStatus.value)  
 
      #  for index in range(1, len(wData)):
       #     wavData = wData[index].tostring()
        #    if len(wavData) == 0:  
         #       break
          #  ret = dll.QISRAudioWrite(sessionID, wavData, len(wavData), MSP_AUDIO_SAMPLE_CONTINUE, byref(epStatus), byref(recogStatus))  
           # print('len(wavData):', len(wavData), 'QISRAudioWrite ret:', ret, 'epStatus:', epStatus.value, 'recogStatus:', recogStatus.value)  
       # time.sleep(0.01)  
        while wavData:
             wavData = wavfile.read(piceLne)
             if len(wavData) == 0:
                  break;
             ret = dll.QISRAudioWrite(sessionID, wavData,len(wavData), MSP_AUDIO_SAMPLE_CONTINUE, byref(epStatus), byref(recogStatus))
             
             time.sleep(0.1)
       # wavfile.close()
        ret = dll.QISRAudioWrite(sessionID, None, 0, MSP_AUDIO_SAMPLE_LAST, byref(epStatus), byref(recogStatus))  
        print("所有待识别音频已全部发送完毕，等待获取识别结果")  
   
        # -- 获取音频  
        laststr = ''  
        counter = 0  
        while recogStatus.value != MSP_REC_STATUS_COMPLETE:  
            ret = c_int()  
            dll.QISRGetResult.restype = c_char_p  
            retstr = dll.QISRGetResult(sessionID, byref(recogStatus), 0, byref(ret))  
            if retstr is not None:  
                laststr += retstr.decode()  
                # print(laststr)  
            # print('ret:', ret.value, 'recogStatus:', recogStatus.value)  
            counter += 1  
            time.sleep(0.2)  
            counter += 1  
	   
        print(laststr)  
        ret = dll.QISRSessionEnd(sessionID, "normal end")  
        # print('end ret: ', ret)  
        return laststr  

def XF_text(audiofile, audiorate,resultdir):  
    msp = Msp()  
    msp.login()  
    print("login successfully")  
    session_begin_params = b"sub = iat, ptt = 0, result_encoding = utf8, result_type = plain, domain = iat"  
    if 16000 == audiorate:  
        session_begin_params = b"sub = iat, domain = iat, language = zh_cn, accent = mandarin, sample_rate = 16000, result_type = plain, result_encoding = utf8"  
    text = msp.isr(audiofile, session_begin_params)
    msp.logout()
  
    return text

#delete the punctutation 
def process(oldtext):
    newtext = re.sub("[\s+\.\!\/_,$%^*(+\"\']+|[+——！，。？、~@#￥%……&*（）]+", "", oldtext)
    return newtext
    
def main(args):
    if len(args)!=2:
        sys.stderr.write(
                'Usage: xunfei.py <path to wav file/directory> <path to result>\n')
        sys.exit(1)
    if(args[0][-3:]=='wav'):
        text = XF_text(args[0],16000,args[1])
        text = process(text)
        fp = open(args[1]+"/"+args[0][:-4]+".txt",'w')
        fp.write(text)
        fp.close()
        
    else:
        for subfolder,_,filelist in sorted(os.walk(args[0])):
            for fname in sorted(filelist):
                audio_path = os.path.join(subfolder,fname)
                text = XF_text(audio_path,16000,args[1])
                text = process(text)
                fp = open(args[1]+"/"+fname[:-4]+".txt","w")
                fp.write(text)
                fp.close()
if __name__=='__main__':
   main(sys.argv[1:])
#main()

