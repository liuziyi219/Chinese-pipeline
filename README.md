# Chinese-pipeline
Introduction

Red Hen gathers Chinese broadcasts to make datasets for NLP, OCR, audio, and video pipelines. Currently, Red Hen have a preliminary ASR pipeline but it needs great improvement.  This program is divided into 2 parts. The first one is to improve the ASR pipeline which contains 3 steps: find a source of correct transcript of the shows;use a different way of cut the audios; use new models to train the data. The second part is to build a CONCRETE Chinese NLP pipeline which includes basic functions like data ingest, word segmentation, part-of-speech tagging, etc.

Goals

1. improve the current ASR pipeline
2. build a correcet transcript(dataset)
3. build a Chinese NLP Pipeline

Library and tools

ASRT modal: https://github.com/nl8590687/ASRT_SpeechRecognition
WebRTC VAD: https://github.com/jtkim-kaist/VAD
CONCRETE-python: https://github.com/hltcoe/concrete-python/
CONCRETE-stanford: https://github.com/hltcoe/concrete-stanford
