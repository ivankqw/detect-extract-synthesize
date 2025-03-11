#!/usr/bin/env python
# -*-coding:utf-8 -*-
'''
@File    :   convert_to_img.py
@Author  :   Ivan Koh
@Version :   1.0
@Contact :   e0543621@u.nus.edu
@License :   Apache License 2.0
@Desc    :   This script converts PDF files to images and saves them to a specified directory.
'''

# script to convert pdf pages to images
import os
from pdf2image import convert_from_path
import argparse
import warnings

path = 'content/drive/MyDrive/pitch_decks'
save_path = "./images"


def save_images_from_pdf(filename, path=path, save_path=save_path) -> None:
    """Converts a pdf file to a series of images and saves them in the specified directory.

    Args:
        filename (str): The name of the pdf file to convert.
        path (str): The path to the directory containing the pdf file.
        save_path (str): The path to the directory to save the images to.

    Returns:
        None
    """
    if not os.path.exists(save_path):
        os.makedirs(save_path)
    try:
        pages = convert_from_path(os.path.join(path, filename), 300) # 300 dpi
        for i, page in enumerate(pages):
            base_filename = os.path.splitext(filename)[0]
            page.save(os.path.join(save_path, base_filename +
                      '_page_' + str(i) + '.jpg'), 'JPEG')
    except Exception as e:
        print(f"Error converting file: {filename}, Error: {e}")


def save_images_from_pdfs(path=path, save_path=save_path) -> None:
    """Converts all pdf files in a directory to a series of images and saves them in the specified directory.

    Args:
        path (str): The path to the directory containing the pdf files.
        save_path (str): The path to the directory to save the images to.

    Returns:
        None
    """
    warnings.filterwarnings("ignore", category=UserWarning,
                            module='pdf2image.pdf2image')
    pdf_files = [f for f in os.listdir(path) if f.endswith('.pdf')]
    for pdf_file in pdf_files:
        save_images_from_pdf(pdf_file, path=path, save_path=save_path)

parser = argparse.ArgumentParser(
    description='Convert PDF files to images and save them to a specified directory.')
parser.add_argument('--path', help='Path to the directory containing the PDF files.', required=True)
parser.add_argument('--save_path', help='Path to the directory to save the images to.', required=True)

if __name__ == '__main__':
    args = parser.parse_args()
    save_images_from_pdfs(path=args.path, save_path=args.save_path)