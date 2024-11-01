from typing import List, Dict
import base64
import json
import re
import tempfile
import shutil
import os
import dill as pickle
import numpy as np
import io
import zarr
import spex_common.services.Task as TaskService
import spex_common.services.Job as JobService
import spex_common.services.Utils as Utils
from spex_common.modules.logging import get_logger
from flask_restx import Namespace, Resource
from flask import request, send_file, make_response, jsonify, send_from_directory
import tifffile
from flask_jwt_extended import jwt_required, get_jwt_identity
from .models import tasks, responses
from enum import Enum
import seaborn as sns
import matplotlib
from matplotlib import pyplot
from distutils.util import strtobool
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image
from skimage.segmentation import mark_boundaries
import scanpy as sc
import anndata
from scipy.stats import zscore
import lttb
from vitessce.data_utils import (
    optimize_adata,
)


class VisType(str, Enum):
    scatter = "scatter"
    boxplot = "boxplot"
    heatmap = "heatmap"
    barplot = "barplot"
    violin = "violin"


class ZarrStatus(str, Enum):
    started = "started"
    in_progress = "in_progress"
    complete = "complete"
    error = "error"


logger = get_logger("spex.backend")
plt.rcParams['figure.max_open_warning'] = 40

namespace = Namespace("Tasks", description="Tasks CRUD operations")

namespace.add_model(tasks.tasks_model.name, tasks.tasks_model)
namespace.add_model(tasks.task_post_model.name, tasks.task_post_model)
namespace.add_model(responses.response.name, responses.response)
namespace.add_model(tasks.a_tasks_response.name, tasks.a_tasks_response)
namespace.add_model(responses.error_response.name, responses.error_response)
namespace.add_model(tasks.list_tasks_response.name, tasks.list_tasks_response)
namespace.add_model(tasks.task_get_model.name, tasks.task_get_model)
namespace.add_model(tasks.tasks_data_get_model.name, tasks.tasks_data_get_model)
namespace.add_model(tasks.zarr_genes.name, tasks.zarr_genes)


@namespace.route("/<_id>")
@namespace.param("_id", "task id")
class TaskGetPut(Resource):
    @namespace.doc("tasks/get_one", security="Bearer")
    @namespace.response(404, "Task not found", responses.error_response)
    @namespace.response(401, "Unauthorized", responses.error_response)
    @namespace.marshal_with(tasks.a_tasks_response)
    @jwt_required()
    def get(self, _id):
        _task = TaskService.select(_id)
        if _task is None:
            return {"success": False, "message": "task not found", "data": {}}, 200

        return {"success": True, "data": _task.to_json()}, 200

    @namespace.doc("tasks/update_one", security="Bearer")
    @namespace.marshal_with(tasks.a_tasks_response)
    @namespace.expect(tasks.tasks_model)
    @namespace.response(404, "Task not found", responses.error_response)
    @namespace.response(401, "Unauthorized", responses.error_response)
    @jwt_required()
    def put(self, _id):
        _task = TaskService.select(_id)
        if _task is None:
            return {"success": False, "message": "task not found", "data": {}}, 200
        body = request.json
        _task = TaskService.update(_id, data=body)

        return {"success": True, "data": _task.to_json()}, 200

    @namespace.doc("task/delete", security="Bearer")
    @namespace.marshal_with(tasks.a_tasks_response)
    @namespace.response(404, "task not found", responses.error_response)
    @namespace.response(401, "Unauthorized", responses.error_response)
    @jwt_required()
    def delete(self, _id):
        _task = TaskService.select(_id)
        if _task is None:
            return {"success": False, "message": "task not found", "data": {}}, 200

        JobService.delete_connection(_to=_task.id)
        deleted = TaskService.delete(_task.id).to_json()
        return {"success": True, "data": deleted}, 200


@namespace.route("/image/<_id>")
@namespace.param("_id", "task id")
class TasksGetIm(Resource):
    @namespace.doc("tasks/getimage", security="Bearer")
    @namespace.response(404, "Task not found", responses.error_response)
    @namespace.response(401, "Unauthorized", responses.error_response)
    # @namespace.marshal_with(tasks.a_tasks_response)
    @jwt_required()
    def get(self, _id):
        _task = TaskService.select(_id)
        if _task is None:
            return {"success": False, "message": "task not found", "data": {}}, 200
        _task = _task.to_json()
        if _task.get("impath") is None:
            return {"success": False, "message": "image not found", "data": {}}, 200

        path = _task.get("impath")
        path = Utils.getAbsoluteRelative(path, absolute=True)

        if not os.path.exists(path):
            return {"success": False, "message": "image not found", "data": {}}, 200

        try:
            with open(path, "rb") as image:
                encoded = base64.b64encode(image.read())

                encoded = f'data:image/png;base64,{encoded.decode("utf-8")}'

                return {"success": True, "data": {"image": encoded}}, 200
        except Exception as error:
            print(f"Error: {error}")

        return {"success": False, "message": "image not found", "data": {}}, 200


@namespace.route("/list")
class TaskListPost(Resource):
    @namespace.doc("tasks/getlist", security="Bearer")
    @namespace.expect(tasks.task_post_model)
    @namespace.marshal_with(tasks.list_tasks_response)
    @namespace.response(404, "Tasks not found", responses.error_response)
    @namespace.response(401, "Unauthorized", responses.error_response)
    @jwt_required()
    def post(self):
        body = request.json
        _tasks = TaskService.select_tasks(condition="in", _key=body["ids"])
        if _tasks is None:
            return {"success": False, "data": []}, 200
        return {"success": True, "data": _tasks}, 200


@namespace.route("")
class TaskPost(Resource):
    @namespace.doc("tasks/update", security="Bearer")
    @namespace.expect(tasks.task_post_model)
    @namespace.marshal_with(tasks.list_tasks_response)
    @namespace.response(404, "Task not found", responses.error_response)
    @namespace.response(401, "Unauthorized", responses.error_response)
    @jwt_required()
    def post(self):
        body = request.json
        arr = []
        for _id in body["ids"]:
            data = dict(body)
            del data["ids"]
            task = TaskService.update(_id, data=data)
            if task is not None:
                arr.append(task.to_json())
        return {"success": True, "data": arr}, 200

    @namespace.doc("task/get", security="Bearer")
    @namespace.marshal_with(tasks.list_tasks_response)
    @namespace.response(200, "list tasks current user", tasks.list_tasks_response)
    @namespace.response(404, "tasks not found", responses.error_response)
    @namespace.response(401, "Unauthorized", responses.error_response)
    @jwt_required()
    def get(self):
        author = get_jwt_identity()
        result = TaskService.select_tasks(author=author)

        if result is None:
            return {"success": False, "message": "tasks not found", "data": {}}, 200

        return {"success": True, "data": result}, 200


class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)


@namespace.route("/file/<_id>")
@namespace.param("_id", "task id")
@namespace.param("key", "key name")
class TasksGetIm(Resource):
    @jwt_required()
    def get(self, _id):
        key: str = ""
        for arg in request.args:
            key = request.args.get(arg)

        task = TaskService.select(_id)
        if task is None:
            return {"success": False, "message": "task not found", "data": {}}, 200
        task = task.to_json()
        if task.get("result") is None:
            return {"success": False, "message": "result not found", "data": {}}, 200

        path = task.get("result")
        path = Utils.getAbsoluteRelative(path, absolute=True)

        message = "result not found"

        if not os.path.exists(path):
            return {"success": False, "message": message, "data": {}}, 200

        try:
            with open(path, "rb") as infile:
                data = pickle.load(infile)

                if not key:
                    return {"success": True, "data": list(data.keys())}, 200

                data = data.get(key)

                fd, temp_file_name = tempfile.mkstemp()
                ext = ".csv"

                if isinstance(data, np.ndarray) and key == "labels":
                    im = create_resp_from_df(data, debug=False, _format='tiff', file=True)
                    im.save(temp_file_name, format='tiff')
                    ext = ".tiff"
                elif isinstance(data, np.ndarray) and key != "labels":
                    pd.DataFrame(data).to_csv(temp_file_name, index=None, format=ext)
                else:
                    data.to_csv(temp_file_name, index=None)

                return send_file(
                    temp_file_name,
                    attachment_filename=f"{_id}_result_{key}.{ext}",
                )

        except AttributeError as error:
            logger.warning(error)
            data = json.dumps(data, cls=NumpyEncoder)
            return {"success": True, "data": data}, 200

        except Exception as error:
            message = str(error)
            logger.warning(error)

        return {"success": False, "message": message, "data": {}}, 200


