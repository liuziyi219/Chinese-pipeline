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

 
dll = cdll.LoadLibrary( "YOUR_DIR/libmsc.so")  
login_params = b"appid = YOUR APPID, work_dir = YOUR WORK_DIR"  
   
FRAME_LEN = 640  # Byte  
   
MSP_SUCCESS = 0  
MSP_AUDIO_SAMPLE_FIRST = 1  
MSP_AUDIO_SAMPLE_CONTINUE = 2  
MSP_AUDIO_SAMPLE_LAST = 4  
MSP_REC_STATUS_COMPLETE = 5    
   
class Msp:  
    def __init__(self):  
        pass  
   
    def login(self):  
        ret = dll.MSPLogin(None, None, login_params)  
   
    def logout(self):  
        ret = dll.MSPLogout() 
   
    def isr(self, audiofile, session_begin_params):  
        ret = c_int()  
        sessionID = c_voidp()  
        dll.QISRSessionBegin.restype = c_char_p  
        sessionID = dll.QISRSessionBegin(None, session_begin_params, byref(ret))   
   
        piceLne = FRAME_LEN * 20  
       # piceLne = 1638*2  
        epStatus = c_int(0)  
        recogStatus = c_int(0)  
   
        wavfile = open(audiofile,'rb')
        wavData = wavfile.read(piceLne)
        ret = dll.QISRAudioWrite(sessionID, wavData, len(wavData), MSP_AUDIO_SAMPLE_FIRST, byref(epStatus), byref(recogStatus)) 
        print('len(wavData):', len(wavData), 'QISRAudioWrite ret:', ret, 'epStatus:', epStatus.value, 'recogStatus:', recogStatus.value)  
	
        while wavData:
             wavData = wavfile.read(piceLne)
             if len(wavData) == 0:
                  break;
             ret = dll.QISRAudioWrite(sessionID, wavData,len(wavData), MSP_AUDIO_SAMPLE_CONTINUE, byref(epStatus), byref(recogStatus))
             
             time.sleep(0.1)
      
        ret = dll.QISRAudioWrite(sessionID, None, 0, MSP_AUDIO_SAMPLE_LAST, byref(epStatus), byref(recogStatus))  
       # print("所有待识别音频已全部发送完毕，等待获取识别结果")  
   
        
        laststr = ''  
        counter = 0  
        while recogStatus.value != MSP_REC_STATUS_COMPLETE:  
            ret = c_int()  
            dll.QISRGetResult.restype = c_char_p  
            retstr = dll.QISRGetResult(sessionID, byref(recogStatus), 0, byref(ret))  
            if retstr is not None:  
                laststr += retstr.decode()  
                
            counter += 1  
            time.sleep(0.2)  
            counter += 1  
	   
        print(laststr)  
        ret = dll.QISRSessionEnd(sessionID, "normal end")  
        
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


