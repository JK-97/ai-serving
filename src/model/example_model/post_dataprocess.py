import numpy as np


score_threshold = 0.35
iou_threshold = 0.5


def post_dataprocess(original_image, prediction_dict, classes, extra_data = []):
    #classes = read()
    num_classes = len(classes)
    pred_mbbox = prediction_dict[1]
    pred_lbbox = prediction_dict[2]
    org_h, org_w, _ = original_image.shape 

    pred_bbox = np.concatenate(
        [np.reshape(pred_mbbox, (-1, 5 + num_classes)),
         np.reshape(pred_lbbox, (-1, 5 + num_classes))], axis=0)

    valid_scale = (0, np.inf)
    bboxes = convert_pred(pred_bbox, 544, (org_h, org_w), valid_scale)
    bboxes = nms(bboxes, score_threshold, iou_threshold, method='nms')

    result = []
    for i, bbox in enumerate(bboxes):
        class_ind = int(bbox[5])
        clss = classes[class_ind].lower()
        coor = bbox[:4]
        for s in range(len(coor)):
            coor[s]=int(coor[s])
        score = float(bbox[4])
        temp = [str(clss),str(score),str(int(coor[0])),str(int(coor[1])),str(int(coor[2])),str(int(coor[3]))]
        result.append(temp)
    return result


def iou_calc1(boxes1, boxes2):

    boxes1 = np.array(boxes1)
    boxes2 = np.array(boxes2)

    boxes1_area = (boxes1[..., 2] - boxes1[..., 0]) * (boxes1[..., 3] - boxes1[..., 1])
    boxes2_area = (boxes2[..., 2] - boxes2[..., 0]) * (boxes2[..., 3] - boxes2[..., 1])

    left_up = np.maximum(boxes1[..., :2], boxes2[..., :2])
    right_down = np.minimum(boxes1[..., 2:], boxes2[..., 2:])

    inter_section = np.maximum(right_down - left_up, 0.0)
    inter_area = inter_section[..., 0] * inter_section[..., 1]
    union_area = boxes1_area + boxes2_area - inter_area
    IOU = 1.0 * inter_area / union_area
    return IOU


def nms(bboxes, score_threshold, iou_threshold, sigma=0.3, method='nms'):

    classes_in_img = list(set(bboxes[:, 5]))
    best_bboxes = []

    for cls in classes_in_img:
        cls_mask = (bboxes[:, 5] == cls)
        cls_bboxes = bboxes[cls_mask]
        while len(cls_bboxes) > 0:
            max_ind = np.argmax(cls_bboxes[:, 4])
            best_bbox = cls_bboxes[max_ind]
            best_bboxes.append(best_bbox)
            cls_bboxes = np.concatenate([cls_bboxes[: max_ind], cls_bboxes[max_ind + 1:]])
            iou = iou_calc1(best_bbox[np.newaxis, :4], cls_bboxes[:, :4])
            assert method in ['nms', 'soft-nms']
            weight = np.ones((len(iou),), dtype=np.float32)
            if method == 'nms':
                iou_mask = iou > iou_threshold
                weight[iou_mask] = 0.0
            if method == 'soft-nms':
                weight = np.exp(-(1.0 * iou ** 2 / sigma))
            cls_bboxes[:, 4] = cls_bboxes[:, 4] * weight
            score_mask = cls_bboxes[:, 4] > score_threshold
            cls_bboxes = cls_bboxes[score_mask]
    return best_bboxes


def convert_pred(pred_bbox, test_input_size, org_img_shape, valid_scale):
    pred_bbox = np.array(pred_bbox)

    pred_coor = pred_bbox[:, 0:4]
    pred_conf = pred_bbox[:, 4]
    pred_prob = pred_bbox[:, 5:]

    org_h, org_w = org_img_shape
    resize_ratio = min(1.0 * test_input_size / org_w, 1.0 * test_input_size / org_h)
    dw = (test_input_size - resize_ratio * org_w) / 2
    dh = (test_input_size - resize_ratio * org_h) / 2
    pred_coor[:, 0::2] = 1.0 * (pred_coor[:, 0::2] - dw) / resize_ratio
    pred_coor[:, 1::2] = 1.0 * (pred_coor[:, 1::2] - dh) / resize_ratio

    pred_coor = np.concatenate([np.maximum(pred_coor[:, :2], [0, 0]),
                                np.minimum(pred_coor[:, 2:], [org_w - 1, org_h - 1])], axis=-1)

    invalid_mask = np.logical_or((pred_coor[:, 0] > pred_coor[:, 2]), (pred_coor[:, 1] > pred_coor[:, 3]))
    pred_coor[invalid_mask] = 0

    bboxes_scale = np.sqrt(np.multiply.reduce(pred_coor[:, 2:4] - pred_coor[:, 0:2], axis=-1))
    scale_mask = np.logical_and((valid_scale[0] < bboxes_scale), (bboxes_scale < valid_scale[1]))


    classes = np.argmax(pred_prob, axis=-1)
    scores = pred_conf * pred_prob[np.arange(len(pred_coor)), classes]
    score_mask = scores > score_threshold

    mask = np.logical_and(scale_mask, score_mask)

    coors = pred_coor[mask]
    scores = scores[mask]
    classes = classes[mask]

    bboxes = np.concatenate([coors, scores[:, np.newaxis], classes[:, np.newaxis]], axis=-1)

    return bboxes