@namespace.route("/anndata_load/<_id>")
@namespace.param("_id", "task id")
class TasksGetIm(Resource):
    @namespace.doc("tasks/get_anndata_file_from_task", security="Bearer")
    @namespace.response(404, "Task not found", responses.error_response)
    @namespace.response(401, "Unauthorized", responses.error_response)
    @jwt_required()
    def get(self, _id):

        task = TaskService.select(_id)
        if task is None:
            return {"success": False, "message": "task not found", "data": {}}, 200

        task = task.to_json()

        if task.get("result") is None:
            return {"success": False, "message": "result not found", "data": {}}, 200

        path = task.get("result")
        path = Utils.getAbsoluteRelative(path, absolute=True)

        message = "result not found"

        if not os.path.exists(path):
            return {"success": False, "message": message, "data": {}}, 200
        return send_file(
            path,
            attachment_filename=f"{_id}_result.h5ad",
            as_attachment=True,
            mimetype='application/octet-stream'
        )


@namespace.route("/anndata/<_id>")
@namespace.param("_id", "task id")
class TasksGetIm(Resource):
    @namespace.doc("tasks/get_anndata_file", security="Bearer")
    @namespace.response(404, "Task not found", responses.error_response)
    @namespace.response(401, "Unauthorized", responses.error_response)
    @jwt_required()
    def get(self, _id):

        task = TaskService.select(_id)
        if task is None:
            return {"success": False, "message": "task not found", "data": {}}, 200

        task = task.to_json()

        if task.get("result") is None:
            return {"success": False, "message": "result not found", "data": {}}, 200

        path = task.get("result")
        path = Utils.getAbsoluteRelative(path, absolute=True)

        message = "result not found"

        if not os.path.exists(path):
            return {"success": False, "message": message, "data": {}}, 200

        with open(path, "rb") as infile:
            data = pickle.load(infile)
            df = data['dataframe']
            df.index = df.index.astype(str)

            coordinates = np.column_stack((df['centroid-1'], df['centroid-0']))
            celltype = df[['label']].copy()
            celltype = celltype.rename(columns={'label': 'Cell_ID'})
            celltype['Cell_ID'] = celltype['Cell_ID'].astype('category')
            cl = data["channel_list"]
            if not cl:
                cl = data["all_channels"]
            expression_data = np.array(df[cl[0].lower().replace('target:', '')])
            expression_data = expression_data.reshape(-1, 1)
            expression_data = np.apply_along_axis(zscore, axis=0, arr=expression_data)

            adata = anndata.AnnData(
                X=expression_data.astype(np.float32),
                obs=pd.DataFrame(index=df.index),
                obsm={'spatial': coordinates},
                layers={'zscored': expression_data.astype(np.float32)},
            )

            for col in df.columns:
                adata.obs[col] = df[col]

            adata.obs['Cell_ID'] = celltype['Cell_ID']

            with tempfile.NamedTemporaryFile(delete=False) as f:
                adata.write(f.name)
                f.seek(0)
                return send_file(
                    f.name,
                    attachment_filename='file.h5ad',
                    as_attachment=True,
                    mimetype='application/octet-stream',
                )

        return {"success": False, "message": message, "data": {}}, 200


def create_resp_from_data(ax, debug):
    fig = ax.get_figure()

    buf = io.BytesIO()
    fig.savefig(buf, format="png")

    buf.seek(0)
    resp_data = buf.read()
    resp_data = base64.b64encode(resp_data)
    resp_data = resp_data.decode("utf-8")

    if debug:
        img = '<img src="data:image/png;base64,{}">'.format(resp_data)
        resp = make_response(img)
        resp.headers["Content-Type"] = "text/html"
    else:
        img = "data:image/png;base64,{}".format(resp_data)
        resp = make_response(img)

    return resp


def create_resp_from_df(pd_data, debug, _format="png", channels=[], file=False):
    nuc = np.zeros_like(pd_data)
    for i in channels:
        nuc += pd_data[i]

    fig, ax = plt.subplots(figsize=(10, 10))

    boundary = mark_boundaries(np.squeeze(nuc), pd_data, (0, 0, 255)).astype('uint8')
    ax.imshow(boundary)
    ax.grid(False)

    buf = io.BytesIO()
    fig.savefig(buf, format=_format, photometric='minisblack')
    buf.seek(0)

    im = Image.open(buf)

    im_arr = np.array(im)
    im_arr[np.all(im_arr == [0, 0, 0, 255], axis=-1)] = [255, 255, 255, 255]
    im = Image.fromarray(im_arr)

    im.thumbnail((800, 600), Image.ANTIALIAS)
    img_buf = io.BytesIO()
    im.save(img_buf, format=_format)
    if file:
        return im

    img_buf.seek(0)
    resp_data = img_buf.read()
    resp_data = base64.b64encode(resp_data)
    resp_data = resp_data.decode("utf-8")

    if debug:
        img = '<img src="data:image/png;base64,{}">'.format(resp_data)
        resp = make_response(img)
        resp.headers["Content-Type"] = "text/html"
    else:
        img = "data:image/png;base64,{}".format(resp_data)
        resp = make_response(img)

    return resp


