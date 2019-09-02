
## Register and Download the SDK package
The first thing is to sign up in [Xunfei Open Platform](https://www.xfyun.cn/). Then enter into the personal application, there you can create an application and add the service you need(you can choose SDK or WebAPI or other formats, in this case, I used Linux SDK). After that, download the SDK package. 

The official website has very clear instructions, check the website to see more details of downloading SDK. Here will be no more explanation.

## Prepare the data
The xunfeisdk only supports sample rate 8k and 16k. So make sure to have changed the sample rate.

## To use the SDK
To see the code, click (here)[https://github.com/liuziyi219/Chinese-pipeline/tree/master/xunfeisdk]

Usage:

    python xunfei.py <path to wav file/directory> <path to result>
The result will be saved in the form of txt and its name is same as the wav file. For example, the name of a wav file is "xwlb0302-117.wav",its corresponding text is "xwlb0302-117.txt".


## Error handling

There will be only one error when using the code above, it's error '10114'. It means session timeout. Just need to check the network connections or change a network. 

## Limitation

The Xunfei SDK only offer 500 times service for free everyday.
