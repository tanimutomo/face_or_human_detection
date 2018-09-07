import cv2
import numpy as np

infile = '../data/video/inter10_night.avi'
# video = []
cap = cv2.VideoCapture(infile)
W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
fps = cap.get(cv2.CAP_PROP_FPS)
print('[INFO] total frame: {}, fps: {}, width: {}, height: {}'.format(count, fps, W, H))
count = 1

while(cap.isOpened()):
    ret, frame = cap.read()
    print('count: {}'.format(count))
    if ret:
        # cv2.imshow('frame', frame)
        # video.append(frame)
        if count >= 1020 and count <= 1170:
            cv2.imwrite('../data/video/night_frames/in_{}.png'.format(count), frame)
        # if cv2.waitKey(1) & 0xFF == ord('q'):
        #     break
    else:
        break
    count += 1
cap.release()

# outfile = '{}ex_{}'.format(infile_dir, infile)
# fps = 20.0
# codecs = 'H264'

# print(np.array([video]).shape)
# ret, frames, height, width, ch = np.array([video]).shape
# 
# fourcc = cv2.VideoWriter_fourcc(*codecs)
# writer = cv2.VideoWriter(outfile, fourcc, fps, (width, height))
# for i in range(frames):
#     writer.write(video[i])
# writer.release()