@namespace.route("/vis/<_id>")
@namespace.param("_id", "task id")
@namespace.param("key", "key name")
@namespace.param("vis_name", "visualisation name")
class TasksGetIm(Resource):
    @namespace.doc("tasks/visualizer", security="Bearer")
    @namespace.response(404, "Task not found", responses.error_response)
    @namespace.response(401, "Unauthorized", responses.error_response)
    # @namespace.marshal_with(tasks.a_tasks_response)
    # @jwt_required()
    def get(self, _id):
        key: str = ""
        vis_name: str = ""
        debug: bool = False

        matplotlib.rc_file_defaults()
        try:
            pyplot.clf()
        except ValueError:
            pass
        plt.subplots(ncols=1, figsize=(5, 5))
        marker_list = []

        for k in request.args.keys():
            if k == "key":
                key = request.args.get(k)
            if k == "vis_name":
                vis_name = request.args.get(k)
            if k == "debug":
                if strtobool(request.args.get(k)):
                    debug = True
            if k == 'marker_list':
                marker_list = request.args.get(k).split(',')

        if marker_list is None and vis_name is VisType.violin:
            return {"success": False, "message": "channels not found", "data": {}}, 200

        task = TaskService.select(_id)
        if task is None:
            return {"success": False, "message": "task not found", "data": {}}, 200
        task = task.to_json()
        if task.get("result") is None:
            return {"success": False, "message": "result not found", "data": {}}, 200

        path = task.get("result")
        path = Utils.getAbsoluteRelative(path, absolute=True)

        message = "result not found"

        if not os.path.exists(path):
            return {"success": False, "message": message, "data": {}}, 200

        try:
            with open(path, "rb") as infile:
                data = pickle.load(infile)

                if not key:
                    return {"success": True, "data": list(data.keys())}, 200

                channels_str = data.get("channel_list", [])
                if not channels_str:
                    channels_str = data.get("all_channels")
                dml_0 = None
                if key == "dml":
                    dml_0 = data.get("dml_0", None)
                data = data.get(key)

        except Exception as error:
            message = str(error)
            logger.warning(message)
            return {"success": True, "data": list(data.keys())}, 200

        sns.set_theme(style="whitegrid")
        sns.reset_orig()
        sns.set(font_scale=0.7)
        ax = None
        img_list_keys = ["labels", "image"]

        if all([key in img_list_keys, type(data) == np.ndarray]):
            return create_resp_from_df(data, debug)

        if vis_name == VisType.scatter:
            if key == "dml":
                index = 0
                data_dict = {"dml": data}
                if dml_0 is not None:
                    data_dict["related_task"] = dml_0
                cols = len(data_dict.keys())
                fig, axs = plt.subplots(ncols=1, nrows=cols, figsize=(8, 4 * cols))
                fig.tight_layout()
                fig.subplots_adjust(top=0.95)
                melted_data = {}
                for item in data_dict.keys():
                    df = pd.DataFrame(data_dict.get(item))
                    to_show_data = pd.melt(df, id_vars=[0, 1, 2])
                    to_show_data["value"] = to_show_data["value"].round()
                    melted_data[item] = to_show_data

                for item in melted_data.keys():
                    ax = axs[index]
                    ax.set(xlabel=None, ylabel=None)

                    asp = np.diff(ax.get_xlim())[0] / np.diff(ax.get_ylim())[0]
                    ax.set_aspect(asp)

                    box = ax.get_position()
                    width = box.x1 - box.x0
                    height = box.y1 - box.y0
                    if len(axs) <= 10:
                        ax.set_position([0.08, box.y0, width, height])
                    else:
                        ax.set_position([0.08, box.y1 + 0.03, width, height])

                    df = melted_data.get(item).loc[(melted_data.get(item)["value"] > 0)]
                    ax.set(xlabel="x", ylabel="y")
                    sns.scatterplot(
                        y=1,
                        x=2,
                        hue="variable",
                        data=df,
                        palette="Set3",
                        ax=ax,
                        s=df.value,
                    )
                    ax.set(title=item)
                    ax.legend(
                        loc="center left", bbox_to_anchor=(1.1, 0.5), labelspacing=3
                    )

                    index += 1

            elif key == "cluster":
                df = pd.DataFrame(data)
                cluster_column_id = len(df.columns) - 1
                replace_dict: dict = {}
                if len(channels_str) == len(df.columns) - 4:
                    for item in range(len(channels_str)):
                        replace_dict[item + 3] = channels_str[item]

                if replace_dict.keys():
                    df.rename(columns=replace_dict, inplace=True)

                df.rename(columns={cluster_column_id: "cluster"}, inplace=True)

                to_show_data = pd.melt(df, id_vars=[0, 1, 2, "cluster"])
                to_show_data["value"] = to_show_data["value"].round()
                if marker_list:
                    to_show_data = to_show_data[to_show_data["variable"].isin(marker_list)]

                cols = len(to_show_data["variable"].unique())
                # cols = 5
                fig, axs = plt.subplots(ncols=1, nrows=cols, figsize=(8, 4 * cols))
                fig.tight_layout()
                fig.subplots_adjust(top=0.95)
                index = 0

                for channel in to_show_data["variable"].unique():

                    df = to_show_data.loc[
                        (to_show_data["variable"] == channel)
                        & (to_show_data["value"] > 0)
                        ]

                    if type(axs) == np.ndarray:
                        ax = axs[index]
                    else:
                        ax = axs
                        axs = [ax]

                    ax.set(xlabel=None, ylabel=None)
                    asp = np.diff(ax.get_xlim())[0] / np.diff(ax.get_ylim())[0]
                    ax.set_aspect(asp)

                    box = ax.get_position()
                    width = box.x1 - box.x0
                    height = box.y1 - box.y0
                    if len(axs) <= 10:
                        ax.set_position([0.08, box.y0, width, height])
                    else:
                        ax.set_position([0.08, box.y1 + 0.03, width, height])

                    if len(df["cluster"]):
                        sns.scatterplot(
                            y=1, x=2, data=df, palette="Set3", hue=df["cluster"], ax=ax
                        )
                    else:
                        sns.scatterplot(
                            y=1, x=2, data=df, hue=df["cluster"], ax=ax
                        )

                    index += 1

                    # Put a legend below current axis
                    ax.legend(
                        loc="center left",
                        bbox_to_anchor=(1.04, 0.5),
                        fancybox=True,
                        shadow=True,
                        ncol=5,
                        title=channel,
                    )
                fig.suptitle(vis_name)

            elif key == "dataframe":
                to_show_data = pd.melt(
                    data, id_vars=["label", "centroid-0", "centroid-1"]
                )
                to_show_data["value"] = to_show_data["value"].round()
                if marker_list:
                    to_show_data = to_show_data[to_show_data["variable"].isin(marker_list)]

                cols = len(to_show_data["variable"].unique())
                fig, axs = plt.subplots(ncols=1, nrows=cols, figsize=(8, 4 * cols))
                fig.tight_layout()
                fig.subplots_adjust(top=0.95)
                index = 0

                for channel in to_show_data["variable"].unique():
                    df = to_show_data.loc[
                        (to_show_data["variable"] == channel)
                        & (to_show_data["value"] > 0)
                        ]
                    if type(axs) == np.ndarray:
                        ax = axs[index]
                    else:
                        ax = axs
                        axs = [ax]

                    ax.set(xlabel=None, ylabel=None)
                    asp = np.diff(ax.get_xlim())[0] / np.diff(ax.get_ylim())[0]
                    ax.set_aspect(asp)

                    box = ax.get_position()
                    width = box.x1 - box.x0
                    height = box.y1 - box.y0
                    if len(axs) <= 10:
                        ax.set_position([0.08, box.y0, width, height])
                    else:
                        ax.set_position([0.08, box.y1 + 0.03, width, height])

                g = sns.relplot(
                    x="centroid-1",
                    y="centroid-0",
                    hue=df["value"],
                    alpha=0.8,
                    s=12,
                    palette="plasma",
                    data=df,
                    ax=ax,
                )
                for ax in g.axes[0]:
                    ax.invert_yaxis()

                index += 1
                fig.suptitle(vis_name)

            elif key == "qfmatch":
                if debug:
                    img = '<img src="data:image/png;base64,{}">'.format(data)
                    resp = make_response(img)
                    resp.headers["Content-Type"] = "text/html"
                else:
                    img = "data:image/png;base64,{}".format(data)
                    resp = make_response(img)
                return resp
            elif key == "spatial":
                df_all = pd.DataFrame()
                fig, axs = plt.subplots(ncols=1, nrows=2, figsize=(7, 14))
                for d in data:
                    for item in d:
                        CLQ_Pval = item["CLQ_Pval"]
                        CLQ_global = item["CLQ_global"]
                        CLQ_local = item["CLQ_local"]
                        cluster_id = item["LCLQ_catrgory"]["cluster_id"]
                        x = item["LCLQ_catrgory"]["x"]
                        y = item["LCLQ_catrgory"]["y"]
                        CLQ_value = item["LCLQ_catrgory"]["CLQ_value"]
                        CLQ_group = item["LCLQ_catrgory"]["CLQ_group"]

                        df = pd.DataFrame(
                            {
                                "x": x,
                                "y": y,
                                "cluster_id": cluster_id,
                                "CLQ_group": CLQ_group,
                                "CLQ_value": CLQ_value,
                                "CLQ_local": CLQ_local,
                                "CLQ_global": CLQ_global,
                                "CLQ_Pval": CLQ_Pval,
                            }
                        )
                        df_all = df_all.append(df)

                df_all = df_all.dropna()
                df_all["CLQ_Pval_alpha"] = (
                    df_all["CLQ_Pval"]
                    .map({"non-significant": 0.5, "attractive": 0.7, "avoidance": 1.0})
                    .astype(float)
                )
                ax = axs[0]
                sns.scatterplot(
                    data=df_all,
                    x="x",
                    y="y",
                    hue="cluster_id",
                    style="CLQ_group",
                    size="CLQ_local",
                    alpha=df_all["CLQ_Pval_alpha"],
                    markers=["o", "s", "^"],
                    ax=ax,
                )
                ax.legend(bbox_to_anchor=(0.5, 1.2), loc="upper center", ncol=4)

                ax = axs[1]
                sns.boxplot(x="cluster_id", y="CLQ_Pval_alpha", data=df_all, ax=ax)

        if vis_name == VisType.boxplot:
            to_show_data = pd.melt(data, id_vars=["label", "centroid-0", "centroid-1"])
            if marker_list:
                to_show_data = to_show_data[to_show_data["variable"].isin(marker_list)]
            ax = sns.boxplot(y="variable", x="value", data=to_show_data, palette="Set3")
            ax.set_yticklabels(to_show_data['variable'].unique())

            ax.set(title=vis_name)

        if vis_name == VisType.heatmap:
            if key == "CellCell":
                to_show_data = data.get("pVal", [])
                to_show_data = np.delete(to_show_data, 0, 0)
                to_show_data = np.delete(to_show_data, 0, 1)

                ax = sns.heatmap(
                    to_show_data,
                    cmap="coolwarm",
                    fmt="g",
                )
                ax.xaxis.set_tick_params(labelsize="small")
                ax.set(title=vis_name)
                ax.set(
                    xlabel="Cell phenotype in neighborhood",
                    ylabel="Cell phenotype of interest",
                )

            else:
                fig, ax = plt.subplots(ncols=1, nrows=1, figsize=(14, 7))
                to_show = np.delete(data, [0, 1, 2], axis=1)
                columns = channels_str + ["cluster"]
                _, c = to_show.shape
                adata = sc.AnnData(to_show, dtype='float64')
                adata.var_names = columns

                cluster_labels = to_show[:, -1]
                cluster_labels = pd.Categorical(cluster_labels.astype(int))
                adata.obs['cluster_labels'] = cluster_labels

                cols: set = set(columns[:-1])
                if marker_list:
                    cols = cols.intersection(set(marker_list))

                sc.pl.matrixplot(
                    adata,
                    var_names=list(cols),
                    groupby='cluster_labels',
                    dendrogram=True,
                    standard_scale='var',
                    ax=ax,
                    show=False,
                )
        if vis_name == VisType.violin:

            fig, axs = plt.subplots(
                nrows=len(marker_list),
                ncols=1,
                figsize=(7, 7 * len(marker_list))
            )
            if len(marker_list) == 1:
                axs = [axs]

            to_show = np.delete(data, [0, 1, 2], axis=1)
            columns = channels_str + ["cluster"]
            _, c = to_show.shape
            adata = sc.AnnData(to_show, dtype='float64')
            adata.var_names = columns
            cluster_labels = to_show[:, -1]
            adata.obs['cluster_labels'] = cluster_labels

            cluster_labels = to_show[:, -1]
            cluster_labels = pd.Categorical(cluster_labels.astype(int))
            adata.obs['cluster_labels'] = cluster_labels

            for i, marker in enumerate(marker_list):
                ax = axs[i]
                sc.pl.violin(
                    adata,
                    marker,
                    groupby='cluster_labels',
                    rotation=45,
                    show=False,
                    ax=ax
                )

            plt.tight_layout()

        if vis_name == VisType.barplot:
            to_show = np.delete(data, [0, 1, 2], axis=1)
            ax = sns.barplot(data=to_show, label="Total", color="b")
            ax.set(title=vis_name)

            try:
                ax.set_xticklabels(channels_str)
            except ValueError as error:
                logger.info(error)

        if not ax:
            return {"success": False, "message": "result not found", "data": {}}, 200

        return create_resp_from_data(ax, debug)


