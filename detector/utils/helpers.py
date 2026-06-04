def calculate_centroid(bbox):
    """Calculates centroid of a bounding box [x1, y1, x2, y2]"""
    x1, y1, x2, y2 = bbox
    cx = int((x1 + x2) / 2)
    cy = int((y1 + y2) / 2)
    return cx, cy

def get_bottom_center(bbox):
    """Gets the bottom-center point of a bounding box for grounded spatial location"""
    x1, y1, x2, y2 = bbox
    cx = int((x1 + x2) / 2)
    cy = int(y2)
    return cx, cy

def calculate_iou(boxA, boxB):
    """Calculates Intersection over Union (IoU) of two bounding boxes"""
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])

    interArea = max(0, xB - xA + 1) * max(0, yB - yA + 1)
    boxAArea = (boxA[2] - boxA[0] + 1) * (boxA[3] - boxA[1] + 1)
    boxBArea = (boxB[2] - boxB[0] + 1) * (boxB[3] - boxB[1] + 1)

    iou = interArea / float(boxAArea + boxBArea - interArea)
    return iou
