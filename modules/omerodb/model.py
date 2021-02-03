from omero.gateway import BlitzGateway
from io import BytesIO


def connect(hostname, username, password):
    """
    Connect to an OMERO server
    :param hostname: Host name
    :param username: User
    :param password: Password
    :return: Connected BlitzGateway
    """
    conn = BlitzGateway(username, password,
                        host=hostname, secure=True)
    conn.connect()
    conn.c.enableKeepAlive(60)
    return conn


def disconnect(conn):
    """
    Disconnect from an OMERO server
    :param conn: The BlitzGateway
    """
    conn.close()


def print_obj(obj, indent=0):
    """
    Helper method to display info about OMERO objects.
    Not all objects will have a "name" or owner field.
    """
    print("""%s%s:%s  Name:"%s" (owner=%s)""" % (
        " " * indent,
        obj.OMERO_CLASS,
        obj.getId(),
        obj.getName(),
        obj.getOwnerOmeName()))
    return obj.getId()


def getData():
    print("0")
    conn = connect("localhost", "root", "omero")
    my_exp_id = conn.getUser().getId()
    default_group_id = conn.getEventContext().groupId
    for project in conn.getObjects("Project", opts={'owner': my_exp_id,
                                                    'group': default_group_id,
                                                    'order_by': 'lower(obj.name)',
                                                    'limit': 5, 'offset': 0}):
        print_obj(project)
        # We can get Datasets with listChildren, since we have the Project already.
        # Or conn.getObjects("Dataset", opts={'project', id}) if we have Project ID
        for dataset in project.listChildren():
            print_obj(dataset, 2)
            try:
                for image in dataset.listChildren():
                    id = print_obj(image, 4)
                    imageF = conn.getObject("Image", id)
                    img_data = imageF.getThumbnail()

                    rendered_thumb = imageF.open(BytesIO(img_data))
                    # renderedThumb.show()           # shows a pop-up
                    rendered_thumb.save("thumbnail.jpg")
            except AttributeError as ae:
                disconnect(conn)
                raise ae
    disconnect(conn)


getData()