def write_zarr_for_tasks(tasks_list: List[Dict], filtered_adatas: Dict[str, anndata.AnnData]):
    for task in tasks_list:
        if task['name'] == 'feature_extraction':
            omero_id = task['omeroId']
            result_path = task.get("result")
            if not result_path:
                continue
            absolute_path = Utils.getAbsoluteRelative(result_path, absolute=True)
            zarr_dir = f'{os.path.dirname(absolute_path)}/static/clusters.h5ad.zarr'
            if os.path.exists(zarr_dir):
                shutil.rmtree(zarr_dir)
            logger.debug(f"zarr_dir: {zarr_dir}")
            os.makedirs(zarr_dir, exist_ok=True)

            current_data = filtered_adatas.get(omero_id)
            if current_data:
                current_data.write_zarr(zarr_dir, chunks=[current_data.shape[0], 2000])


def create_zarr_archive(task_json) -> ZarrStatus:
    result_path = task_json.get("result")
    if not result_path:
        return ZarrStatus.error

    absolute_path = Utils.getAbsoluteRelative(result_path, absolute=True)
    zarr_dir = f'{os.path.dirname(absolute_path)}/static/cells.h5ad.zarr'
    started_file_path = f"{os.path.dirname(zarr_dir)}/started"
    completed_file_path = f"{os.path.dirname(zarr_dir)}/complete"
    if os.path.exists(started_file_path):
        return ZarrStatus.started

    if os.path.exists(completed_file_path) and os.path.exists(zarr_dir):
        return ZarrStatus.complete

    if (
            os.path.exists(completed_file_path)
            and not os.path.exists(started_file_path)
            and os.path.exists(zarr_dir)
    ):
        return ZarrStatus.complete

    if not os.path.exists(zarr_dir):
        os.makedirs(os.path.dirname(started_file_path), exist_ok=True)
        with open(started_file_path, 'w') as started_file:
            started_file.write("started")

        with open(absolute_path, "rb") as infile:
            to_show_data = pickle.load(infile)

        if to_show_data:

            os.makedirs(os.path.dirname(zarr_dir), exist_ok=True)
            adata = to_show_data['adata']
            if task_json.get("name") != "Cluster ST data":
                if 'x_coordinate' not in adata.obs.columns or 'y_coordinate' not in adata.obs.columns:
                    adata.obs['x_coordinate'] = 0
                    adata.obs['y_coordinate'] = 0
                xy_coordinates = adata.obs[["x_coordinate", "y_coordinate"]].values

                adata.obsm['xy_scaled'] = xy_coordinates
                for col in adata.obs.columns:
                    if adata.obs[col].dtype == '<i8':
                        adata.obs[col] = adata.obs[col].astype('int32')
            else:
                xy_coordinates = adata.obs[["min_x", "min_y"]].values
                if 'leiden' in adata.obs.keys():
                    clusters = adata.obs["leiden"].values
                else:
                    clusters = adata.obs["louvain"].values
                # xy_coordinates = adata.obs[["x_coordinate", "y_coordinate"]].values
                adata._n_obs = len(adata.obs['min_x'])
                adata._n_vars = len(adata.var['n_cells'])

                adata.obsm['xy_scaled'] = xy_coordinates
                for col in adata.obs.columns:
                    if adata.obs[col].dtype == '<i8':
                        adata.obs[col] = adata.obs[col].astype('int32')
                adata.X = adata.X.astype('float32')

            reduced_polygons = []
            obs_cols = []
            obsm_keys = []
            if task_json.get("name") not in ["phenograph_cluster", "Cluster ST data"]:
                cell_polygons = np.array(adata.obsm['cell_polygon'])

                for polygon in cell_polygons:
                    num_points = len(polygon)
                    if num_points < 32:
                        extra_points_needed = 32 - num_points
                        extra_points = np.tile(polygon[-1:], (extra_points_needed, 1))
                        new_polygon = np.vstack([polygon, extra_points])
                        reduced_polygon = new_polygon
                    else:
                        swapped_polygon = polygon[:, [1, 0]]
                        reduced_polygon = lttb.downsample(np.array(swapped_polygon), n_out=32, validators=[])

                    reduced_polygons.append(reduced_polygon)

                adata.obsm['cell_polygon'] = np.array(reduced_polygons)

                obs_cols = ['Cell_ID', 'Nucleus_area', 'x_coordinate', 'y_coordinate']
                obsm_keys = ['spatial', 'xy_scaled', 'cell_polygon']
                optimized_adata = optimize_adata(
                    adata,
                    obs_cols=obs_cols,
                    obsm_keys=obsm_keys,
                    var_cols=None,
                    varm_keys=None,
                    layer_keys=['X_uint8'],
                    remove_X=False,
                    optimize_X=True
                )

            if task_json.get("name") in ["phenograph_cluster", "Cluster ST data"]:
                if 'cluster_phenograph' not in adata.obs.keys():
                    if 'leiden' in adata.obs.keys():
                        clusters = adata.obs["leiden"].values
                    else:
                        clusters = adata.obs["louvain"].values
                    adata.obs['cluster_phenograph'] = clusters
                    adata.obs['image_id'] = ['adata'] * adata.shape[0]

                obs_cols += ['cluster_phenograph', 'image_id']
                obsm_keys += ['X_umap']
                optimized_adata = optimize_adata(
                    adata,
                    obs_cols=obs_cols,
                    obsm_keys=obsm_keys,
                    var_cols=None,
                    varm_keys=None,
                    remove_X=False,
                    optimize_X=True
                )

                filtered_adatas = {}
                unique_image_ids = optimized_adata.obs['image_id'].unique()
                for image_id in unique_image_ids:
                    current_data = optimized_adata[optimized_adata.obs['image_id'] == image_id].copy()
                    filtered_adatas[image_id] = current_data
                fe_tasks = to_show_data.get('tasks_list', [])
                if len(filtered_adatas.keys()) > 0 and fe_tasks:
                    write_zarr_for_tasks(fe_tasks, filtered_adatas)

            for col in optimized_adata.obs.select_dtypes(include='category').columns:
                optimized_adata.obs[col] = optimized_adata.obs[col].cat.add_categories("Unknown")

            optimized_adata.write_zarr(zarr_dir, chunks=[optimized_adata.shape[0], 2000])
            os.remove(started_file_path)
            with open(f"{os.path.dirname(zarr_dir)}/complete", 'w') as complete_file:
                complete_file.write("complete")

            if os.path.exists(zarr_dir):
                return ZarrStatus.complete
            else:
                return ZarrStatus.error
        return ZarrStatus.error


