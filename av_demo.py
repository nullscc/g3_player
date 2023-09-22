# -*- coding: utf-8 -*-
import numpy as np
import time
import threading
import queue
from task_ts_stream import tsk_ts_stream
from task_aud_play import Audio_play
import cv2

class Video_play():
    def __init__(self, threadID, name, video_queue, gaze_queue):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.queue = video_queue
        self.gaze_queue = gaze_queue

    def get_frame_with_gaze2d(self, frame, gaze_data):
        if "gaze2d" in gaze_data:
            gaze2d = gaze_data["gaze2d"]
            # print(f"Gaze2d: {gaze2d[0]:9.4f},{gaze2d[1]:9.4f}")

            # Convert rational (x,y) to pixel location (x,y)
            h, w = frame.shape[:2]
            fix = (int(gaze2d[0] * w), int(gaze2d[1] * h))

            # Draw gaze
            frame = cv2.circle(frame, fix, 10, (0, 0, 255), 3)
        return frame
    def run(self):
        queue = self.queue
        gaze_queue = self.gaze_queue

        last_pts = 0
        pts_delta = 0
        last_show_time = 0
        sleep_time = 0
        time_need2show = 0
        last_gaze_packet = (0, {})
        while True:
            if not queue.empty():
                packet = queue.get()
            else:
                time.sleep(0.01)
                continue

            for VideoFrame in packet.decode():

                if VideoFrame.pts == None:
                    continue

                gaze_packet = None
                if not gaze_queue.empty():
                    while not gaze_queue.empty() and gaze_queue.queue[0] and gaze_queue.queue[0][0] and gaze_queue.queue[0][0] <= packet.pts:
                        gaze_packet = gaze_queue.get()

                show_width = VideoFrame.width
                show_height = VideoFrame.height
                frame_show = VideoFrame
                # #convert to rgb
                img_array = frame_show.to_rgb().to_ndarray()[:, :, ::-1]
                in_frame = img_array
    
                # in_frame = (
                #     np
                #         .frombuffer(img_array, np.uint8)
                #         .reshape([show_height, show_width, 3])
                # )

                pts_delta = VideoFrame.pts - last_pts
                pts_delta = pts_delta/90000.0

                if (not gaze_packet) or (not gaze_packet[1]):
                    gaze_packet = last_gaze_packet

                if gaze_packet and gaze_packet[1]:
                    gaze_data = gaze_packet[1]
                    in_frame = self.get_frame_with_gaze2d(in_frame, gaze_data)
                    last_gaze_packet = gaze_packet
                show_time = time.time()
                if show_time <= last_show_time + pts_delta - time_need2show:
                    sleep_time = last_show_time + pts_delta - show_time - time_need2show
                    if sleep_time > 0.1:
                        sleep_time = 0.1
                    #缓冲区超过25帧，则2倍速播放
                    # if queue.qsize() > 25:
                    #     sleep_time = sleep_time/2
                    # elif queue.qsize() < 5:
                    #     sleep_time += 0.003
                    if sleep_time > 0:
                        time.sleep(sleep_time)

                    time_start = time.time()
                    cv2.imshow("Video", in_frame)  # type: ignore
                    cv2.waitKey(1)  # type: ignore
                    time_need2show = time.time() - time_start
                elif (show_time - last_show_time - pts_delta + time_need2show) > 0.2:
                    pass
                else:
                    time_start = time.time()
                    cv2.imshow("Video", in_frame)  # type: ignore
                    cv2.waitKey(1)  # type: ignore
                    time_need2show = time.time() - time_start
                last_pts = VideoFrame.pts
                time_now = time.time()
                sleep_time = 0
                last_show_time = time_now


if __name__ == '__main__':
    video_queue = queue.Queue(1000000)
    audio_queue = queue.Queue(1000000)
    gaze_queue = queue.Queue(1000000)

    # thread_vid_play = Video_play(2, "Video-dec", video_queue)
    thread_aud_play = Audio_play(1, "Audio-dec", audio_queue)
    # thread_stream = tsk_ts_stream(1, "parse-stream", "rtsp://123.249.4.175:8554/live/all", video_queue, audio_queue, gaze_queue)
    thread_stream = tsk_ts_stream(1, "parse-stream", "violin.mp4", video_queue, audio_queue, gaze_queue)
    
    thread_aud_play.start()
    thread_stream.start()
    video_play = Video_play(2, "Video-dec", video_queue, gaze_queue)
    video_play.run()
    thread_stream.join()
