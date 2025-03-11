#!/usr/bin/env python
# -*-coding:utf-8 -*-
'''
@File    :   clean_coco.py
@Author  :   Ivan Koh
@Version :   1.0
@Contact :   e0543621@u.nus.edu
@License :   Apache License 2.0
@Desc    :   Remove images with no annotations from the COCO dataset.
'''

# in the train folder, in the _annotations.coco.json file, remove images with no annotations

import json

# Load the dataset
data = json.load(open('train/_annotations.coco.json'))

new_images = []
new_annotations = []
new_categories = []

# Filter out images without annotations
image_ids_with_annotations = {
    annotation['image_id'] for annotation in data['annotations']}
new_images = [image for image in data['images']
              if image['id'] in image_ids_with_annotations]

# Filter out annotations that don't belong to any image
image_ids = {image['id'] for image in data['images']}
new_annotations = [annotation for annotation in data['annotations']
                   if annotation['image_id'] in image_ids]

# Filter out categories without annotations
category_ids_with_annotations = {
    annotation['category_id'] for annotation in data['annotations']}
new_categories = [category for category in data['categories']
                  if category['id'] in category_ids_with_annotations]

# Update the dataset
data['images'] = new_images
data['annotations'] = new_annotations
data['categories'] = new_categories

# Save the cleaned dataset
with open('_annotations.coco.json', 'w') as f:
    json.dump(data, f, indent=4)