def strip_no_cache(url):
    if 'nocache' in url.lower():
        parts = url.split('/')
        for i, part in enumerate(parts):
            if 'nocache' in part.lower():
                return '/'.join(parts[i+1:])
    return url


@namespace.route("/static/<_id>/<path:filepath>")
@namespace.param("_id", "task id")
class TaskStaticGet(Resource):
    @namespace.doc("tasks/vitesscegenes")
    @namespace.response(404, "Task not found", responses.error_response)
    @namespace.response(401, "Unauthorized", responses.error_response)
    def get(self, _id, filepath):

        filepath = strip_no_cache(filepath)
        task = TaskService.select(_id)
        if not task:
            return {"success": False, "message": "task not found", "data": {}}, 200

        task_json = task.to_json()
        result_path = task_json.get("result")
        if not result_path:
            return False

        absolute_path = Utils.getAbsoluteRelative(result_path, absolute=True)
        created = create_zarr_archive(task_json)

        z_d = f'{os.path.dirname(absolute_path)}/static/cells.h5ad.zarr'
        complete_file_path = f"{os.path.dirname(z_d)}/complete"
        started_file_path = f"{os.path.dirname(z_d)}/started"

        if os.path.exists(started_file_path) and not os.path.exists(complete_file_path):
            return {"success": False, "message": "result not yet available", "data": {}}, 408

        if created == ZarrStatus.complete:
            return send_from_directory(z_d, filepath)
        else:
            return {"success": False, "message": "result not found", "data": {}}, 200


@namespace.route("/zarr_structure/<_id>")
@namespace.param("_id", "task id")
class TaskZarrStructure(Resource):
    @namespace.doc("tasks/vitesscegenes")
    @namespace.response(404, "Task not found", responses.error_response)
    @namespace.response(401, "Unauthorized", responses.error_response)
    def get(self, _id):

        task = TaskService.select(_id)
        if not task:
            return {"success": False, "message": "task not found", "data": {}}, 200

        task_json = task.to_json()
        result_path = task_json.get("result")
        if not result_path:
            return False

        absolute_path = Utils.getAbsoluteRelative(result_path, absolute=True)
        created = create_zarr_archive(task_json)

        z_d = f'{os.path.dirname(absolute_path)}/static/cells.h5ad.zarr'
        complete_file_path = f"{os.path.dirname(z_d)}/complete"
        started_file_path = f"{os.path.dirname(z_d)}/started"

        if os.path.exists(started_file_path) and not os.path.exists(complete_file_path):
            return {"success": False, "message": "result not yet available", "data": {}}, 408

        if created == ZarrStatus.complete:
            ad = anndata.read_zarr(z_d);
            clusters = list(set(ad.obs[ad.obs.keys()[0]]));
            return {"success": True, "data": list(ad.var_names), "clusters": clusters}
        else:
            return {"success": False, "message": "result not found", "data": [], "clusters": []}, 200

    @namespace.doc('tasks/zarr_change', security='Bearer')
    @namespace.expect(tasks.zarr_genes)
    @namespace.response(404, "Task not found", responses.error_response)
    @namespace.response(401, "Unauthorized", responses.error_response)
    def post(self, _id):
        body = request.json
        genes_to_remove = body.get('data', [])
        clusters = body.get('clusters', [])

        task = TaskService.select(_id)
        if not task:
            return {"success": False, "message": "task not found", "data": {}}, 200

        task_json = task.to_json()
        result_path = task_json.get("result")
        if not result_path:
            return {"success": False, "message": "result path not found", "data": {}}, 200

        absolute_path = Utils.getAbsoluteRelative(result_path, absolute=True)
        z_d = f'{os.path.dirname(absolute_path)}/static/cells.h5ad.zarr'
        complete_file_path = f"{os.path.dirname(z_d)}/complete"
        started_file_path = f"{os.path.dirname(z_d)}/started"

        if os.path.exists(started_file_path) and not os.path.exists(complete_file_path):
            return {"success": False, "message": "result not yet available", "data": {}}, 408

        created = create_zarr_archive(task_json)
        if created == ZarrStatus.complete:
            ad = anndata.read_zarr(z_d)

            if clusters:

                clust_col = ad.obs.columns[-2:][0]
                ad.obs[clust_col] = ad.obs[clust_col].astype(str)

                for cluster_map in clusters:
                    for old_cluster, new_cluster in cluster_map.items():
                        ad.obs[clust_col] = ad.obs[clust_col].replace(old_cluster, new_cluster)
                ad.obs[clust_col] = ad.obs[clust_col].astype('category')

            to_save = set(ad.var_names).intersection(set(genes_to_remove))
            if len(to_save) == 0:
                return {
                    "success": False, "message": "no intersection found, need to leave at least one var", "data": {}
                }, 200

            ad_filtered = ad[:, ad.var_names.isin(to_save)]
            ad_filtered.write_zarr(z_d)
            clusters = list(set(ad_filtered.obs[ad_filtered.obs.keys()[0]]));
            return {
                "success": True,
                "message": "genes removed successfully",
                "data": list(ad_filtered.var_names),
                "clusters": clusters
            }
        else:
            return {
                "success": False,
                "message": "result not found",
                "data": {},
                "clusters": []
            }, 200


@namespace.route("/phenograph_static/<_id>/<path:filepath>")
@namespace.param("_id", "task id")
class TaskClustersGet(Resource):
    @namespace.doc("tasks/vitessceclusters")
    @namespace.response(404, "Task not found", responses.error_response)
    @namespace.response(401, "Unauthorized", responses.error_response)
    def get(self, _id, filepath):

        task = TaskService.select(_id)
        if not task:
            return {"success": False, "message": "task not found", "data": {}}, 200

        task_json = task.to_json()
        result_path = task_json.get("result")
        if not result_path:
            return False

        absolute_path = Utils.getAbsoluteRelative(result_path, absolute=True)
        z_d = f'{os.path.dirname(absolute_path)}/static/clusters.h5ad.zarr'

        if os.path.exists(z_d):
            return send_from_directory(z_d, filepath)
        else:
            return {"success": False, "message": "result not found", "data": {}}, 408


@namespace.route("/clq_static/<_id>/<path:filepath>")
@namespace.param("_id", "task id")
class TaskClqGet(Resource):
    @namespace.doc("tasks/vitessceClq")
    @namespace.response(404, "Task not found", responses.error_response)
    @namespace.response(401, "Unauthorized", responses.error_response)
    def get(self, _id, filepath):

        task = TaskService.select(_id)
        if not task:
            return {"success": False, "message": "task not found", "data": {}}, 200

        task_json = task.to_json()
        result_path = task_json.get("result")
        if not result_path:
            return False

        absolute_path = Utils.getAbsoluteRelative(result_path, absolute=True)
        z_d = f'{os.path.dirname(absolute_path)}/static/zarr.h5ad.zarr'

        if os.path.exists(z_d):
            return send_from_directory(z_d, filepath)
        else:
            return {"success": False, "message": "result not found", "data": {}}, 408


@namespace.route("/get_result_data/<_id>")
@namespace.param("_id", "job id")
class TaskStaticGet(Resource):
    @namespace.doc("tasks/vitesscegenes")
    @namespace.response(404, "Task not found", responses.error_response)
    @namespace.response(401, "Unauthorized", responses.error_response)
    @namespace.expect(tasks.tasks_data_get_model)
    def post(self, _id):

        body = request.json

        _tasks = TaskService.select_tasks(parent=_id)
        if not _tasks:
            return {"success": False, "message": "task not found", "data": {}}, 200
        else:
            result_data = {}
            for task_json in _tasks:
                result_path = task_json.get("result")
                if not result_path:
                    continue

                absolute_path = Utils.getAbsoluteRelative(result_path, absolute=True)
                with open(absolute_path, "rb") as infile:
                    to_show_data = pickle.load(infile)

                if to_show_data:
                    for _field in body['fields']:
                        result_data[_field] = to_show_data[_field]

                if len(result_data.keys()) > 0:
                    return {"success": True, "data": result_data}, 200

        return {"success": False, "message": "result not found", "data": {}}, 200


