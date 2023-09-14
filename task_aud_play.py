# -*- coding: utf-8 -*-
import numpy as np
import threading
import pyaudio
import av
import time

#音频播放类，从queue中接收音频码流，解码并进行播放
class Audio_play(threading.Thread):  # 继承父类threading.Thread
    def __init__(self, threadID, name, audio_queue):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.audio_queue = audio_queue

    def run(self):  # 把要执行的代码写到run函数里面 线程在创建后会直接运行run函数
        print
        "Starting " + self.name
        #fo = open("foo.pcm", "wb+")
        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paInt16,
                        channels=1,
                        rate=32000,
                        output=True)
        audio_queue = self.audio_queue
        aud_convert = av.audio.resampler.AudioResampler(format='s16', layout='mono', rate=32000)

        pts = 0
        # last_pts = 0
        last_show_time = 0
        sleep_time = 0
        time_need2show = 0.002
        last_pts_delta = 0
        while True:
            if not audio_queue.empty():
                # print("audio get")
                packet = audio_queue.get()
            else:
                time.sleep(0.030)
                continue

            for frame in packet.decode():
                frame1 = aud_convert.resample(frame)[0]
                pts_delta = frame1.samples * 90000 / frame1.rate
                # frame.pts = pts
                # pts += pts_delta
                array = frame1.to_ndarray()
                pcm = (
                    np
                        .frombuffer(array, np.int16)
                )
                pts_delta_time = last_pts_delta / 90000
                show_time = time.time()
                # print(show_time, last_show_time, pts_delta_time, time_need2show)
                if show_time < last_show_time + pts_delta_time - time_need2show:
                    sleep_time = last_show_time + pts_delta_time - show_time - time_need2show
                    if sleep_time > 0.01:
                        sleep_time = 0.01
                    # print(sleep_time)
                    # time.sleep(sleep_time)
                time_start = time.time()
                last_pts_delta = pts_delta
                stream.write(pcm.tobytes())
                time_need2show = time.time() - time_start
                # last_pts = frame.pts
                sleep_time = 0
                last_show_time = time.time()

        # 停止数据流
        stream.stop_stream()
        stream.close()

        # 关闭 PyAudio
        p.terminate()