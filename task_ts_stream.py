# -*- coding: utf-8 -*-
import av
import threading
import json

#从网络上接收TS流，分离出音视频数据，发给对应的解码线程
class tsk_ts_stream(threading.Thread):  # 继承父类threading.Thread
    def __init__(self, threadID, name, stream_name, video_queue, audio_queue):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.stream_name = stream_name
        self.video_queue = video_queue
        self.audio_queue = audio_queue
        print("thread " + str(stream_name) + "  started")

    def run(self):  # 把要执行的代码写到run函数里面 线程在创建后会直接运行run函数, options = ['-i','h265_aac.sdp']
        if self.stream_name.startswith("rtsp"):
            container = av.open(file = self.stream_name, mode = 'r', format = "rtsp",options={'rtsp_transport':'tcp'})
        else:
            container = av.open(file = self.stream_name, mode = 'r')
        video_queue = self.video_queue
        audio_queue = self.audio_queue
        while True:
            for packet in container.demux():
                # print(packet.pts, packet.dts)
                if packet.stream.type == 'video':
                    if packet.stream_index == 0:
                        video_queue.put(packet)
                elif packet.stream.type == 'audio':
                # else:
                    #continue
                    audio_queue.put(packet)
                    #print(packet.buffer_size)
                   # print(packet.to_bytes())
                    #print(packet.stream.type)
                else:
                    if packet.stream_index != 5:
                        print(f"stream_index: {packet.stream_index}", packet.to_bytes())
                    pass
                    # import pdb
                    # pdb.set_trace()
                    # print(packet.stream.type)



