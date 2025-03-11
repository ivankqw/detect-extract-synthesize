import aiohttp
import asyncio
from google.cloud import storage
import fitz
from ultralytics import YOLO

import os
import io
import base64

import requests
from PIL import Image, ImageDraw
from typing import Any, Tuple, Optional
import time
import uuid
from db import Database
from typing import List, Dict, Union
from definitions import PGDocument, extraction_prompt
from vector_db import VectorDB

MODEL_PATH = "best.pt"
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")


class DocUploader:
    def __init__(self,
                 is_nerfed: bool,
                 storage_client: storage.Client,
                 bucket: storage.Bucket,
                 blob: storage.Blob,
                 db: Database,
                 vector_db: VectorDB):
        """Initializes the DocUploader class with the filename of the document to be uploaded.

        The DocUploader class is used to retrieve the text from a PDF document, run inference to extract bounding boxes from the document, 
        and send the entire image with bounding boxes to OpenAI for processing.

        1. first, uid is assigned to the document based on the filename
        2. we need to push (path: str, name: str, parsed_data: str, bboxes: list) to the database
        3. once parse is done, we get the bboxes and parsed_data 
        4. we can then push the parsed_data and bboxes to the database

        filename should always be in PDF extension
        """
        self.is_nerfed = is_nerfed
        self.storage_client = storage_client
        self.bucket = bucket
        self.blob = blob
        self.yolo_model = YOLO(MODEL_PATH)
        self.openai_api_key = OPENAI_API_KEY

        self.uid = self._get_uid()
        self.db = db
        self.vector_db = vector_db

    def _get_uid(self) -> str:
        return str(uuid.uuid4())

    def _get_doc_stream(self) -> io.BytesIO:
        pdf_stream = io.BytesIO()
        self.blob.download_to_file(pdf_stream)
        pdf_stream.seek(0)
        return pdf_stream

    def _object_detection_infer(self, img: Image.Image) -> Optional[Tuple[Image.Image, List[List[int]]]]:
        results = self.yolo_model(img)
        conf = results[0].boxes.conf.numpy()
        boxes = results[0].boxes.xyxy.numpy()

        # Take only boxes with confidence > 0.8
        conf_mask = conf > 0.8
        conf_boxes = boxes[conf_mask]

        if len(conf_boxes):
            # Draw the boxes on the image with transparency
            draw = ImageDraw.Draw(img, "RGBA")
            for box in conf_boxes:
                # Create a semi-transparent red for the bounding box
                draw.rectangle(box.tolist(), outline=(
                    255, 0, 0, 128), width=2)
            # convert np to list
            conf_boxes = conf_boxes.tolist()
            return (img, conf_boxes)
        return None

    @staticmethod
    def _pad_bboxes(all_bboxes: List[List[int]]) -> List[List[int]]:
        # edge case, no bboxes
        if len(all_bboxes) == 0:
            return all_bboxes
        # Get the max number of bboxes in a single image
        max_size = max(len(bbox) for bbox in all_bboxes)
        # Pad the bboxes with -1s to make them all the same size
        for curr_img_bboxes in all_bboxes:
            curr_img_bboxes.extend([[-1, -1, -1, -1]
                                   for _ in range(max_size - len(curr_img_bboxes))])
        # check if all bboxes have the same size
        assert all(len(
            bboxes) == max_size for bboxes in all_bboxes), "Images should have the same number of bounding boxes"
        return all_bboxes

    def _extract_insights_from_image(self,
                                     image_payload: Dict[str, Union[str, Dict[str, str]]],
                                     openai_api_key: str = OPENAI_API_KEY) -> str:
        start = time.time()
        # OpenAI API
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {openai_api_key}"
        }
        payload = {
            "model": "gpt-4-vision-preview",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": extraction_prompt(self.blob.name)
                        }
                    ] + [image_payload]
                }
            ],
            "max_tokens": 4096
        }

        # Send the request to OpenAI
        response = requests.post(
            "https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        if response.status_code == 200:
            response_data = response.json()['choices'][0]['message']['content']
        else:
            print(f"Error: {response.status_code} - {response.text}")

        print(f"Time taken to run OpenAI API: {time.time() - start} seconds")
        return response_data

    async def _aextract_insights_from_image(self,
                                            session: aiohttp.ClientSession,
                                            image_payload: Dict[str, Union[str, Dict[str, str]]],
                                            openai_api_key=OPENAI_API_KEY) -> str:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {openai_api_key}"
        }
        payload = {
            "model": "gpt-4-vision-preview",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",

                            "text": extraction_prompt(self.blob.name)
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
                raise Exception(
                    f"OpenAI request failed with error {response['error']}")
            print(response['choices'][0]['message']['content'])
            return response['choices'][0]['message']['content']
        except Exception as e:
            print(f"Error: {e}")
            response_data = ""
        return response_data

    async def _aextract_insights_from_images(self,
                                             image_payload_list: List[Tuple[str, Dict[str, Any]]]) -> List[str]:
        start = time.time()
        async with aiohttp.ClientSession() as session:
            tasks = [self._aextract_insights_from_image(
                session, image_payload) for _, image_payload in image_payload_list]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results and exceptions
            for result in results:
                if isinstance(result, Exception):
                    print(f"Error parsing file: {result}")
                else:
                    # Process the valid result
                    pass

        print(f"Time taken to run OpenAI API: {time.time() - start} seconds")
        return [result for result in results if not isinstance(result, Exception)]

    def _convert_bbox_to_pixel(self, bbox, img_width, img_height):
        x_center, y_center, width, height = bbox
        xmin = int((x_center - width / 2) * img_width)
        ymin = int((y_center - height / 2) * img_height)
        xmax = int((x_center + width / 2) * img_width)
        ymax = int((y_center + height / 2) * img_height)
        return xmin, ymin, xmax, ymax

    def _plot_bboxes_on_image(self, img: Image.Image, bboxes: List[List[int]]) -> Image.Image:
        draw = ImageDraw.Draw(img, "RGBA")
        for bbox in bboxes:
            # convert bbox to pixel
            bbox = self._convert_bbox_to_pixel(bbox, img.width, img.height)
            draw.rectangle(bbox, outline=(255, 0, 0, 128), width=2)
        return img

        # Function to encode the image in memory
    def _encode_image_in_memory(self, image: Image.Image) -> str:
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        return base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')

    def _process_and_encode_image(self, img: Image.Image, bboxes: List[List[int]]) -> str:
        img_with_bboxes = self._plot_bboxes_on_image(img, bboxes)
        return self._encode_image_in_memory(img_with_bboxes)

    async def parse(self) -> None:
        very_start = time.time()
        pdf_stream = self._get_doc_stream()

        doc = fitz.open(stream=pdf_stream, filetype="pdf")
        parsed_data = []
        width, height = 0, 0

        start = time.time()

        for i, page in enumerate(doc):
            text = page.get_text().encode("utf-8")
            parsed_data.append(text.decode("utf-8"))
            if i == 0:
                width, height = page.rect.width, page.rect.height

        print(
            f"Time taken to extract text from the document: {time.time() - start} seconds")

        if not self.is_nerfed:
            image_payload_list: List[Tuple[str, Dict[str, Any]]] = []
            pages_with_charts_idx = []
            bbox_data = []
            for i, page in enumerate(doc):
                text = page.get_text().encode("utf-8")
                parsed_data.append(text.decode("utf-8"))

                # convert the page to an image
                pix = page.get_pixmap()
                img = Image.frombytes(
                    "RGB", [pix.width, pix.height], pix.samples)

                img_with_inference = self._object_detection_infer(img)

                if img_with_inference:
                    img, bboxes = img_with_inference
                    pages_with_charts_idx.append(i)
                    # check if shape of bboxes is (n, 4) because 1 image can have multiple bboxes
                    for bbox in bboxes:
                        assert len(
                            bbox) == 4, "Bounding box should have 4 coordinates"
                    bbox_data.append(bboxes)

                    encoded_image = self._process_and_encode_image(img, bboxes)

                    image_payload_list.append(
                        (i,
                         {
                             "type": "image_url",
                             "image_url": {
                                 "url": f"data:image/png;base64,{encoded_image}"
                             }
                         }))

            print(
                f"Time taken to run object detection on the document: {time.time() - start} seconds")

            # Pad the bboxes with -1s to make them all the same size
            bbox_data = self._pad_bboxes(bbox_data)

            # Extract insights from the images
            results = await self._aextract_insights_from_images(image_payload_list=image_payload_list)
            for i in range(len(image_payload_list)):
                page_num, _ = image_payload_list[i]
                parsed_data[page_num] += '\n' + results[i]

            document = PGDocument(
                path=self.blob.name,
                name=self.blob.name,
                id=self.uid,
                pages_with_charts_idx=pages_with_charts_idx,
                parsed_data="\n".join(parsed_data),
                bboxes=bbox_data,
                width=width,
                height=height
            )
        else:
            # If is_nerfed, create the document without image processing data
            document = PGDocument(
                path=self.blob.name,
                name=self.blob.name,
                id=self.uid,
                pages_with_charts_idx=[],
                parsed_data="\n".join(parsed_data),
                bboxes=[],
                width=width,
                height=height
            )

        start = time.time()
        self.db.insert_document(document)
        print(
            f"Time taken to insert document into sql database: {time.time() - start} seconds")

        start = time.time()

        self.vector_db.ingest_pitchdeck(
            doc_id=self.uid, page_contents=parsed_data, path_to_document=self.blob.name)

        print(
            f"Time taken to ingest document into vector database: {time.time() - start} seconds")
        with open('vector_db_logs.txt', 'a') as f:
            f.write(f"{time.time() - start}\n")
        print(
            f"Time taken to parse the document: {time.time() - very_start} seconds"
        )
