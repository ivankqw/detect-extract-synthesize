#!/usr/bin/env python
# -*-coding:utf-8 -*-
'''
@File    :   clean_img_dir.py
@Author  :   Ivan Koh
@Version :   1.0
@Contact :   e0543621@u.nus.edu
@License :   Apache License 2.0
@Desc    :   This script transfers images with annotations from a COCO dataset
             from the 'train' directory to a 'train_cleaned' directory.
'''

# in the train folder, transfer images that have annotations in the _annotations.coco.json file to a new folder called train_cleaned
import os
import shutil
import json

# Load the annotations file to find out which images have annotations
with open('_annotations.coco.json', 'r') as f:
    data = json.load(f)

# Create a set of all image filenames that have annotations
annotated_images = {image['file_name'] for image in data['images']}

# Define the source and destination directories
source_dir = 'train/'
destination_dir = 'train_cleaned/'

# Create the destination directory if it doesn't exist
if not os.path.exists(destination_dir):
    os.makedirs(destination_dir)

# Transfer the images
for image_filename in annotated_images:
    source_path = os.path.join(source_dir, image_filename)
    destination_path = os.path.join(destination_dir, image_filename)
    if os.path.exists(source_path):
        shutil.move(source_path, destination_path)
