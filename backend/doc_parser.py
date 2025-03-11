from typing import Dict, Union
import os
import fitz
from PIL import Image, ImageDraw
import time
import io
from ultralytics import YOLO
import base64
import aiohttp
import asyncio

class DocParser:
    def __init__(self, input_dir: str, output_dir: str, openai_api_key: str, model_path: str):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.total_pages = 0
        self.total_length = 0
        self.openai_api_key = openai_api_key
        self.yolo_model = YOLO(model_path)

    def _save_page_content(self, doc_name: str, page_num: int, content: str):
        doc_output_dir = os.path.join(self.output_dir, doc_name)
        os.makedirs(doc_output_dir, exist_ok=True)
        output_file = os.path.join(doc_output_dir, f"page_{page_num}.txt")
        with open(output_file, "w", encoding="utf-8") as file:
            file.write(content)

    def _object_detection_infer(self, img: Image.Image):
        results = self.yolo_model(img)
        conf = results[0].boxes.conf.numpy()
        boxes = results[0].boxes.xyxy.numpy()

        conf_mask = conf > 0.8
        conf_boxes = boxes[conf_mask]

        if len(conf_boxes):
            draw = ImageDraw.Draw(img, "RGBA")
            for box in conf_boxes:
                draw.rectangle(box.tolist(), outline=(255, 0, 0, 128), width=2)
            conf_boxes = conf_boxes.tolist()
            return img, conf_boxes
        return None

    async def _aextract_insights_from_image(self, session: aiohttp.ClientSession, image_payload: Dict[str, Union[str, Dict[str, str]]]):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.openai_api_key}"
        }
        payload = {
            "model": "gpt-4-vision-preview",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Please extract insights from the provided image."
                        }
                    ] + [image_payload]
                }
            ],
            "max_tokens": 4096
        }
        try:
            async with session.post(
                "https://api.openai.com/v1/chat/completions", headers=headers, json=payload
            ) as response:
                response = await response.json()
            if "error" in response:
                raise Exception(f"OpenAI request failed with error {response['error']}")
            return response['choices'][0]['message']['content']
        except Exception as e:
            print(f"Error: {e}")
            return ""

    def _encode_image_in_memory(self, image: Image.Image):
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        return base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')

    async def parse_document(self, file_path: str):
        with open(file_path, "rb") as file:
            pdf_stream = io.BytesIO(file.read())

        doc = fitz.open(stream=pdf_stream, filetype="pdf")
        parsed_data = []

        async with aiohttp.ClientSession() as session:
            for i, page in enumerate(doc):
                text = page.get_text().encode("utf-8")
                parsed_data.append(text.decode("utf-8"))

                pix = page.get_pixmap()
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

                img_with_inference = self._object_detection_infer(img)

                if img_with_inference:
                    img, bboxes = img_with_inference
                    encoded_image = self._encode_image_in_memory(img)

                    image_payload = {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{encoded_image}"
                        }
                    }

                    insights = await self._aextract_insights_from_image(session, image_payload)
                    parsed_data[i] += '\n' + insights

        doc_name = os.path.splitext(os.path.basename(file_path))[0]
        for i, page_content in enumerate(parsed_data):
            self._save_page_content(doc_name, i, page_content)
            self.total_pages += 1
            self.total_length += len(page_content)


    async def parse_directory(self):
        very_start = time.time()

        pdf_files = [file for file in os.listdir(self.input_dir) if file.endswith(".pdf")]
        # random sample 10 files
        pdf_files = pdf_files[10:]
        # randomly sample 90 files
        from random import sample
        pdf_files = sample(pdf_files, 90)

        for pdf_file in pdf_files:
            file_path = os.path.join(self.input_dir, pdf_file)
            start = time.time()
            await self.parse_document(file_path)
            print(f"Time taken to extract text and insights from {pdf_file}: {time.time() - start} seconds")
            average_length = self.total_length / self.total_pages
            print(f"Average page length: {average_length} characters")

        print(f"Time taken to parse all documents: {time.time() - very_start} seconds")