# -*- coding: utf-8 -*-
import numpy as np
import time
import threading
import queue
from task_ts_stream import tsk_ts_stream
from task_aud_play import Audio_play
import cv2

class Video_play():
    def __init__(self, threadID, name, video_queue):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.queue = video_queue

    def run(self):
        queue = self.queue

        last_pts = 0
        pts_delta = 0
        last_show_time = 0
        sleep_time = 0
        while True:
            if not queue.empty():
                packet = queue.get()
            else:
                time.sleep(0.01)
                continue

            for VideoFrame in packet.decode():

                if VideoFrame.pts == None:
                    continue
                # if VideoFrame.width != 1920:
                #     continue
                show_width = VideoFrame.width
                show_height = VideoFrame.height
                frame_show = VideoFrame

                img_array = frame_show.to_ndarray(format='rgb24')

                in_frame = (
                    np
                        .frombuffer(img_array, np.uint8)
                        .reshape([show_height, show_width, 3])
                )

                pts_delta = VideoFrame.pts - last_pts
                pts_delta = pts_delta/90000.0

                show_time = time.time()

                if show_time < last_show_time + pts_delta - 0.002:
                    sleep_time = last_show_time + pts_delta - show_time - 0.002
                    if sleep_time > 0.1:
                        sleep_time = 0.1
                    #缓冲区超过25帧，则2倍速播放
                    if queue.qsize() > 25:
                        sleep_time = sleep_time/2
                    elif queue.qsize() < 5:
                        sleep_time += 0.003
                    time.sleep(sleep_time)

                cv2.imshow("Video", in_frame)  # type: ignore
                cv2.waitKey(1)  # type: ignore
                last_pts = VideoFrame.pts
                time_now = time.time()
                sleep_time = 0
                last_show_time = time_now


if __name__ == '__main__':
    video_queue = queue.Queue(1000000)
    audio_queue = queue.Queue(1000000)

    thread_vid_play = Video_play(2, "Video-dec", video_queue)
    thread_aud_play = Audio_play(1, "Audio-dec", audio_queue, 100)
    thread_stream = tsk_ts_stream(1, "parse-stream", "rtsp://123.249.4.175:8554/live/all", video_queue, audio_queue)
    # thread_stream = tsk_ts_stream(1, "parse-stream", "violin.mp4", video_queue, audio_queue)
    
    thread_aud_play.start()
    thread_stream.start()
    video_play = Video_play(2, "Video-dec", video_queue)
    video_play.run()
    thread_stream.join()
