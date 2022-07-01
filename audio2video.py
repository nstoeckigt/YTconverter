#!/bin/env python3

import os
import subprocess
import asyncio
from loguru import logger
import snoop
import tkinter as tk
from tkinter import filedialog, ttk
from tkinter.messagebox import askyesno, askquestion, showinfo, showwarning, showerror
from functools import partial
import ffmpy


class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("audio2YouTube Converter")
        self.resizable(False, False)
        self.geometry('560x340')
        self.option_add('*Dialog.msg.font', 'Helvetica 10')

        self._audio_label = tk.Label(self, text="INPUT:  Audio File:", anchor=tk.W)
        self._audio_label.place(x=12, y=10, width=130, height=22)
        self._audio_text = tk.Label(self, relief=tk.SUNKEN, anchor=tk.W)
        self._audio_text.place(x=152, y=8, width=360, height=26)
        self._audio_button = ttk.Button(self, text='...', command=partial(self._getFile, title="Select Audio File"))
        self._audio_button.place(x=520, y=8, width=28, height=26)

        self._image_label = tk.Label(self, text="INPUT:  Image File:", anchor=tk.W)
        self._image_label.place(x=12, y=44, width=130, height=22)
        self._image_text = tk.Label(self, relief=tk.SUNKEN, anchor=tk.W)
        self._image_text.place(x=152, y=42, width=360, height=26)
        self._image_button = ttk.Button(self, text='...', command=partial(self._getFile, title="Select Image File"))
        self._image_button.place(x=520, y=42, width=28, height=26)

        self._video_label = tk.Label(self, text="OUTPUT: Video File:", anchor=tk.W)
        self._video_label.place(x=12, y=78, width=130, height=22)
        self._video_text = tk.Label(self, relief=tk.SUNKEN, anchor=tk.W)
        self._video_text.place(x=152, y=76, width=360, height=26)
        self._video_button = ttk.Button(self, text='...', command=self._setFile)
        self._video_button.place(x=520, y=76, width=28, height=26)

        # Convert button
        self._convert_button = ttk.Button(self, text='Convert', state=tk.DISABLED, command=self.convertAudio2YouTube)
        self._convert_button.place(x=152, y=110)

        # Quit button
        self._quit_button = ttk.Button(self, text='Quit', command=self._close)
        self._quit_button.place(x=252, y=110)

        # Output
        self._output_label = tk.Label(self, text="Output:", anchor=tk.W)
        self._output_label.place(x=8, y=152, width=130, height=22)
        self._output_text = tk.Text(self, bg='black', fg='lightgray', state=tk.DISABLED)
        self._output_scroll = tk.Scrollbar(self._output_text, orient="vertical", command=self._output_text.yview)
        self._output_text.configure(yscrollcommand=self._output_scroll.set)
        self._output_scroll.pack(side="right", fill="y")
        self._output_text.place(x=8, y=172, width=540, height=160)


    def _checkFiles(self):
        # TODO: Check all files if exists or path is valid
        self._output_text['state'] = tk.NORMAL
        self._output_text.insert(1.0, 'READY')
        self._output_text.see("end")
        self._output_text['state'] = tk.DISABLED
        self._convert_button['state'] = tk.NORMAL


    def _getFile(self, title="Open Audio/Image"):
        if 'Audio' in title:
            filter = ("audio files", "*.wav *.mp3")
            dir = "~/Musik"
            self._audio_file = filedialog.askopenfilename(initialdir=dir, title=title, filetypes=(filter, ))
            self._audio_text.config(text=self._audio_file)
        elif 'Image' in title:
            filter = ("images", "*.jpg *.png *.gif")
            dir = "~/Bilder"
            self._image_file = filedialog.askopenfilename(initialdir=dir, title=title, filetypes=(filter, ))
            self._image_text.config(text=self._image_file)
        else:
            raise Exception("Invalid Filter")
        self._checkFiles()


    def _setFile(self):
        self._video_file = filedialog.asksaveasfilename(initialdir="~/Videos", title="Save Video as", filetypes=(("mp4 video", "*.mp4"), ("all files", "*.*")))
        self._video_text.config(text=self._video_file)
        self._checkFiles()


    def _close(self):
        answer = askyesno(title='Quit Application',
                          message='Are you sure that you want to quit?')
        if answer:
            self.destroy()


    @logger.catch
    @snoop
    def convertAudio2YouTube(self):
        self._convert_button['state'] = tk.DISABLED
        self._quit_button['state'] = tk.DISABLED
        self._output_text['state'] = tk.NORMAL
        self._output_text.delete("1.0", "end")
        self._output_text['state'] = tk.DISABLED

        # Execute Shell Command
        #command_call = ('ffmpeg', '-loop 1', f'-i "{self._image_file}"', f'-i "{self._audio_file}"', '-c:a copy', '-c:v libx264', f'-shortest "{self._video_file}"')

        try:
            ff = ffmpy.FFmpeg(
                    inputs={f"{self._audio_file}": None, f"{self._image_file}": '-loop 1'},
                    outputs={f"{self._video_file}": '-c:a copy -c:v libx264 -shortest'}
            )
            #TODO: use StringObject to redirect output via Variable to text_label
            stdout, stderr = ff.run(stdout=subprocess.PIPE)

            self._convert_button['state'] = tk.NORMAL
#        except Exception as ex:
#            showerror(title="EXCEPTION", message=ex)
        finally:
            self._quit_button['state'] = tk.NORMAL


if __name__ == "__main__":
    app = App()
    app.mainloop()