def delete_zarr_archive(task_json):
    absolute_path = Utils.getAbsoluteRelative(task_json.get("result"), absolute=True)
    static_folder_path = f'{os.path.dirname(absolute_path)}/static'

    if os.path.exists(static_folder_path):
        shutil.rmtree(static_folder_path)

    return False


@namespace.route("/vitessce/<_id>")
@namespace.param("_id", "task id")
class TaskConfigGet(Resource):
    base_url = 'REACT_APP_BACKEND_URL_ROOT'

    def get_feature_extraction_config(self, task):
        _id = task.id
        _conf = {
            "version": "1.0.15",
            "name": "feature_extraction_config",
            "description": "vitessce setup for feature extraction",
            "datasets": [
                {
                    "uid": "B",
                    "name": "zarr",
                    "files": [
                        {
                            "fileType": "anndata.zarr",
                            "url": f"{self.base_url}tasks/static/{_id}",
                            "coordinationValues": {
                                "obsType": "cell",
                                "featureType": "channel",
                                "featureValueType": "expression"
                            },
                            "options": {
                                "obsLocations": {
                                    "path": "obsm/xy_scaled"
                                },
                                "obsSegmentations": {
                                    "path": "obsm/cell_polygon"
                                },
                                "obsFeatureMatrix": {
                                    "path": "X"
                                },
                                "obsSets": [
                                    {
                                        "name": "Nucleus_area",
                                        "path": "obs/Nucleus_area"
                                    },
                                ]
                            }
                        },
                        {
                            "fileType": "image.ome-tiff",
                            "url": f"{self.base_url}images/download/original/{task.omeroId}.ome.tif"
                        }
                    ]
                }
            ],
            "initStrategy": "auto",
            "coordinationSpace": {
                "obsType": {
                    "B": "cell"
                },
                "featureType": {
                    "A": "channel"
                },
                "featureValueType": {
                    "C": "expression"
                },
                "spatialSegmentationLayer": {
                    "B": {
                        "radius": 3,
                        "stroked": True,
                        "visible": True,
                        "opacity": 1
                    }
                },
                "featureSelection": {
                    "D": []
                },
            },
            "layout": [
                # Layer Controller ( 30% width)
                {
                    "component": "layerController",
                    "coordinationScopes": {
                        "obsType": "B",
                        "spatialSegmentationLayer": "B"
                    },
                    "h": 4,
                    "w": 3,
                    "x": 0,
                    "y": 0,
                    "uid": "I"
                },
                # Channel List ( 20%  width)
                {
                    "component": "featureList",
                    "h": 4,
                    "w": 2,
                    "x": 3,
                    "y": 0,
                    "coordinationScopes": {
                        "obsType": "B",
                        "featureType": "A",
                        "featureValueType": "C",
                        "featureSelection": "D"
                    },
                    "uid": "F"
                },
                # Spatial (left 50% width)
                {
                    "component": "spatial",
                    "h": 4,
                    "w": 5,
                    "x": 5,
                    "y": 0,
                    "coordinationScopes": {
                        "obsType": "B",
                        "featureType": "A",
                        "featureValueType": "C",
                        "spatialSegmentationLayer": "B",
                        "featureSelection": "D"
                    },
                    "uid": "B"
                },
                # Expression histogramm (second level)
                {
                    "component": "featureValueHistogram",
                    "h": 4,
                    "w": 4,
                    "x": 4,
                    "y": 4,
                    "coordinationScopes": {
                        "obsType": "B",
                        "featureType": "A",
                        "featureValueType": "C",
                        "featureSelection": "D",
                    },
                    "uid": "H"
                },
                # Heatmap (second level)
                {
                    "component": "heatmap",
                    "h": 4,
                    "w": 4,
                    "x": 0,
                    "y": 4,
                    "coordinationScopes": {
                        "obsType": "B",
                        "featureType": "A",
                        "featureValueType": "C",
                        "featureSelection": "D"
                    },
                    "uid": "C"
                }
            ],
        }
        return _conf

    def get_combined_config(self, task):
        _id = task.id
        _conf = {
            "version": "1.0.15",
            "name": "feature_extraction_config",
            "description": "vitessce setup for feature extraction",
            "datasets": [
                {
                    "uid": "B",
                    "name": "zarr",
                    "files": [
                        {
                            "fileType": "anndata.zarr",
                            "url": f"{self.base_url}tasks/static/{_id}",
                            "coordinationValues": {
                                "obsType": "cell",
                                "featureType": "channel",
                                "featureValueType": "expression"
                            },
                            "options": {
                                "obsLocations": {
                                    "path": "obsm/xy_scaled"
                                },
                                "obsSegmentations": {
                                    "path": "obsm/cell_polygon"
                                },
                                "obsFeatureMatrix": {
                                    "path": "X"
                                },
                                "obsSets": [
                                    {
                                        "name": "Nucleus_area",
                                        "path": "obs/Nucleus_area"
                                    },
                                ]
                            }
                        },
                        {
                            "fileType": "image.ome-tiff",
                            "url": f"{self.base_url}images/download/original/{task.omeroId}.ome.tif"
                        },
                        {
                            "fileType": "anndata.zarr",
                            "url": f"{self.base_url}tasks/phenograph_static/{_id}",
                            "coordinationValues": {
                                "obsType": "cell",
                                "featureType": "gene",
                                "featureValueType": "expression",
                                "embeddingType": "UMAP"
                            },
                            "options": {
                                "obsEmbedding": {
                                    "path": "obsm/X_umap"
                                },
                                "obsFeatureMatrix": {
                                    "path": "X"
                                },
                                "obsSets": [
                                    {
                                        "name": "Phenograph Cluster",
                                        "path": "obs/cluster_phenograph"
                                    }
                                ]
                            }
                        }
                    ]
                }
            ],
            "initStrategy": "auto",
            "coordinationSpace": {
                "obsType": {
                    "B": "cell",
                    "C": "cell"
                },
                "featureType": {
                    "A": "channel",
                    "C": "gene"
                },
                "featureValueType": {
                    "C": "expression"
                },
                "embeddingType": {
                    "UMAP": "UMAP",
                    "C": "UMAP"
                },
                "spatialSegmentationLayer": {
                    "B": {
                        "radius": 3,
                        "stroked": True,
                        "visible": True,
                        "opacity": 1
                    },
                    "C": {
                        "radius": 3,
                        "stroked": True,
                        "visible": True,
                        "opacity": 1
                    }
                },
                "featureSelection": {
                    "D": [],
                    "C": []
                },
                "obsColorEncoding": {
                    "A": "cellSetSelection",
                    "C": "cellSetSelection"
                },
            },
            "layout": [
                # Layer Controller ( 30% width)
                {
                    "component": "layerController",
                    "coordinationScopes": {
                        "obsType": "B",
                        "spatialSegmentationLayer": "B"
                    },
                    "h": 4,
                    "w": 3,
                    "x": 0,
                    "y": 0,
                    "uid": "I"
                },
                # Channel List ( 20%  width)
                {
                    "component": "featureList",
                    "h": 4,
                    "w": 2,
                    "x": 3,
                    "y": 0,
                    "coordinationScopes": {
                        "obsType": "B",
                        "featureType": "A",
                        "featureValueType": "C",
                        "featureSelection": "D"
                    },
                    "uid": "F"
                },
                # Spatial (left 50% width)
                {
                    "component": "spatial",
                    "h": 4,
                    "w": 5,
                    "x": 5,
                    "y": 0,
                    "coordinationScopes": {
                        "obsType": "B",
                        "featureType": "A",
                        "featureValueType": "C",
                        "spatialSegmentationLayer": "B",
                        "featureSelection": "D"
                    },
                    "uid": "B"
                },
                # Expression histogramm (second level)
                {
                    "component": "featureValueHistogram",
                    "h": 4,
                    "w": 4,
                    "x": 4,
                    "y": 4,
                    "coordinationScopes": {
                        "obsType": "B",
                        "featureType": "A",
                        "featureValueType": "C",
                        "featureSelection": "D",
                    },
                    "uid": "H"
                },
                # Heatmap (second level)
                {
                    "component": "heatmap",
                    "h": 4,
                    "w": 4,
                    "x": 0,
                    "y": 4,
                    "coordinationScopes": {
                        "obsType": "B",
                        "featureType": "A",
                        "featureValueType": "C",
                        "featureSelection": "D"
                    },
                    "uid": "C"
                },
                {
                    "component": "scatterplot",
                    "h": 4,
                    "w": 4,
                    "x": 0,
                    "y": 8,
                    "coordinationScopes": {
                        "embeddingType": "UMAP",
                        "featureType": "C",
                        "featureSelection": "C",
                        "obsColorEncoding": "C",
                        "obsSetColor": "C",
                        "obsSetSelection": "C",
                        "featureValueColormapRange": "C",
                        "obsSetHighlight": "C",
                        "embeddingObsSetLabelsVisible": "C"
                    },
                    "uid": "scatterplot_C"
                },
                {
                    "component": "obsSets",
                    "h": 4,
                    "w": 3,
                    "x": 5,
                    "y": 8,
                    "coordinationScopes": {
                        "obsSetSelection": "C",
                        "obsSetColor": "C"
                    },
                    "uid": "obsSets_C"
                }
            ],
        }
        return _conf

    def get_phenograph_config(self, task):
        _id = task.id
        _conf = {
            "version": "1.0.15",
            "name": "scatterplot_config",
            "description": "vitessce setup for scatterplot",
            "datasets": [
                {
                    "uid": "A",
                    "name": "zarr",
                    "files": [
                        {
                            "fileType": "anndata.zarr",
                            "url": f"{self.base_url}tasks/static/{_id}",
                            "coordinationValues": {
                                "obsType": "cell",
                                "featureType": "gene",
                                "featureValueType": "expression",
                                "embeddingType": "UMAP"
                            },
                            "options": {
                                "obsEmbedding": {
                                    "path": "obsm/X_umap"
                                },
                                "obsFeatureMatrix": {
                                    "path": "X"
                                },
                                "obsSets": [
                                    {
                                        "name": "Phenograph Cluster",
                                        "path": "obs/cluster_phenograph"
                                    },
                                    {
                                        "name": "image id",
                                        "path": "obs/image_id"
                                    }
                                ]
                            }
                        }
                    ]
                }
            ],
            "initStrategy": "auto",
            "coordinationSpace": {
                "embeddingType": {
                    "UMAP": "UMAP"
                },
                "obsType": {
                    "A": "cell"
                },
                "obsSetHighlight": {
                    "A": None,
                    "B": None
                },
                "featureValueColormapRange": {
                    "A": [
                        0,
                        0.1
                    ]
                },
                "embeddingObsSetLabelsVisible": {
                    "A": True
                },
                "obsSetSelection": {
                    "A": None,
                    "B": None
                },
                "obsSetColor": {
                    "A": None,
                    "B": None
                }
            },
            "layout": [
                {
                    "component": "scatterplot",
                    "h": 4,
                    "w": 4,
                    "x": 0,
                    "y": 0,
                    "coordinationScopes": {
                        "embeddingType": "UMAP",
                        "featureValueColormapRange": "A",
                        "obsLabelsType": [
                            "A"
                        ]
                    },
                    "uid": "S"
                },
                {
                    "component": "heatmap",
                    "coordinationScopes": {
                        "featureValueColormapRange": "A",
                        "obsLabelsType": [
                            "A"
                        ]
                    },
                    # "props": {
                    #     "transpose": True
                    # },

                    "h": 4,
                    "w": 10,
                    "x": 0,
                    "y": 4,
                    "uid": "H"
                },
                # {
                #     "component": "obsSetFeatureValueDistribution",
                #     "x": 7,
                #     "y": 4,
                #     "w": 5,
                #     "h": 2
                # },
                {
                    "component": "obsSets",
                    "h": 4,
                    "w": 3,
                    "x": 5,
                    "y": 0,
                    "uid": "F"
                }
            ]
        }

        return _conf

    def get_cluster_config(self, task):
        _id = task.id
        _conf = {
            "version": "1.0.15",
            "name": "scatterplot_config",
            "description": "vitessce setup for scatterplot",
            "datasets": [
                {
                    "uid": "A",
                    "name": "zarr",
                    "files": [
                        {
                            "fileType": "anndata.zarr",
                            "url": f"{self.base_url}tasks/static/{_id}",
                            "coordinationValues": {
                                "obsType": "cell",
                                "featureType": "gene",
                                "featureValueType": "expression",
                                "embeddingType": "UMAP"
                            },
                            "options": {
                                "obsEmbedding": {
                                    "path": "obsm/X_umap"
                                },
                                "obsFeatureMatrix": {
                                    "path": "X"
                                },
                                "obsSets": [
                                    {
                                        "name": "cluster",
                                        "path": "obs/cluster_phenograph"
                                    }
                                ]
                            }
                        }
                    ]
                }
            ],
            "initStrategy": "auto",
            "coordinationSpace": {
                "embeddingType": {
                    "UMAP": "UMAP"
                },
                "obsType": {
                    "A": "cell"
                },
                "obsSetHighlight": {
                    "A": None,
                    "B": None
                },
                "featureValueColormapRange": {
                    "A": [
                        0,
                        0.1
                    ]
                },
                "embeddingObsSetLabelsVisible": {
                    "A": True
                },
                "obsSetSelection": {
                    "A": None,
                    "B": None
                },
                "obsSetColor": {
                    "A": None,
                    "B": None
                }
            },
            "layout": [
                {
                    "component": "scatterplot",
                    "h": 4,
                    "w": 4,
                    "x": 0,
                    "y": 0,
                    "coordinationScopes": {
                        "embeddingType": "UMAP",
                        "featureValueColormapRange": "A",
                        "obsLabelsType": [
                            "A"
                        ]
                    },
                    "uid": "S"
                },
                {
                    "component": "heatmap",
                    "coordinationScopes": {
                        "featureValueColormapRange": "A",
                        "obsLabelsType": [
                            "A"
                        ]
                    },
                    "h": 4,
                    "w": 10,
                    "x": 0,
                    "y": 4,
                    "uid": "H"
                },
                {
                    "component": "obsSets",
                    "h": 4,
                    "w": 2,
                    "x": 4,
                    "y": 0,
                    "uid": "F"
                },
                {
                    "component": "obsSetSizes",
                    "x": 6,
                    "y": 0,
                    "w": 3,
                    "h": 4
                }
            ]
        }
        return _conf

    def get_one_task_config(self, task):
        _id = task.id
        _conf = {
            "version": "1.0.16",
            "name": "Cluster Matrix Heatmap",
            "description": "Heatmap visualization of cluster data from AnnData object",
            "datasets": [
                {
                    "uid": "global_clq",
                    "name": "Cluster Data",
                    "files": [
                        {
                            "fileType": "obsFeatureMatrix.anndata.zarr",
                            "url": f"{self.base_url}tasks/clq_static/{_id}",
                            "coordinationValues": {
                                "obsType": "cell",
                                "featureType": "gene",
                                "featureValueType": "expression"
                            },
                            "options": {
                                "path": "layers/global_clq"
                            }
                        },
                    ],
                },
                {
                    "uid": "permute_test",
                    "name": "Permute Test Data",
                    "files": [
                        {
                            "fileType": "obsFeatureMatrix.anndata.zarr",
                            "url": f"{self.base_url}tasks/clq_static/{_id}",
                            "coordinationValues": {
                                "obsType": "cell",
                                "featureType": "gene",
                                "featureValueType": "expression"
                            },
                            "options": {
                                "path": "layers/permute_test"
                            }
                        },
                    ],
                }
            ],
            "initStrategy": "auto",
            "coordinationSpace": {
                "dataset": {
                    "global_clq": "global_clq",
                    "permute_test": "permute_test"
                },
                "embeddingType": {
                    "UMAP": "UMAP"
                },
                "obsSetHighlight": {
                    "A": None
                },
                "featureValueColormapRange": {
                    "A": [0, 1]
                },
                "embeddingObsSetLabelsVisible": {
                    "A": True
                },
                "obsSetSelection": {
                    "A": None
                },
                "obsSetColor": {
                    "A": None
                }
            },
            "layout": [
                {
                    "component": "heatmap",
                    "h": 4,
                    "w": 4,
                    "x": 0,
                    "y": 0,
                    "options": {
                        "showValueAnnotations": True,
                    },
                    "coordinationScopes": {
                        "featureValueColormapRange": "A",
                        "obsSetHighlight": "A",
                        "obsSetSelection": "A",
                        "obsSetColor": "A",
                        "obsSetLabelsVisible": "A",
                        "dataset": "global_clq",
                    },
                    "uid": "H2"
                },
                {
                    "component": "heatmap",
                    "h": 4,
                    "w": 4,
                    "x": 4,
                    "y": 0,
                    "options": {
                        "showValueAnnotations": True,
                    },
                    "coordinationScopes": {
                        "featureValueColormapRange": "A",
                        "obsSetHighlight": "A",
                        "obsSetSelection": "A",
                        "obsSetColor": "A",
                        "obsSetLabelsVisible": "A",
                        "dataset": "permute_test",
                    },
                    "uid": "H1"
                }
            ]
        }

        return _conf

    def get_spatial_scatter_config(self, task):
        _id = task.id
        _conf = {
            "version": "1.0.15",
            "name": "feature_extraction_config",
            "description": "Vitessce setup for feature extraction",
            "datasets": [
                {
                    "uid": "B",
                    "name": "zarr",
                    "files": [
                        {
                            "fileType": "obsEmbedding.anndata.zarr",
                            "url": f"{self.base_url}tasks/clq_static/{_id}",
                            "coordinationValues": {
                                "obsType": "cell",
                                "embeddingType": "spatial"
                            },
                            "options": {
                                "path": "obsm/spatial"
                            }
                        },
                        {
                            "fileType": "obsEmbedding.anndata.zarr",
                            "url": f"{self.base_url}tasks/clq_static/{_id}",
                            "coordinationValues": {
                                "obsType": "cell",
                                "embeddingType": "UMAP"
                            },
                            "options": {
                                "path": "obsm/X_umap"
                            }
                        },
                        {
                            "fileType": "obsSets.anndata.zarr",
                            "url": f"{self.base_url}tasks/clq_static/{_id}",
                            "coordinationValues": {
                                "obsType": "cell"
                            },
                            "options": [

                                {
                                    "name": "Niche Analysis",
                                    "path": "obs/niche"
                                },
                                {
                                    "name": "Leiden Analysis",
                                    "path": "obs/leiden"
                                }
                            ]
                        },
                        {
                            "fileType": "obsFeatureMatrix.anndata.zarr",
                            "url": f"{self.base_url}tasks/clq_static/{_id}",
                            "coordinationValues": {
                                "obsType": "cell",
                                "featureType": "gene",
                                "featureValueType": "expression"
                            },
                            "options": {
                                "path": "X"
                            }
                        }
                    ]
                }
            ],
            "initStrategy": "auto",
            "coordinationSpace": {
                "dataset": {
                    "B": "zarr"
                },
                "featureValueColormapRange": {
                    "B": [
                        0,
                        0.1
                    ]
                },
                "embeddingObsSetLabelsVisible": {
                    "B": True
                },
                "obsSetSelection": {
                    "B": None
                },
                "obsSetColor": {
                    "B": None
                },
                "embeddingType": {
                    "SPATIAL": "spatial",
                    "UMAP": "UMAP"
                },
                "embeddingZoom": {
                    "B": None
                },
                "embeddingTargetX": {
                    "B": None
                },
                "embeddingTargetY": {
                    "B": None
                },
                "embeddingObsSetLabelsVisible": {
                    "B": True
                },
                "obsType": {
                    "B": "cell"
                },
                "featureType": {
                    "B": "gene"
                },
                "featureValueType": {
                    "B": "expression"
                }

            },
            "layout": [

                {
                    "component": "scatterplot",
                    "coordinationScopes": {
                        "embeddingType": "SPATIAL",
                        "obsSetColor": "B",
                        "obsSetSelection": "B",
                        "obsColorEncoding": "B"
                    },
                    "h": 4,
                    "w": 6,
                    "x": 0,
                    "y": 0,
                    "options": {
                        "obsColorEncoding": "categorical"
                    },
                    "uid": "scatterplot_B"
                },
                {
                    "component": "scatterplot",
                    "coordinationScopes": {
                        "embeddingType": "UMAP",
                        "obsSetColor": "B",
                        "obsSetSelection": "B",
                        "obsColorEncoding": "B"
                    },
                    "h": 4,
                    "w": 6,
                    "x": 0,
                    "y": 6,
                    "options": {
                        "obsColorEncoding": "categorical"
                    },
                    "uid": "scatterplot_C"
                },
                {
                    "component": "obsSets",
                    "coordinationScopes": {
                        "obsSetSelection": "B",
                        "obsSetColor": "B"
                    },
                    "h": 4,
                    "w": 3,
                    "x": 6,
                    "y": 0,
                    "uid": "obsSets_B"
                }
            ]
        }
        return _conf

    @namespace.doc("tasks/vitessceconfig")
    @namespace.response(404, "Task not found", responses.error_response)
    @namespace.response(401, "Unauthorized", responses.error_response)
    def get(self, _id):

        task = TaskService.select(_id)
        if task is None:
            return {"success": False, "message": "task not found", "data": {}}, 200
        if task.name == "feature_extraction":
            # return self.get_feature_extraction_config(task)
            # return jsonify(self.get_one_task_config(task))
            return jsonify(self.get_combined_config(task))

        if task.name == "phenograph_cluster":
            return jsonify(self.get_phenograph_config(task))
        if task.name == "Cluster ST data":
            return jsonify(self.get_cluster_config(task))
        if task.name == "clq_anndata":
            return jsonify(self.get_one_task_config(task))
        if task.name == "niche_analysis":
            return jsonify(self.get_spatial_scatter_config(task))

    @namespace.response(404, "Task not found", responses.error_response)
    @namespace.response(401, "Unauthorized", responses.error_response)
    def delete(self, _id):

        task = TaskService.select(_id)
        if not task:
            return {"success": False, "message": "task not found", "data": {}}, 200

        deleted = delete_zarr_archive(task.to_json())
        if deleted:
            return {"success": True, "message": "data deleted", "data": {}}, 200
        else:
            return {"success": False, "message": "data does not exist", "data": {}}, 200

    @namespace.response(404, "Task not found", responses.error_response)
    @namespace.response(401, "Unauthorized", responses.error_response)
    def post(self, _id):

        task = TaskService.select(_id)
        if task is None:
            return {"success": False, "message": "task not found", "data": {}}, 200

        status = create_zarr_archive(task.to_json())
        if status == ZarrStatus.complete:
            return {"success": True, "message": "data created", "data": {}}, 200
        elif status == ZarrStatus.started:
            return {"success": True, "message": "data creation in progress", "data": {}}, 200
        else:
            return {"success": False, "message": "data creation failed", "data": {}}, 200


