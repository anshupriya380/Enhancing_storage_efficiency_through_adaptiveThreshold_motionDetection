import cv2
import tkinter as tk
from tkinter import ttk
from tkinter.constants import *
from tkinter import messagebox
from PIL import Image, ImageTk
from threading import Thread
import datetime
import os
import time
from moviepy.editor import VideoFileClip, concatenate_videoclips

class VideoProcessor:
    def __init__(self, master, recorded_output_folder, concatenated_output_folder):
        self.master = master
        self.cap = cv2.VideoCapture(0)
        self.frame_size = (int(self.cap.get(3)), int(self.cap.get(4)))
        self.out = None
        self.recording = False
        self.processing = False
        self.motion_detected = False
        self.motion_start_time = None
        self.motion_timeout = 2  # Timeout in seconds
        self.backSub = cv2.createBackgroundSubtractorMOG2(detectShadows=True)
        self.backSub.setVarThreshold(100)
        self.recorded_output_folder = recorded_output_folder
        self.concatenated_output_folder = concatenated_output_folder
        self.night_vision_on = False
        self.video_files = []

    current_time: str = ""

    def start_recording(self):
        if not self.recording:
            self.recording = True
            self.current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = os.path.join(self.recorded_output_folder, f"recorded_video_{self.current_time}.avi")
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            self.out = cv2.VideoWriter(output_filename, fourcc, 20.0, self.frame_size)
            print("Recording started.")

    def stop_recording(self):
        self.recording = False
        if self.out is not None:
            self.out.release()
            self.out = None
            self.video_files.append(f"recorded_video_{self.current_time}.avi")
            print("Recording stopped.")
            #self.stop_processing()

    def start_processing(self):
        if not self.processing:
            self.processing = True
            self.process_thread = Thread(target=self._process)
            self.process_thread.start()

    def stop_processing(self):
        self.processing = False

    def toggle_night_vision(self):
        self.night_vision_on = not self.night_vision_on

    def _record(self, frame):
        if self.recording:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cv2.putText(frame, timestamp, (10, self.frame_size[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1, cv2.LINE_AA)
            self.out.write(frame)

    def _process(self):
        while self.processing:
            ret, frame = self.cap.read()
            if ret:
                fgMask = self.backSub.apply(frame)
                motion_pixels = cv2.countNonZero(fgMask)

                if motion_pixels > 500:  # Adjusted motion threshold
                    if not self.motion_detected:
                        self.motion_detected = True
                        self.motion_start_time = time.time()
                        self.start_recording()
                        print("Motion detected. Recording started.")
                elif self.motion_detected:
                    if time.time() - self.motion_start_time >= self.motion_timeout:
                        self.motion_detected = False
                        self.stop_recording()
                        print("Motion stopped. Recording stopped.")

                if self.motion_detected:
                    if self.night_vision_on:
                        frame = self.apply_night_vision(frame)

                    self._record(frame)

                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    cv2.putText(frame, timestamp, (10, self.frame_size[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1, cv2.LINE_AA)

                    cv2.imshow('Processed Video', frame)

                # Check for events and exit loop if tkinter window is destroyed
                if cv2.waitKey(1) & 0xFF == ord('q') or cv2.getWindowProperty('Processed Video', cv2.WND_PROP_VISIBLE) < 1:
                    break

                # Update tkinter window to handle events
                self.master.update()

        cv2.destroyAllWindows()  # Ensure OpenCV windows are destroyed when processing stops

    def apply_night_vision(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY)
        night_vision = cv2.bitwise_not(thresh)
        night_vision = cv2.cvtColor(night_vision, cv2.COLOR_GRAY2BGR)
        return night_vision

    def concatenate_videos(self):
        if self.video_files:
            clips = [VideoFileClip(os.path.join(self.recorded_output_folder, file)) for file in self.video_files]
            final_clip = concatenate_videoclips(clips)
            output_filename = os.path.join(self.concatenated_output_folder, "concatenated_video.avi")
            final_clip.write_videofile(output_filename, codec="libx264")
            final_clip.close()
            for file in self.video_files:
                os.remove(os.path.join(self.recorded_output_folder, file))
            self.video_files = []
            print(f"Concatenated video saved as '{output_filename}'")
        else:
            print("No recorded videos to concatenate.")

    def __del__(self):
        self.cap.release()

class App:
    def __init__(self, master):
        self.master = master
        self.master.title("Video Processing App")
        self.master.geometry("800x600")
        # Load the background image
        background_image = Image.open("D:\\project\\4TH_YR_PROJECT\\pic1.jpeg")
        # Resize the image to fit the window size
        background_image = background_image.resize((800, 600))
        # Convert the image to Tkinter-compatible format
        self.background_photo = ImageTk.PhotoImage(background_image)

        # Create a label to display the background image
        self.background_label = tk.Label(self.master, image=self.background_photo)
        self.background_label.place(x=0, y=0, relwidth=1, relheight=1)


        self.video_processor = VideoProcessor(master, recorded_output_folder='D:\\project\\4TH_YR_PROJECT\\app_cctv\\recorded_videos',
                                              concatenated_output_folder='D:\\project\\4TH_YR_PROJECT\\app_cctv\\recorded_videos')

        # Create buttons with gradient backgrounds using hexadecimal color codes
        self.start_recording_button = tk.Button(self.master, text="Start Recording", command=self.video_processor.start_processing,
                                                bg='#008000', fg='white', activebackground='#006400', activeforeground='white') # Green
        self.start_recording_button.config(height=3, width=20)  # Set button size
        self.start_recording_button.pack(side=LEFT, expand=YES, padx=10, pady=10)  # Use pack layout to place button and allow it to expand

        self.night_vision_button = tk.Button(self.master, text="Night Vision", command=self.toggle_night_vision,
                                             bg='#0000FF', fg='white', activebackground='#00008B', activeforeground='white') # Blue
        self.night_vision_button.config(height=3, width=20)  # Set button size
        self.night_vision_button.pack(side=LEFT, expand=YES, padx=10, pady=10)  # Use pack layout to place button and allow it to expand

        self.stop_recording_button = tk.Button(self.master, text="Stop Recording", command=self.stop_recording,
                                               bg='#FF0000', fg='white', activebackground='#8B0000', activeforeground='white') # Red
        self.stop_recording_button.config(height=3, width=20)  # Set button size
        self.stop_recording_button.pack(side=LEFT, expand=YES, padx=10, pady=10)  # Use pack layout to place button and allow it to expand

        self.concat_button = tk.Button(self.master, text="Concatenate Videos", command=self.concat_and_exit,
                                       bg='#800080', fg='white', activebackground='#4B0082', activeforeground='white') # Purple
        self.concat_button.config(height=3, width=20)  # Set button size
        self.concat_button.pack(side=LEFT, expand=YES, padx=10, pady=10)  # Use pack layout to place button and allow it to expand

        self.complete_button = tk.Button(self.master, text="Complete", command=self.complete,
                                          bg='#FFA500', fg='white', activebackground='#FF8C00', activeforeground='white') # Orange
        self.complete_button.config(height=3, width=20)  # Set button size
        self.complete_button.pack(side=LEFT, expand=YES, padx=10, pady=10)  # Use pack layout to place button and allow it to expand


        # Bind the window destruction event to the video concatenation method
        self.master.protocol("WM_DELETE_WINDOW", self.concat_and_exit)

        self.complete_flag = False

    def stop_recording(self):
        self.video_processor.stop_recording()
        messagebox.showinfo("Recording Stopped", "Recording stopped.")

    def toggle_night_vision(self):
        self.video_processor.toggle_night_vision()
        if self.video_processor.night_vision_on:
            messagebox.showinfo("Night Vision On", "Night Vision enabled.")
        else:
            messagebox.showinfo("Night Vision Off", "Night Vision disabled.")

    def concat_and_exit(self):
        self.video_processor.concatenate_videos()
        self.master.destroy()

    def complete(self):
        self.complete_flag = True
        self.stop_recording()
        self.video_processor.stop_processing()
        self.master.destroy()

    def is_complete(self):
        return self.complete_flag

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()

    if app.is_complete():
        print("Processing Complete!")

