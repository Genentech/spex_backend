# from models.Files import file
import os
import spex_common.services.Files as fileService
from flask_restx import Namespace, Resource
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from .models import files as _file
from .models import responses
from werkzeug.datastructures import FileStorage
import spex_common.services.Utils as Utils
import anndata
import io
import h5py

namespace = Namespace('Files', description='Files operations CRUD operations')
upload_parser = namespace.parser()
upload_parser.add_argument('filenames', location='files', type=FileStorage, required=True)
upload_parser.add_argument(
    'folder',
    help='parent folder name create if not exist',
    location='headers',
    type=str,
    required=False
)

namespace.add_model(_file.file_model.name, _file.file_model)
namespace.add_model(_file.file_get_model.name, _file.file_get_model)
namespace.add_model(responses.response.name, responses.response)
namespace.add_model(responses.error_response.name, responses.error_response)


#  TODO @namespace.param(name='filenames', _in='formData', description='Upload file',
#   required=True, type='array', items={'type': 'file'}, collectionFormat='multi') multi uploading

@namespace.route('')
class FileResPost(Resource):
    @namespace.doc('file/uploadone', security='Bearer')
    @namespace.expect(upload_parser)
    @namespace.response(404, 'file not found', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @jwt_required()
    def post(self):
        args = upload_parser.parse_args()
        file = args['filenames']
        file_bytes = io.BytesIO(file.read())

        if file.content_type == 'image/tiff':
            destination = f'{os.getenv("DATA_STORAGE")}/originals/{file.filename}'
            file_to_save = os.path.join(destination, 'image.tiff')
            if not os.path.exists(destination):
                os.makedirs(destination)
            file.stream.seek(0)
            file.save(file_to_save)
            return {"success": True, "path": file_to_save}, 200
        else:
            with h5py.File(file_bytes, 'r') as h5_file:
                obs_keys = [key.lower() for key in h5_file['obs'].keys()]

            # if 'cell_id1' not in obs_keys:
            #     return {"error": "File does not contain the required key: Cell_Id"}, 400

            destination = fileService.user_folder(author=get_jwt_identity(), folder=args['folder'])
            file_to_save = os.path.join(destination, file.filename)
            file.stream.seek(0)
            file.save(file_to_save)

            return {"success": True, "keys": obs_keys}, 200

    @namespace.doc('file/getfiletree', security='Bearer')
    # @namespace.expect(upload_parser)
    # @namespace.marshal_with(_resource.list_tasks_response)
    @namespace.response(404, 'file not found', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @jwt_required()
    def get(self):
        def transform_tiff_tree(_tree):
            transformed_tree = []
            for item in _tree:
                key = list(item.keys())[0]
                if 'children' in item[key]:
                    transformed_tree.append({f"{key}.tiff": {"type": "file"}})
                else:
                    transformed_tree.append(item)
            return transformed_tree

        tree = fileService.path_to_dict(fileService.user_folder(author=get_jwt_identity()))
        tiff_tree = fileService.path_to_dict(f'{os.getenv("DATA_STORAGE")}/originals/')

        if not tiff_tree or list(tiff_tree.keys())[0] not in tiff_tree:
            tiff_tree_children = []
        else:
            tiff_tree_children = tiff_tree[list(tiff_tree.keys())[0]].get('children', [])

        user_folder_tree = tree[list(tree.keys())[0]].get('children', [])
        transformed_tiff_tree = transform_tiff_tree(tiff_tree_children)
        user_folder_tree += transformed_tiff_tree

        return {'success': 'True', 'tree': user_folder_tree}, 200

    @namespace.doc('file/deletefilefolder', security='Bearer')
    # @namespace.expect(upload_parser)
    # @namespace.marshal_with(_resource.list_tasks_response)
    @namespace.response(404, 'file not found', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @namespace.param('path', 'path to delete')
    @jwt_required()
    def delete(self):

        path = request.args.get('path')

        _path, folder = fileService.check_path(get_jwt_identity(), path)
        if _path is None:
            folder_name, ext = os.path.splitext(path)
            destination = f'{os.getenv("DATA_STORAGE")}/originals/{folder_name}'
            if os.path.exists(destination) and os.path.isdir(destination):
                Utils._rmDir(destination)
                return {'success': True, 'deleted': destination}, 200
            else:
                return {'success': False, 'message': f'path {path} not found'}, 200
        else:
            if folder:
                Utils._rmDir(_path)
            else:
                os.remove(_path)

        return {'success': True, 'deleted': path}, 200


@namespace.route('/check-file')
class CheckFileResource(Resource):
    @namespace.doc('file/check', security='Bearer')
    @namespace.response(404, 'File not found', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @namespace.param('filename', 'Filename to check')
    @jwt_required()
    def get(self):
        filename = request.args.get('filename')
        if not filename:
            return {'success': False, 'message': 'Filename parameter is required'}, 400

        user_folder = fileService.user_folder(author=get_jwt_identity())
        file_path = os.path.join(user_folder, filename)

        if not os.path.exists(file_path):
            return {'success': False, 'message': f'File {filename} not found'}, 404

        try:
            adata = anndata.read_h5ad(file_path)
            keys = list(adata.obs_keys())
            return {'success': True, 'keys': keys}, 200
        except Exception as e:
            return {'success': False, 'message': f'Error processing file: {str(e)}'}, 500
