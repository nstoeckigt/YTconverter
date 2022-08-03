#!/bin/env python3

import os, sys
import subprocess
import threading
import asyncio
from loguru import logger
import snoop
import tkinter as tk
from tkinter import filedialog, ttk
from tkinter.messagebox import askyesno, askquestion, showinfo, showwarning, showerror
from functools import partial
import ffmpy


class ConsoleText(tk.Text):
    '''A Tkinter Text widget that provides a scrolling display of console
    stderr and stdout.'''


    class IORedirector(object):
        '''A general class for redirecting I/O to this Text widget.'''
        def __init__(self, text_area):
            self.text_area = text_area


    class StdoutRedirector(IORedirector):
        '''A class for redirecting stdout to this Text widget.'''
        def write(self, str):
            self.text_area.write(str, False)


    class StderrRedirector(IORedirector):
        '''A class for redirecting stderr to this Text widget.'''
        def write(self, str):
            self.text_area.write(str, True)


    def __init__(self, master=None, cnf={}, **kw):
        '''See the __init__ for Tkinter.Text for most of this stuff.'''

        tk.Text.__init__(self, master, cnf, **kw)

        self.started = False
        self.write_lock = threading.Lock()
        self.config(state=tk.NORMAL)
        self.bind('<Key>', lambda e: 'break') #ignore all key presses


    def start(self):
        if self.started:
            return

        self.started = True

        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr

        stdout_redirector = ConsoleText.StdoutRedirector(self)
        stderr_redirector = ConsoleText.StderrRedirector(self)

        sys.stdout = stdout_redirector
        sys.stderr = stderr_redirector


    def stop(self):
        if not self.started:
            return

        self.started = False

        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr

    @snoop
    def write(self, val, is_stderr=False):
        self.write_lock.acquire()
        self.config(state=tk.NORMAL)

        self.insert('end', val.encode('utf8'), 'STDERR' if is_stderr else 'STDOUT')
        self.see('end')
        self.update_idletasks()

        self.config(state=tk.DISABLED)
        self.write_lock.release()


    def flush(self):
        pass


class App(tk.Tk):

    def __init__(self):
        super().__init__()

        #TODO: add NAG screen

        self.title("audio2video Converter")
        self.resizable(False, False)
        self.geometry('560x340')
        self.update_idletasks()
        self.option_add('*Dialog.msg.font', 'Helvetica 10')

        self._audio_file = None
        self._image_file = None
        self._video_file = None

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
        ##self._convert_button = ttk.Button(self, text='Convert', state=tk.DISABLED, command=threading.Thread(target=self.convertAudio2YouTube).start())
        self._convert_button.place(x=152, y=110)

        # Quit button
        self._quit_button = ttk.Button(self, text='Quit', command=self._close)
        self._quit_button.place(x=252, y=110)

        # Output
        self._output_label = tk.Label(self, text="Output:", anchor=tk.W)
        self._output_label.place(x=8, y=152, width=130, height=22)
        ##self._output_text = tk.Text(self, bg='black', fg='lightgray', state=tk.DISABLED)
        self._output_text = ConsoleText(self, {'bg': 'black', 'fg': 'lightgray'}, state=tk.NORMAL)
        self._output_scroll = tk.Scrollbar(self._output_text, orient="vertical", command=self._output_text.yview)
        self._output_text.configure(yscrollcommand=self._output_scroll.set)
        self._output_scroll.pack(side="right", fill="y")
        self._output_text.place(x=8, y=172, width=540, height=160)


    def _checkFiles(self):
        if self._audio_file: af_check = os.path.isfile(self._audio_file)
        else: af_check = None
        if self._image_file: if_check = os.path.isfile(self._image_file)
        else: if_check = None
        if self._video_file: vf_check = os.path.exists(os.path.dirname(self._video_file))
        else: vf_check = None

        if af_check and if_check and af_check:
            self._output_text.insert(1.0, 'READY')
            self._output_text.see("end")
            self._convert_button['state'] = tk.NORMAL
        else:
            if af_check == False:
                self._audio_text.config(bg='red')
            if if_check == False:
                self._image_text.config(bg='red')
            if vf_check == False:
                self._video_text.config(bg='red')


    def _getFile(self, title="Open Audio/Image"):
        if 'Audio' in title:
            filter = ("audio files", "*.wav *.mp3")
            dir = "~/Musik"
            self._audio_text.config(bg='white')
            self._audio_file = filedialog.askopenfilename(initialdir=dir, title=title, filetypes=(filter, ))
            if isinstance(self._audio_file, bytes):
                self._audio_file = self._audio_file.decode('utf-8')
            self._audio_text.config(text=self._audio_file)
        elif 'Image' in title:
            filter = ("images", "*.jpg *.png *.gif")
            dir = "~/Bilder"
            self._image_text.config(bg='white')
            self._image_file = filedialog.askopenfilename(initialdir=dir, title=title, filetypes=(filter, ))
            if isinstance(self._image_file, bytes):
                self._image_file = self._image_file.decode('utf-8')
            self._image_text.config(text=self._image_file)
        else:
            raise Exception("Invalid Filter")
        self._checkFiles()


    def _setFile(self):
        self._video_text.config(bg='white')
        self._video_file = filedialog.asksaveasfilename(initialdir="~/Videos", title="Save Video as", filetypes=(("mp4 video", "*.mp4"), ("all files", "*.*")))
        if isinstance(self._video_file, bytes):
            self._video_file = self._video_file.decode('utf-8')
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
        self._output_text.delete("1.0", "end")

        # Execute Shell Command
        #command_call = (f'ffmpeg -loop 1 -i "{self._image_file}" -i "{self._audio_file}" -c:a copy -c:v libx264 -shortest "{self._video_file}"'

        try:
            self._output_text.start()
            ff = ffmpy.FFmpeg(
                    inputs={f"{self._audio_file}": None, f"{self._image_file}": '-loop 1'},
                    outputs={f"{self._video_file}": '-y -c:a copy -c:v libx264 -shortest'}
            )
            #TODO: use StringObject to redirect output via Variable to text_label
            stdout, stderr = ff.run(stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            self._convert_button['state'] = tk.NORMAL
#        except Exception as ex:
#            showerror(title="EXCEPTION", message=ex)
        finally:
            self._output_text.stop()
            self._quit_button['state'] = tk.NORMAL


if __name__ == "__main__":
    app = App()
    app.mainloop()