@namespace.route("/static/image/<_id>/<path:filepath>")
@namespace.param("_id", "task id")
class ImageStaticGet(Resource):
    @namespace.doc("tasks/vitessceimage")
    @namespace.response(404, "Task not found", responses.error_response)
    @namespace.response(401, "Unauthorized", responses.error_response)
    def get(self, _id, filepath):
        filepath = strip_no_cache(filepath)
        task = TaskService.select(_id)
        if not task:
            return {"success": False, "message": "task not found", "data": {}}, 200

        task_json = task.to_json()
        image_path = f'{os.getenv("DATA_STORAGE")}/originals/{task_json["omeroId"]}/image.tiff'
        if not os.path.exists(image_path):
            return {'success': False, 'message': 'Image not found'}, 404

        with tifffile.TiffFile(image_path) as tif:
            image_data = tif.asarray()
            # image_data = image_data.transpose(1, 2, 0)
            ome_metadata = tif.ome_metadata

        result_path = task_json.get("result")
        absolute_path = Utils.getAbsoluteRelative(result_path, absolute=True)
        zarr_image_dir = f'{os.path.dirname(absolute_path)}/static/image.h5ad.zarr'

        if os.path.exists(zarr_image_dir):
            return send_from_directory(zarr_image_dir, filepath)

        os.makedirs(zarr_image_dir, exist_ok=True)

        store = zarr.DirectoryStore(zarr_image_dir)
        root = zarr.group(store=store, overwrite=True)

        image_zarr = root.create_dataset("0", shape=image_data.shape, dtype=image_data.dtype)
        image_zarr[:] = image_data

        image_zarr.attrs['multiscales'] = [
            {
                "version": "0.1",
                "datasets": [{"path": "0"}],
                "type": "image",
                "metadata": {
                    "omero": ome_metadata
                }
            }
        ]

        if os.path.exists(os.path.join(zarr_image_dir, filepath)):
            return send_from_directory(zarr_image_dir, filepath)
        else:
            return {"success": False, "message": "result not found", "data": {}}, 200
