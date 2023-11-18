from flask_restx import Namespace, Resource, reqparse
from werkzeug.datastructures import FileStorage
from imantics import Mask
from flask_login import login_required
from config import Config
from PIL import Image
# from database import ImageModel


import json
import os
import logging

from flask import Flask, request, jsonify
import numpy as np

logger = logging.getLogger('gunicorn.error')

SAM_LOADED = os.path.isfile(Config.SAM_MODEL_FILE)
if SAM_LOADED:
    from ..util.sam import model as sam
else:
    logger.warning("SAM model is disabled.")

MASKRCNN_LOADED = os.path.isfile(Config.MASK_RCNN_FILE)
logger.info('MaskRCNN path: {}'.format(Config.MASK_RCNN_FILE))
if MASKRCNN_LOADED:
    from ..util.mask_rcnn import model as maskrcnn
else:
    logger.warning("MaskRCNN model is disabled.")

DEXTR_LOADED = os.path.isfile(Config.DEXTR_FILE)
if DEXTR_LOADED:
    from ..util.dextr import model as dextr
else:
    logger.warning("DEXTR model is disabled.")

api = Namespace('model', description='Model related operations')

DETECTRON2_LOADED = os.path.isfile(Config.DETECTRON2_FILE)
if DETECTRON2_LOADED:
    from ..util.detectron2_coco import model as detectron2_coco
    logger.info("Detectron2 model is enabled. Using model {}".format(Config.DETECTRON2_FILE))
else:
    logger.warning("DETECTRON2 model is disabled.")

MASKFORMER_LOADED = os.path.isfile(Config.MASK_FORMER_FILE)
if MASKFORMER_LOADED:
    from ..util.mask_former import model as maskformer
    logger.info("MaskFormer model is enabled. Using model {}".format(Config.MASK_FORMER_FILE))
else:
    logger.warning("MaskFormer model is disabled.")

MASKCOCO_LOADED = os.path.isfile(Config.MASK_COCO_FILE)
logger.info('MaskCoco path: {}'.format(Config.MASK_COCO_FILE))
if MASKCOCO_LOADED:
    from ..util.mask_coco import model as maskcoco
else:
    logger.warning("MaskCoco model is disabled.")

image_upload = reqparse.RequestParser()
image_upload.add_argument('image', location='files', type=FileStorage, required=True, help='Image')

dextr_args = reqparse.RequestParser()
dextr_args.add_argument('data', type=str, required=True)
dextr_args.add_argument('image', location='files', type=FileStorage, required=True, help='Image')

sam_args = reqparse.RequestParser()
sam_args.add_argument('data', type=str, required=True)
sam_args.add_argument('image', location='files', type=FileStorage, required=True, help='Image')

@api.route('/dextr')
class MaskRCNN(Resource):

    @api.expect(dextr_args)
    def post(self):
        """ COCO data test """

        if not DEXTR_LOADED:
            return {"disabled": True, "message": "DEXTR is disabled"}, 400

        args = dextr_args.parse_args()
        
        # logger.warning("args: {}".format(args))
        data = json.loads(args['data'])
        points=data['points']        
        if len(points) != 4:
            return {"message": "Invalid points entered"}, 400
        
        image = Image.open(args['image']).convert('RGB')

        result = dextr.predict_mask(image, points)

        return { "segmentaiton": Mask(result).polygons().segmentation }


@api.route('/maskrcnn')
class MaskRCNN(Resource):

    @api.expect(image_upload)
    def post(self):
        """ COCO data test """
        if not MASKRCNN_LOADED:
            return {"disabled": True, "coco": {}}

        args = image_upload.parse_args()
        im = Image.open(args.get('image'))
        coco = maskrcnn.detect(im)
        return {"coco": coco}

@api.route('/detectron2')
class MaskRCNN(Resource):

    @api.expect(image_upload)
    def post(self):
        """ COCO data test """
        if not DETECTRON2_LOADED:
            return {"disabled": True, "coco": {}}

        args = image_upload.parse_args()
        im = Image.open(args.get('image'))
        coco = detectron2_coco.detect(im)
        return {"coco": coco}

@api.route('/maskformer')
class MaskRCNN(Resource):

    @api.expect(image_upload)
    def post(self):
        """ COCO data test """
        if not MASKFORMER_LOADED:
            return {"disabled": True, "coco": {}}

        args = image_upload.parse_args()
        im = Image.open(args.get('image'))
        coco = maskformer.detect(im)
        return {"coco": coco}

@api.route('/maskcoco')
class MaskRCNN(Resource):

    @api.expect(image_upload)
    def post(self):
        """ COCO data test """
        if not MASKCOCO_LOADED:
            return {"disabled": True, "coco": {}}

        args = image_upload.parse_args()
        im = Image.open(args.get('image'))
        coco = maskcoco.detect(im)
        return {"coco": coco}

@api.route('/sam')
class MaskRCNN(Resource):

    @api.expect(image_upload)
    def post(self):

        """ COCO data test """
        if not SAM_LOADED:
             return {"disabled": True, "message": "SAM is disabled"}, 400

        args = sam_args.parse_args()
        # logger.warning("args: {}".format(args))
        data = json.loads(args['data'])
        points=data['points'][0]

        img_file = args['image']
        im = Image.open(img_file.stream).convert('RGB')
        im = np.asarray(im)
        
        logger.warning("points: {}".format(points))
        sam.setImage(im)
        sam.calcMasks(np.array([points]), np.array([1]))
        sam.getSegmentation()
        return { "segmentaiton": sam.getSegmentation() }
