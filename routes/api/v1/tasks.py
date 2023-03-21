import base64
import json
import tempfile
import os
import pickle
import numpy as np
import io

import spex_common.services.Task as TaskService
import spex_common.services.Job as JobService
import spex_common.services.Utils as Utils
from spex_common.modules.logging import get_logger
from flask_restx import Namespace, Resource
from flask import request, send_file, make_response
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
from anndata import AnnData
from scipy.stats import zscore

class VisType(str, Enum):
    scatter = "scatter"
    boxplot = "boxplot"
    heatmap = "heatmap"
    barplot = "barplot"


logger = get_logger("spex.backend")

namespace = Namespace("Tasks", description="Tasks CRUD operations")

namespace.add_model(tasks.tasks_model.name, tasks.tasks_model)
namespace.add_model(tasks.task_post_model.name, tasks.task_post_model)
namespace.add_model(responses.response.name, responses.response)
namespace.add_model(tasks.a_tasks_response.name, tasks.a_tasks_response)
namespace.add_model(responses.error_response.name, responses.error_response)
namespace.add_model(tasks.list_tasks_response.name, tasks.list_tasks_response)
namespace.add_model(tasks.task_get_model.name, tasks.task_get_model)


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
    @namespace.doc("tasks/get_file", security="Bearer")
    @namespace.response(404, "Task not found", responses.error_response)
    @namespace.response(401, "Unauthorized", responses.error_response)
    # @namespace.marshal_with(tasks.a_tasks_response)
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
                    # data = json.dumps(data, cls=NumpyEncoder)
                    return {"success": True, "data": list(data.keys())}, 200

                data = data.get(key)

                fd, temp_file_name = tempfile.mkstemp()
                # fd.close()
                ext = ".csv"

                if isinstance(data, np.ndarray) and key == "labels":
                    im = create_resp_from_df(data, debug=False, _format='tiff', file=True)
                    im.save(temp_file_name, format=ext)

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
            coordinates = []
            df = data['dataframe']
            for k in range(0, len(df), 1):
                coordinates.append([df.loc[df.index[k], 'centroid-1'], df.loc[df.index[k], 'centroid-0']])

            celltype = df[['label']]
            celltype['label'] = celltype.label.astype('category')
            celltype = celltype.rename(columns={'label': 'Cell_ID'})
            expression_data = np.array(df[data["channel_list"][0].lower().replace('target:', '')])
            expression_data = expression_data.reshape(-1, 1)
            coordinates = np.asarray(coordinates)

            adata = AnnData(X=expression_data, obsm={"spatial": coordinates})
            adata.obs['Cell_ID'] = np.array(celltype['Cell_ID']).astype(str)
            adata.layers["zscored"] = np.apply_along_axis(zscore, axis=0, arr=expression_data)
            buffer = io.BytesIO()
            buffer.seek(0)

            return send_file(
                buffer,
                attachment_filename='file.h5ad',
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

    img_buf.seek(0)
    resp_data = img_buf.read()
    resp_data = base64.b64encode(resp_data)
    resp_data = resp_data.decode("utf-8")
    if file:
        return im

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
        pyplot.clf()
        plt.subplots(ncols=1, figsize=(5, 5))

        for k in request.args.keys():
            if k == "key":
                key = request.args.get(k)
            if k == "vis_name":
                vis_name = request.args.get(k)
            if k == "debug":
                if strtobool(request.args.get(k)):
                    debug = True

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

                cols = len(to_show_data["variable"].unique())
                # cols = 5
                fig, axs = plt.subplots(ncols=1, nrows=cols, figsize=(8, 4 * cols))
                fig.tight_layout()
                fig.subplots_adjust(top=0.95)
                index = 0

                for channel in to_show_data["variable"].unique():
                    # if index == 5:
                    #     continue

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

                    sns.scatterplot(
                        y=1, x=2, data=df, palette="Set3", hue=df["cluster"], ax=ax
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
            ax = sns.boxplot(y="variable", x="value", data=to_show_data, palette="Set3")
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
                to_show = np.delete(data, [0, 1, 2], axis=1)
                _, c = to_show.shape
                rows = [element for element in range(c)]
                rows.insert(0, rows.pop())

                to_show = to_show[:, rows]

                result = np.empty(shape=(0, c), dtype=to_show.dtype)

                clusters = np.unique(to_show[:, 0])
                for cluster in clusters:
                    df = to_show[(to_show[:, 0] == cluster)]
                    if len(df):
                        result = np.append(result, [np.average(df, axis=0)], axis=0)

                result = np.delete(result, [0], axis=1)

                fig, ax = plt.subplots(1, 1, figsize=(10, 5))
                fig.tight_layout()

                sns.heatmap(
                    result,
                    vmin=np.min(result[(result[:]) > 0]),
                    vmax=np.max(result),
                    xticklabels=channels_str,
                    cmap="rocket",
                    fmt="g",
                    ax=ax,
                )
                # ax.xaxis.set_tick_params(labelsize='small')
                ax.set(title=vis_name)

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
