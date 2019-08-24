# Chinese-pipeline
The project is mainly based on the open source project Deepspeech2 on PaddlePaddle released by Baidu. For the configuration, I strongly recommend you to use our singularity recipe to avoid protential problems.
For the code, click [here](https://github.com/liuziyi219/Chinese-pipeline)

## Prerequsites
For the Red Hen Lab participants, all the configuration has been set up on the server.

Python==2.7  
Singularity==2.5.1  
CUDA==7.5

## Data Preparation
### Data Description
What we use in this project is the Chinese video news data collected by Red Hed Lab, including Xinwenlianbo(新闻联播）,Xinwen1+1(新闻1+1）,etc. The video lengths vary from 20 minutes to 40 minutes.(some of them may include advertisements)
### Data Extraction
To extract the mp4 file from ./tv, you can use the order below  
    `find . -name '*_CN_*.mp4' ! -iname "*CGTN*" -exec cp {} $PWDDIR #set this as your directory to save the videos`

### Format Conversion
Firstl we need to convert the video to audio so that we could apply our pipeline. The tools we use here is FFmpeg.
The usage is:  
    `ffmpeg -i file.mp4 -ac 1 -ar 32000 file.wav`   
ac is to set the channel, '-ac 1' means set the channal as mono, or it will be stereo.  
ar is to set the sample rate. 16000 and 32000 are both acceptable.

### Split the audio
The tool we use here is WebRTCVad. A VAD classifies a piece of audio data as being voiced or unvoiced.
### Installation
Install the webrtcvad module
    
    pip install webrtcvad

### Preparing the audios
Redhen only have mp4 format videos. So, we need to transform the video to audios by ffmpeg. 

FFmpeg is a powerful tool for format converting. After install the ffmpeg, you can convert the video like this:

    ffmpeg -i XXX.mp4 -hide_banner -loglevel 0 -ac 1 -ar 32000 xxx.wav

   XXX.mp4 is the input video, and the xxx.wav is the output audio. 'ac' is to set the channel and 'ar' is to set the sample rate.
#### Split the audio
    To run the files:

    python audiosplit.py <padding duration> <path to wav file/directory> <path to directory>
    
   The complete code audiosplit.py and sample I used can be found at [repository](https://github.com/liuziyi219/Chinese-pipeline).

   Usually, the result won't be satisfied after the first split. Some of cuts will be quite long. To deal with the audios that are longer than 30 seconds(or you can change into other standards), you can decrease the padding duration and re-split them. You don't need to select them by yourself. Just assign the directory including all the files, and all audio that are longer than 30s would be selected and re-splitted.


#### Explanations of parameters
There are several parameters needed to be explained. Some of them are defining, some are not. But I think it's important to introduce all of them and it will be easier to understand the program.
##### aggressiveness mode
You can see 'aggressiveness' in 'run the files'. This parameter is used to filter out non-speech. It's an integer between 0 and 3. 0 is the least aggressive about filtering out non-speech, 3 is the most aggressive. If you set the aggressiveness '0', then you will find many non-speech parts which may last for 1 or 2 seconds in the result. However, if you set the aggressiveness '3', the audio will be splited into hundreds of small parts and that's also not the results we want. After several tests, I found that with the aggressiveness node set **'2'**, the splitting performs best.
##### sample_rate
The API only accepts the sample_rate '16000','24000','32000' and '48000'. The higher the sample rate, the better the audio quality. When converting the video to audio, you need to set the sample rate.
##### num_channels
The API only accepts the audio with monochannel, this is also needed to be set when converting.
##### frame _duration _ms
This defines how long a frame is. I have tried both 20ms and 30ms, and there is no difference between the results.
##### padding _duration _ms
This is most defining parameter since the webrtcvad's theory is to test the padding. This parameter determines how long the pause will be detected. If we set the padding duration small, the audio will be splitted into many small parts and some of them just last 2 or 3 seconds, and that is not fit for later model testing. So after testing 200ms, 250ms, 280ms, 300ms, me and zhaoqing both considered that 300ms is best for cutting the audio.


### Prepare the Manifest

Manifest is a file that includes the information of data, including the audio path, duration. It is made up of small jsons which looks like:  
   ` {"audio_filepath": "data/split/2018-01/2018-01-31_0410_CN_HNTV1_午间新闻/2018-01-31_0410_CN_HNTV1_午间新闻001.wav", "duration": 10.0, "text": ""}`
You can find the code manifest.py in the repository to create the manifest.

## Hyper-parameters Tuning
The hyper-parameters $\alpha$ (language model weight) and $\beta$ (word insertion weight) for the CTC beam search decoder often have a significant impact on the decoder's performance. It would be better to re-tune them on the validation set when the acoustic model is renewed.

 tune.py performs a 2-D grid search over the hyper-parameter $\alpha$ and $\beta$. You must provide the range of $\alpha$ and $\beta$, as well as the number of their attempts.

Tuning with GPU:  
 
    CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7 \
    python tune.py \
    --trainer_count 8 \
    --alpha_from 1.0 \
    --alpha_to 3.2 \
    --num_alphas 45 \
    --beta_from 0.1 \
    --beta_to 0.45 \
    --num_betas 8

     

The grid search will print the WER (word error rate) or CER (character error rate) at each point in the hyper-parameters space, and draw the error surface optionally. What need to be noticed is that tuning might take lots of time, so it's better not to set the range of alpha and beta wide.

If you need to use testset from Red Hen Lab, here is the introduction of [test set](https://liuziyi219.github.io/2019/06/16/Chinese-Pipeline-week3/)
The testset is in /mnt/rds/redhen/gallina/Chinese_Pipeline/ziyiliu. The audios set is in /results, the annotated script is in /script. This testset only contains 150min of voice.

## Infer
To get the inference of your data, we need the following files:

### Infer Manifest
This is the file that generates from the Prepare the Manifest

### Mean&Stddev
This is the file that perform z-score normalization which includes audio features.

    python code/compute_mean_std.py \
    --num_samples 2000 \
    --specgram_type linear \
    --manifest_paths {your manifest path here} \
    --output_path {your expected output path}
you could check in the compute_mean.sh and compute_mean_std.py to see more details.

### Vocabulary
This is the file to count all the words(in Chinese we say characters, same thing) in your data. Note that all the generated words are from the vocabulary, so if you didn't put the expected word here, it's impossible to generate it. We just use the vocab.txt that Baidu provides. You could find the vocab.txt in code directory.

### Speech & Language Model
We used Aishell Model here, which is trained on the Aishell Dataset for 151h and for the language model, we used Mandarin LM Large here, which has no pruning and about 3.7 billion n-grams

After all the preparation, you could fiil them in the right place in infer.sh. The code in the repository contains all the work, from extracting the video, to the inference, so you only need to run infer.sh.

## Running Code at CWRU HPC
### Get into the container

    module load singularity/2.5.1
    module load cuda/7.5
    export SINGULARITY_BINDPATH="/mnt"
    srun -p gpu -C gpup100 --mem=100gb --gres=gpu:2 --pty bash
    cd /mnt/rds/redhen/gallina/Singularity/Chinese_Pipeline/ziyiliu
    singularity shell -e --nv ziyiliu.simg

### Run the infer.sh
    cd code
    ./infer.sh
### Check the results
    cd ../new_text

## Results
A cut of sample output file: 

    TOP|20190505183301|2019-05-05_1833_CN_CCTV13_新闻1+1
    COL|Communication Studies Archive, UCLA
    UID|e1bcc5b0-6f68-11e9-9863-eb97ad55d029
    DUR|00:26:54
    VID|720x576|1024x576
    SRC|Changsha, China
    TTL|News 1+1
    CMT|
    ASR_01|CMN
    LBT|2019-05-06 02:33:01 Asia/Shanghai
    ASR_01|2019-08-18 07:55|Source_Program=Baidu DeepSpeech2,infer.sh|Source_Person=Zhaoqing Xu,Shuwei Xu,Ziyi Liu|Codebook=Chinese Speech to Text
    20190505183301.000|20190505183311.950|ASR_01|一只很可爱的目的和他们的男孩安东江>湖的美人模样还行不
    20190505183311.950|20190505183323.560|ASR_01|创业的感受将是你我还是我的国家我还>没有
    20190505183323.560|20190505183324.430|ASR_01|没
    20190505183324.430|20190505183328.240|ASR_01|我曾好好地对本行业的公司
    20190505183328.240|20190505183333.100|ASR_01|比如原来的因为中国在黄金上的突破
    20190505183333.100|20190505183341.230|ASR_01|也还是要亲口说出而没有这个机会来了>还是中国的年的太空
    20190505183341.230|20190505183343.930|ASR_01|同时很多的欧美国 
