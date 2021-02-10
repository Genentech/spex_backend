import omero
from omero.gateway import BlitzGateway
from os import getenv
# from io import BytesIO
# try:
#     from PIL import Image
# except ImportError:
#     import Image
# import tempfile


def connect(username, password):
    hostname = getenv('OMERO_HOST')
    print(hostname)

    conn = BlitzGateway(username, password, host=hostname, secure=True)
    conn.connect()
    conn.c.enableKeepAlive(60)
    return conn


def disconnect(conn):
    conn.close()


def print_obj(obj, indent=0):
    res = """%s%s:%s  Name:"%s" (owner=%s)""" % (
        " " * indent,
        obj.OMERO_CLASS,
        obj.getId(),
        obj.getName(),
        obj.getOwnerOmeName())

    print(res)
    return res


def getData():
    print("0")
    conn = connect("localhost", "root", "omero")
    # my_exp_id = conn.getUser().getId()
    # default_group_id = conn.getEventContext().groupId
    # for project in conn.getObjects("Project", opts={'owner': my_exp_id,
    #                                                 'group': default_group_id,
    #                                                 'order_by': 'lower(obj.name)',
    #                                                 'limit': 5, 'offset': 0}):
    #     print_obj(project)
    #     # We can get Datasets with listChildren, since we have the Project already.
    #     # Or conn.getObjects("Dataset", opts={'project', id}) if we have Project ID
    #     for dataset in project.listChildren():
    # print_obj(dataset, 2)
    image = conn.getObject("Image", "52")

    try:
        # for imageF in dataset.listChildren():
        id = print_obj(image, 4)
        print(id)
        fileset = image.getFileset()       # will be None for pre-FS images
        fs_id = fileset.getId()
        fileset = conn.getObject("Fileset", fs_id)

        for fs_image in fileset.copyImages():
            print(fs_image.getId(), fs_image.getName())
        for orig_file in fileset.listFiles():
            name = orig_file.getName()
            path = orig_file.getPath()
            print(path, name)
            print("Downloading...", name)
            dir = ".\\tmp\\"
            name = dir + name
            with open(name, "wb") as f:
                for chunk in orig_file.getFileInChunks(buf=2621440):
                    f.write(chunk)
        # image = conn.getObject("Image", id)
        disconnect(conn)
    except AttributeError as ae:
        disconnect(conn)
        raise ae


# getData()

# conn = connect("localhost", "root", "omero")
# disconnect(conn)


def archived_files(iid=None, conn=None, **kwargs):
    iid = 52
    conn = connect("localhost", "root", "omero")
    """
    Downloads the archived file(s) as a single file or as a zip (if more than
    one file)
    """

    imgIds = [iid]

    images = list()
    wells = list()
    if imgIds:
        images = list(conn.getObjects("Image", imgIds))

    if len(images) == 0:
        message = (
            "Cannot download archived file because Images not "
            "found (ids: %s)" % (imgIds)
        )
        return message

    # Test permissions on images and weels
    for ob in wells:
        if hasattr(ob, "canDownload"):
            return "HttpResponseNotFound"

    for ob in images:
        well = None
        try:
            well = ob.getParent().getParent()
        except Exception:
            if hasattr(ob, "canDownload"):
                if not ob.canDownload():
                    return "HttpResponseNotFound"
        else:
            if well and isinstance(well, omero.gateway.WellWrapper):
                if hasattr(well, "canDownload"):
                    if not well.canDownload():
                        return "HttpResponseNotFound()"

    # make list of all files, removing duplicates
    fileMap = {}
    for image in images:
        for f in image.getImportedImageFiles():
            fileMap[f.getId()] = f
    files = list(fileMap.values())

    if len(files) == 0:
        message = (
            "Tried downloading archived files from image with no" " files archived."
        )
        return message

    if len(files) == 1:
        orig_file = files[0]
        rsp = orig_file.getFileInChunks(buf=1048576)
        # rsp['conn'] = conn
        # rsp["Content-Length"] = orig_file.getSize()
        # ',' in name causes duplicate headers
        fname = orig_file.getName().replace(" ", "_").replace(",", ".")
        # rsp["Content-Disposition"] = "attachment; filename=%s" % (fname)
        print(fname)
    # rsp["Content-Type"] = "application/force-download"
    rsp.save("/tmp" + fname)


# archived_files()
