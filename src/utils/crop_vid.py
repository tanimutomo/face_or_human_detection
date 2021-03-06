import os
import cv2
import numpy as np

from util import video_writer


def crop_vid(infile, outname, out_fps=None, start=None, end=None,
             resize_factor=None):
    cap = cv2.VideoCapture(infile)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    print('[INFO] total frame: {}, fps: {}, width: {}, height: {}'.format(count, fps, w, h))

    if not out_fps:
        out_fps = fps
    if resize_factor:
        new_h = int(h / resize_factor)
        new_w = int(w / resize_factor)

    writer = video_writer(infile, outname, out_fps, new_w, new_h)

    count = 1
    while(cap.isOpened()):
        ret, frame = cap.read()
        if not start or count >= start:
            print('count: {}'.format(count))
            if ret:
                if resize_factor:
                    frame = cv2.resize(frame, (new_w, new_h))
                writer.write(frame)
            else:
                break
                raise RuntimeError('Cannot read the video frame')
        if end and count > end:
            break
        count += 1
    cap.release()
    writer.release()

if __name__ == '__main__':
    infile = '/Users/tanimu/projects/pytorch-yolo-v3/videos/ex01.avi'
    crop_vid(infile, '_short', resize_factor=2)

