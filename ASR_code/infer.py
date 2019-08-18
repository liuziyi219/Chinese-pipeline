# -*- coding: UTF-8 -*-
"""Inferer for DeepSpeech2 model."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import argparse
import functools
import paddle.v2 as paddle
from data_utils.data import DataGenerator
from model_utils.model import DeepSpeech2Model
from utils.error_rate import wer, cer
from utils.utility import add_arguments, print_arguments
import datetime
import json
parser = argparse.ArgumentParser(description=__doc__)
add_arg = functools.partial(add_arguments, argparser=parser)
# yapf: disable
add_arg('batch_size',       int,    10,     "# of samples to infer.")
add_arg('trainer_count',    int,    1,      "# of Trainers (CPUs or GPUs).")
add_arg('beam_size',        int,    500,    "Beam search width.")
add_arg('num_proc_bsearch', int,    8,      "# of CPUs for beam search.")
add_arg('num_conv_layers',  int,    2,      "# of convolution layers.")
add_arg('num_rnn_layers',   int,    3,      "# of recurrent layers.")
add_arg('rnn_layer_size',   int,    2048,   "# of recurrent cells per layer.")
add_arg('alpha',            float,  2.5,    "Coef of LM for beam search.")
add_arg('beta',             float,  0.3,    "Coef of WC for beam search.")
add_arg('cutoff_prob',      float,  1.0,    "Cutoff probability for pruning.")
add_arg('cutoff_top_n',     int,    40,     "Cutoff number for pruning.")
add_arg('use_gru',          bool,   False,  "Use GRUs instead of simple RNNs.")
add_arg('use_gpu',          bool,   True,   "Use GPU or not.")
add_arg('share_rnn_weights',bool,   True,   "Share input-hidden weights across "
                                            "bi-directional RNNs. Not for GRU.")
add_arg('infer_manifest',   str,
        'data/aishell/manifest.test',
        "Filepath of manifest to infer.")
add_arg('mean_std_path',    str,
        'data/aishell/mean_std.npz',
        "Filepath of normalizer's mean & std.")
add_arg('vocab_path',       str,
        'data/aishell/vocab.txt',
        "Filepath of vocabulary.")
add_arg('lang_model_path',  str,
        'models/lm/zhidao_giga.klm',
        "Filepath for language model.")
add_arg('model_path',       str,
        './checkpoints/librispeech/params.latest.tar.gz',
        "If None, the training starts from scratch, "
        "otherwise, it resumes from the pre-trained model.")
add_arg('decoding_method',  str,
        'ctc_beam_search',
        "Decoding method. Options: ctc_beam_search, ctc_greedy",
        choices = ['ctc_beam_search', 'ctc_greedy'])
add_arg('output_file',  str,
        '',
        "The output file you want to place."
       )
add_arg('input_file',str,
       '',
       "The default title from the text in dataset"
       )
add_arg('specgram_type',    str,
        'linear',
        "Audio feature type. Options: linear, mfcc.",
        choices=['linear', 'mfcc'])
# yapf: disable
args = parser.parse_args()


def infer():
    """extract the duration from manifest"""
    f=open(args.infer_manifest)
    timelist=[]
    for line in f:
       d=json.loads(line.strip())['duration']
       timelist.append(d)
    """Inference for DeepSpeech2."""
    data_generator = DataGenerator(
        vocab_filepath=args.vocab_path,
        mean_std_filepath=args.mean_std_path,
        augmentation_config='{}',
        specgram_type=args.specgram_type,
        num_threads=1,
        keep_transcription_text=True)
    batch_reader = data_generator.batch_reader_creator(
        manifest_path=args.infer_manifest,
        batch_size=args.batch_size,
        min_batch_size=1,
        sortagrad=False,
        shuffle_method=None) 
    ds2_model = DeepSpeech2Model(
        vocab_size=data_generator.vocab_size,
        num_conv_layers=args.num_conv_layers,
        num_rnn_layers=args.num_rnn_layers,
        rnn_layer_size=args.rnn_layer_size,
        use_gru=args.use_gru,
        pretrained_model_path=args.model_path,
        share_rnn_weights=args.share_rnn_weights)

    # decoders only accept string encoded in utf-8
    vocab_list = [chars.encode("utf-8") for chars in data_generator.vocab_list]
    if args.decoding_method == "ctc_greedy":
        ds2_model.logger.info("start inference ...")
        probs_split = ds2_model.infer_batch_probs(infer_data=infer_data,
            feeding_dict=data_generator.feeding)
        result_transcripts = ds2_model.decode_batch_greedy(
            probs_split=probs_split,
            vocab_list=vocab_list)
    else:
        ds2_model.init_ext_scorer(args.alpha, args.beta, args.lang_model_path,
                                  vocab_list)
        ds2_model.logger.info("start inference ...")


        with open(args.input_file,'r') as f:
                l = f.readlines()
                l[8] = "ASR_01|CMN\n"
                start_time = l[10].split('|')[0]
                end_time = l[10].split('|')[1]
                time_now = str(datetime.datetime.now())[:16] # get the current time
                l[10] = "|".join(["ASR_01",time_now,"Source_Program=Baidu DeepSpeech2,infer.sh","Source_Person=Zhaoqing Xu,Shuwei Xu","Codebook=Chinese Speech to Text\n"])
                end_line = ""
                if l[-1].startswith("END"):
                      end_line = l[-1]
                l = l[:11]

        with open(args.output_file,"w") as f:
               f.writelines(l)
 

        for infer_data in batch_reader():
	    probs_split = ds2_model.infer_batch_probs(infer_data=infer_data,
               feeding_dict=data_generator.feeding)
            result_transcripts = ds2_model.decode_batch_beam_search(
              probs_split=probs_split,
              beam_alpha=args.alpha,
              beam_beta=args.beta,
              beam_size=args.beam_size,
              cutoff_prob=args.cutoff_prob,
              cutoff_top_n=args.cutoff_top_n,
              vocab_list=vocab_list,
              num_processes=args.num_proc_bsearch)
              index=0
	    for result in result_transcripts:

              with open(args.output_file,'a+') as f:
                 print("\nOutput Transcription: %s" %
                 result.encode('utf-8'))
            #	 try:
             #    print(start_time)
            
            #     start,m_sec = start_time.split('.')
                 time_format = '%Y%m%d%H%M%S.%f'
                 end = (datetime.datetime.strptime(start_time,time_format) + datetime.timedelta(0,timelist[index])).strftime(time_format)
                 index+=1
                 prefix = start +  '|' + end[:-3]  + '|ASR_01|'
                 f.write(prefix)			
                 f.write(result.encode('utf-8'))
                 f.write('\n')
                 start_time = end 
                # except:
                 #    continue
        with open(args.output_file, 'a+') as f:
             f.write(end_line)
        ds2_model.logger.info("finish inference")

def main():
   # print_arguments(args)
    paddle.init(use_gpu=args.use_gpu,
                rnn_use_batch=True,
                trainer_count=args.trainer_count)
    infer()


if __name__ == '__main__':
    main()
