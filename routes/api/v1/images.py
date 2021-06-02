from services.Utils import download_file, del_file
import services.Image as ImageService
from flask_restx import Namespace, Resource
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from .models import image
from .models import responses
import modules.omeroweb as omeroweb
import os
from datetime import date
from modules.database import database
from models.Image import image as im


namespace = Namespace('Images', description='image download and cache in our data storage CRUD operations')
namespace.add_model(image.paths.name, image.paths)
namespace.add_model(image.image_model.name, image.image_model)
namespace.add_model(image.image_get_model.name, image.image_get_model)
namespace.add_model(image.a_images_response.name, image.a_images_response)
namespace.add_model(image.list_images_response.name, image.list_images_response)
namespace.add_model(responses.response.name, responses.response)
namespace.add_model(responses.error_response.name, responses.error_response)


def image_by_id_format(id, format):
    # ' RETURN { _key: doc._key, name: doc.name, omeroId: doc.omeroId, paths: [path]} '
    image = ImageService.select_images(omeroId=id)
    if image is not None:
        query = ' FOR doc IN images ' + \
            f' FILTER doc.omeroId == "{id}" ' + \
                ' FOR path IN doc.paths ' + \
            f' FILTER path.format == "{format}" ' + \
                ' LIMIT 1 ' + \
                ' RETURN doc '
        result = database.query(query)

        if len(result) > 0:
            image = im(result[0]).to_json()
        else:
            image = None
        return image
    else:
        return None


def del_data_fromImg(data, format):
    pathToResponce = []
    if data.get('paths') is not None:
        for path in data['paths']:
            if path['format'] == format:
                pathToResponce.append(path)
    data.update({'paths': pathToResponce})
    return data


@namespace.route('/<string:id>')
@namespace.param('id', 'omero image id')
class ImgGetDel(Resource):
    @namespace.doc('image/delone', security='Bearer')
    @namespace.response(200, 'image by id', image.a_images_response)
    @namespace.response(404, 'Image not found', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @namespace.marshal_with(image.a_images_response)
    @jwt_required()
    def delete(self, id):
        image = ImageService.select_images(omeroId=id)
        image = image[0] if image is not None else None
        if image is None:
            return {'success': False, 'message': 'Image not found'}, 200
        else:
            for path in image.get('paths'):
                print(del_file(path.get('path')))
                break
        deleted = ImageService.delete(id)
        if deleted is None:
            return {'success': False, 'message': 'cannot delete'}, 200
        else:
            return {'success': True, 'data': deleted}, 200

    @namespace.doc('image/getone', security='Bearer')
    @namespace.param('download', 'Try to download True False')
    @namespace.param('format', 'file format JPEG/PNG/TIF default TIF')
    @namespace.response(200, 'image by id', image.a_images_response)
    @namespace.response(404, 'Image not found', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @namespace.marshal_with(image.a_images_response)
    @jwt_required()
    def get(self, id):
        author = get_jwt_identity()
        download = bool(request.args.get('download'))
        format = request.args.get('format')

        if format is None:
            format = 'tif'
        else:
            format = format.lower()
            if 'tif' == format or 'png' == format or 'jpeg' == format:
                pass
            else:
                return {'success': False, 'message': 'format error tif/png/jpeg'}, 200
        image = image_by_id_format(id, format)
        im_without_format = ImageService.select_images(omeroId=id)
        im_without_format = im_without_format[0] if im_without_format is not None else None

        if download is True:
            session = omeroweb.get(author['login'])
            path = os.getenv('OMERO_PROXY_PATH') + '/webclient/render_image_download/' + str(id) + '/?format=' + format
            relativePath = download_file(path, client=session, imgId=id)
            if relativePath is not None:
                path = {'path': relativePath, 'format': format, 'date': date.today().isoformat()}
                if image is not None:
                    for path in image.paths:
                        if path.get('format') == format:
                            path['path'] = relativePath
                            path['date'] = date.today().isoformat()
                    image = ImageService.update(id, image.to_json()).to_json()
                elif image is None and im_without_format is not None:
                    image = im_without_format
                    if image.get('paths') is not None:
                        image['paths'].append(path)
                    else:
                        image.update({'paths': [path]})
                    image = ImageService.update(id, image).to_json()
                else:
                    (filename, ext) = os.path.splitext(os.path.basename(relativePath))
                    data = {'name': filename, 'omeroId': id, 'paths': [path]}
                    image = ImageService.insert(data).to_json()
            else:
                if image is not None:
                    return {'success': True, 'data': del_data_fromImg(image, format)}, 200
        else:
            image = ImageService.select_images(omeroId=id)
            image = image[0] if image is not None else None
            if image is None:
                return {'success': False, 'message': "image not found"}, 200
            image = del_data_fromImg(image.to_json(), format)
            if len(image.get('paths')) == 0:
                return {'success': False, 'message': "image not found"}, 200

        return {'success': True, 'data': del_data_fromImg(image.to_json(), format)}, 200


@namespace.route('/')
class ImgesGet(Resource):
    @namespace.doc('image/getall', security='Bearer')
    @namespace.response(200, 'images', image.list_images_response)
    @namespace.response(404, 'Images not found', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @namespace.marshal_with(image.list_images_response)
    @jwt_required()
    def get(self):
        images = ImageService.select_images()
        if images is None:
            return {'success': False, 'message': 'Images not found'}, 200
        else:
            return {'success': True, 'data': images}, 200
