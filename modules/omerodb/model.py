export JAVA_OPTS=-Xmx4G
omero import -d 4051 R2_PCNA.Her2.ER.CD45_BM-Her2N75-15_2017_08_11__2327.czi --debug WARN
from omero.gateway import BlitzGateway
from io import BytesIO
try:
    from PIL import Image
except ImportError:
    import Image


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
                for imageF in dataset.listChildren():
                    id = print_obj(imageF, 4)
                    image = conn.getObject("Image", id)
                    print(" X:", image.getSizeX())
                    print(" Y:", image.getSizeY())
                    print(" Z:", image.getSizeZ())
                    print(" C:", image.getSizeC())
                    print(" T:", image.getSizeT())

                    # img_data = image.getThumbnail()  # R endering settings from OMERO.web
                    # rendered_image = Image.open(BytesIO(img_data))

                    # rendered_image.save('tmp/my_image.png')  # Save image to current folder

                    z = image.getSizeZ() / 2
                    t = 0
                    image.setColorRenderingModel()
                    channels = [1, 2, 3]
                    colorList = ['F00', None, 'FFFF00']  # do not change colour of 2nd channel
                    image.setActiveChannels(channels, colors=colorList)
                    # max intensity projection 'intmean' for mean-intensity
                    image.setProjection('intmax')
                    # renderedImage = image.renderImage(z=None, t=None, compression=0.5)  # z and t are ignored for projections
                    # renderedImage.show()
                    # renderedImage.save("all_channels.jpg")

            except AttributeError as ae:
                disconnect(conn)
                raise ae
    disconnect(conn)


getData()
