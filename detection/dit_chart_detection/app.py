import sys
import os
import glob
import numpy as np
import time

import cv2

from unilm.dit.object_detection.ditod import add_vit_config

import torch

from detectron2.config import CfgNode as CN
from detectron2.config import get_cfg
from detectron2.utils.visualizer import ColorMode, Visualizer
from detectron2.data import MetadataCatalog
from detectron2.engine import DefaultPredictor

from pdf2image import convert_from_bytes

pdf_files = [
    ""
]

images = convert_from_bytes(open(pdf_files[0], 'rb').read())

# save out images
for i, image in enumerate(images):
    image.save(
        f"/Users/ivankoh/work/chatpdf/dit_chart_detection/predictions/images/image_{i}.jpg", "JPEG")

# instantiate the config
cfg = get_cfg()
add_vit_config(cfg)
cfg_path = 'unilm/dit/object_detection/publaynet_configs/cascade/cascade_dit_base.yaml'
cfg.merge_from_file(cfg_path)

# add model weights
cfg.MODEL.WEIGHTS = 'publaynet_dit-b_cascade.pth'

# set device
cfg.MODEL.DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# define model
predictor = DefaultPredictor(cfg)


def analyze_image(idx, img):
    md = MetadataCatalog.get(cfg.DATASETS.TEST[0])
    if cfg.DATASETS.TEST[0] == "icdar2019_test":
        md.set(thing_classes=["table"])
    else:
        md.set(thing_classes=["text", "title", "list", "table", "figure"])
    start = time.time()
    try:
        output = predictor(img)["instances"]
    except:
        return img
    end = time.time()
    inference_time = end - start
    boxes = output.pred_boxes.tensor.cpu().numpy()
    classes = output.pred_classes.cpu().numpy()
    scores = output.scores.cpu().numpy()
    high_confidence_indices = np.where(scores > 0.5)[0]
    boxes = boxes[high_confidence_indices]
    classes = classes[high_confidence_indices]
    # Keep scores of high confidence predictions
    scores = scores[high_confidence_indices]
    for i, (box, cls, score) in enumerate(zip(boxes, classes, scores)):  # Include score in the loop
        # Draw predictions with score > 0.5
        if md.thing_classes[cls] == "figure" and score > 0.5:
            x1, y1, x2, y2 = box
            cropped_img = img[int(y1):int(y2), int(x1):int(x2)]
            cv2.imwrite(
                f"figure_instances/figure_{str(idx) + '_' + str(i)}.jpg", cropped_img)

    v = Visualizer(img[:, :, ::-1], metadata=md, scale=1.0,
                   instance_mode=ColorMode.SEGMENTATION)
    high_confidence_output = output[high_confidence_indices]
    result = v.draw_instance_predictions(high_confidence_output.to("cpu"))
    result_image = result.get_image()[:, :, ::-1]

    return result_image, inference_time


# test on images folder
images = glob.glob(
    "/Users/ivankoh/work/chatpdf/dit_chart_detection/predictions/images/*")
inference_times = []
# only on jpg files
images = [image for image in images if image.endswith('.jpg')]

for i, image in enumerate(images):
    # Start time before inference
    img = cv2.imread(image)

    print(f"Processing image {i + 1}/{len(images)}")
    result_image, inference_time = analyze_image(image.split('/')[-1], img)

    inference_times.append(inference_time)
    cv2.imwrite(f"predictions/{image.split('/')[-1]}", result_image)

print(inference_times)
average_inference_time = sum(inference_times) / len(inference_times)
print(f"Average inference time: {average_inference_time:.4f} seconds")
