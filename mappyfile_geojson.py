from collections import OrderedDict

__version__ = "0.1.0"


def explode(coords):
    """
    From https://gist.github.com/sgillies/3975665
    Explode a GeoJSON geometry's coordinates object and yield
    coordinate tuples. As long as the input is conforming,
    the type of the geometry doesn't matter.
    """
    for e in coords:
        if isinstance(e, (float, int, long)):
            yield coords
            break
        else:
            for f in explode(e):
                yield f


def bbox(f):
    x, y = zip(*list(explode(f.geometry.coordinates)))
    return min(x), min(y), max(x), max(y)


def get_extent(features, buffer=0):
    extents = map(bbox, features)
    full_extent = (min(zip(*extents)[0]) - buffer,
                   min(zip(*extents)[1]) - buffer,
                   max(zip(*extents)[2]) + buffer,
                   max(zip(*extents)[3]) + buffer)

    return list(full_extent)


def create_inline_feature(feat):

    geom = feat.geometry
    f = {"__type__": "feature"}

    coords = geom.coordinates

    if geom.type == "Point":
        coords = [coords]  # put coords in an outer list

    f["points"] = coords
    # note items use semicolons and not commas as used elsewhere
    f["items"] = ";".join(map(str, feat.properties.values()))
    return f


def get_features(gj):
    # loop through each feature in a feature collection

    if gj.type == "FeatureCollection":
        features = gj.features
    elif gj.type == "Feature":
        features = [gj]

    return features


def create_layer(features, bbox):

    first_feature = features[0]
    geom_type = first_feature.geometry.type

    mapfile_features = map(create_inline_feature, features)

    layer = OrderedDict()
    layer["__type__"] = "layer"
    layer["extent"] = bbox
    layer["status"] = "on"

    if geom_type == "LineString":
        layer_type = "line"
    elif geom_type == "Point":
        layer_type = "point"
    elif geom_type == "Polygon":
        layer_type = "polygon"
    else:
        raise NotImplemented("The geometry type {} is not yet implemented".format(geom_type))

    # layer type must be set before adding inline features!!

    layer["type"] = layer_type
    props = first_feature.properties.keys()
    layer["processing"] = ["ITEMS={}".format(",".join(props))]
    layer["features"] = mapfile_features
    return layer


def convert(gj, extent_buffer=0):
    features = get_features(gj)
    bbox = get_extent(features, buffer=extent_buffer)
    layer = create_layer(features, bbox)
    return layer