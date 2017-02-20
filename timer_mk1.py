from Tkinter import *
import time

class Extractor:
    def __init__(self):
        self.root = Tk()
        self.f = Frame(self.root)
        self.open_b = Button(self.f, text = "CSV Open", command = self.open_csv).pack(side = LEFT)
        self.start = Button(self.f, text = "Run Frequency_BE", command = self.freq_be).pack(side = LEFT)
        self.pause = Button(self.f, text = "Run Frequency_AE", command = self.freq_ae).pack(side = LEFT)
        self.stop_save = Button(self.f, text = "Run IPA", command = self.IPA).pack(side = LEFT)
        self.cancel = Button(self.f, text = "Run IPA", command = self.IPA).pack(side = LEFT)

        self.canvas = Canvas(self.root, height = 20, width = 400, bg = 'white')
        self.canvas.pack()
        self.f.pack()
        self.root.mainloop()
        
    def start(self):
        pass
    