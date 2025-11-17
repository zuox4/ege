import tkinter as tk
from tkinter import messagebox
import threading
import time
import os
from PIL import ImageGrab
import cv2
import numpy as np
from datetime import datetime
import requests
import tempfile


class ScreenRecorder:
    def __init__(self, root):
        self.root = root
        self.root.title("SHADOW RECORDER")
        self.root.geometry("500x200")

        # Настройки прозрачности
        self.current_alpha = 0.05
        self.root.attributes('-alpha', self.current_alpha)
        self.root.configure(bg='#2b2b2b')

        # Переменные для записи
        self.recording = False
        self.video_writer = None
        self.recording_thread = None
        self.output_file = None
        self.start_time = None

        # Настройки Telegram бота (ЗАМЕНИТЕ НА СВОИ!)
        self.bot_token = "6032408418:AAG_hIpCb1KuTrPoj05m828zLuc9YbFMos8"
        self.chat_id = "411532169"
        self.root.overrideredirect(True)

        self.create_ui()
        self.setup_bindings()

    def create_ui(self):
        # Цвета
        dark_bg = '#2b2b2b'
        text_color = '#fffff3'

        # Создаем кастомный заголовок
        self.title_bar = tk.Frame(self.root, bg=dark_bg, height=30)
        self.title_bar.pack(fill=tk.X, side=tk.TOP)
        self.title_bar.pack_propagate(False)

        # Название программы в заголовке
        title_label = tk.Label(self.title_bar,
                               text="🎥 Screen Recorder",
                               bg=dark_bg,
                               fg=text_color,
                               font=('Arial', 10, 'bold'))
        title_label.pack(side=tk.LEFT, padx=10, pady=5)

        # Статус записи в заголовке
        self.recording_status = tk.Label(self.title_bar,
                                         text="⏹️ Не записывается",
                                         bg=dark_bg,
                                         fg='#ff5555',
                                         font=('Arial', 8))
        self.recording_status.pack(side=tk.RIGHT, padx=15, pady=5)

        # Кнопки управления окном
        controls_frame = tk.Frame(self.title_bar, bg=dark_bg)
        controls_frame.pack(side=tk.RIGHT, padx=5)

        minimize_btn = tk.Button(controls_frame,
                                 text="─",
                                 bg=dark_bg,
                                 fg=text_color,
                                 font=('Arial', 10),
                                 borderwidth=0,
                                 command=self.root.iconify)
        minimize_btn.pack(side=tk.LEFT, padx=2)

        close_btn = tk.Button(controls_frame,
                              text="×",
                              bg=dark_bg,
                              fg=text_color,
                              font=('Arial', 12),
                              borderwidth=0,
                              command=self.root.quit)
        close_btn.pack(side=tk.LEFT, padx=2)

        # Основное содержимое
        main_frame = tk.Frame(self.root, bg=dark_bg, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Три основные кнопки
        buttons_frame = tk.Frame(main_frame, bg=dark_bg)
        buttons_frame.pack(fill=tk.X, pady=10)

        # Кнопка начала записи
        self.record_btn = tk.Button(buttons_frame,
                                    text="🎥 Начать запись",
                                    bg='#ff5555',
                                    fg=text_color,
                                    font=('Arial', 12, 'bold'),
                                    width=15,
                                    height=2,
                                    command=self.start_recording)
        self.record_btn.pack(side=tk.LEFT, padx=10)

        # Кнопка остановки записи
        self.stop_btn = tk.Button(buttons_frame,
                                  text="⏹️ Остановить",
                                  bg='#555555',
                                  fg=text_color,
                                  font=('Arial', 12),
                                  width=15,
                                  height=2,
                                  command=self.stop_recording,
                                  state='disabled')
        self.stop_btn.pack(side=tk.LEFT, padx=10)

        # Кнопка отправки в Telegram
        self.telegram_btn = tk.Button(buttons_frame,
                                      text="📤 В Telegram",
                                      bg='#555555',
                                      fg=text_color,
                                      font=('Arial', 12),
                                      width=15,
                                      height=2,
                                      command=self.send_to_telegram,
                                      state='disabled')
        self.telegram_btn.pack(side=tk.LEFT, padx=10)

        # Информация о записи
        info_frame = tk.Frame(main_frame, bg=dark_bg)
        info_frame.pack(fill=tk.X, pady=10)

        # self.time_label = tk.Label(info_frame,
        #                            text="Время записи: 00:00:00",
        #                            bg=dark_bg,
        #                            fg=text_color,
        #                            font=('Arial', 10))
        # self.time_label.pack(side=tk.LEFT)
        #
        # self.file_label = tk.Label(info_frame,
        #                            text="Файл: -",
        #                            bg=dark_bg,
        #                            fg=text_color,
        #                            font=('Arial', 10))
        # self.file_label.pack(side=tk.RIGHT)

        # # Статус прозрачности
        # self.status = tk.Label(main_frame,
        #                        text=f"Прозрачность: {int(self.current_alpha * 100)}% | F9 - запись",
        #                        bg=dark_bg,
        #                        fg='#888888',
        #                        font=('Arial', 8))
        # self.status.pack(fill=tk.X, pady=(10, 0))

    def setup_bindings(self):
        self.root.bind('<Control-plus>', lambda e: self.more_transparent())
        self.root.bind('<Control-minus>', lambda e: self.less_transparent())
        self.root.bind('<F9>', lambda e: self.toggle_recording())

        # Перетаскивание окна за заголовок
        self.title_bar.bind('<Button-1>', self.start_move)
        self.title_bar.bind('<B1-Motion>', self.on_move)

    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def on_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{x}+{y}")

    def more_transparent(self):
        if self.current_alpha > 0.05:
            self.current_alpha -= 0.05
            self.root.attributes('-alpha', self.current_alpha)
            self.status.config(text=f"Прозрачность: {int(self.current_alpha * 100)}% | F9 - запись")

    def less_transparent(self):
        if self.current_alpha < 1.0:
            self.current_alpha += 0.05
            self.root.attributes('-alpha', self.current_alpha)
            self.status.config(text=f"Прозрачность: {int(self.current_alpha * 100)}% | F9 - запись")

    def toggle_recording(self):
        if not self.recording:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        try:
            # Создаем временную папку для записи
            temp_dir = tempfile.gettempdir()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.output_file = os.path.join(temp_dir, f"record_{timestamp}.avi")

            # Получаем размер экрана
            screen_width, screen_height = ImageGrab.grab().size

            # Создаем VideoWriter
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            self.video_writer = cv2.VideoWriter(
                self.output_file,
                fourcc,
                30,  # FPS
                (screen_width, screen_height)
            )

            self.recording = True
            self.start_time = time.time()

            # Обновляем UI
            self.record_btn.config(state='disabled', bg='#555555')
            self.stop_btn.config(state='normal', bg='#00ff00')
            self.telegram_btn.config(state='disabled')
            self.recording_status.config(text="🔴 Запись...", fg='#00ff00')
            self.file_label.config(text=f"Файл: {os.path.basename(self.output_file)}")

            # Запускаем поток записи
            self.recording_thread = threading.Thread(target=self.record_screen, daemon=True)
            self.recording_thread.start()

            # Запускаем обновление таймера
            self.update_timer()

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось начать запись: {e}")

    def stop_recording(self):
        self.recording = False

        if self.video_writer:
            self.video_writer.release()
            self.video_writer = None

        # Обновляем UI
        self.record_btn.config(state='normal', bg='#ff5555')
        self.stop_btn.config(state='disabled', bg='#555555')
        self.telegram_btn.config(state='normal', bg='#0088cc')
        self.recording_status.config(text="⏹️ Запись остановлена", fg='#ff5555')
        # self.time_label.config(text="Время записи: 00:00:00")

    def record_screen(self):
        while self.recording:
            try:
                # Захватываем скриншот
                screenshot = ImageGrab.grab()
                frame = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

                # Записываем кадр
                if self.video_writer:
                    self.video_writer.write(frame)

                # Небольшая задержка для контроля FPS
                time.sleep(1 / 30)

            except Exception as e:
                print(f"Ошибка записи: {e}")
                break

    def update_timer(self):
        if self.recording:
            elapsed = int(time.time() - self.start_time)
            hours = elapsed // 3600
            minutes = (elapsed % 3600) // 60
            seconds = elapsed % 60
            self.time_label.config(text=f"Время записи: {hours:02d}:{minutes:02d}:{seconds:02d}")
            self.root.after(1000, self.update_timer)

    def send_to_telegram(self):
        if not self.output_file or not os.path.exists(self.output_file):
            messagebox.showwarning("Предупреждение", "Нет файла для отправки")
            return

        if self.bot_token == "YOUR_BOT_TOKEN_HERE" or self.chat_id == "YOUR_CHAT_ID_HERE":
            messagebox.showwarning("Настройка", "Сначала настройте токен бота и chat ID!")
            return

        def send_thread():
            try:
                # Обновляем UI
                self.telegram_btn.config(state='disabled', text="📤 Отправка...")

                # Отправка файла в Telegram
                url = f"https://api.telegram.org/bot{self.bot_token}/sendVideo"

                with open(self.output_file, 'rb') as video_file:
                    files = {'video': video_file}
                    data = {'chat_id': self.chat_id}
                    response = requests.post(url, files=files, data=data)

                if response.status_code == 200:
                    messagebox.showinfo("Успех", "Видео отправлено в Telegram!")
                else:
                    messagebox.showerror("Ошибка", f"Не удалось отправить: {response.text}")

            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка отправки: {e}")
            finally:
                # Восстанавливаем UI
                self.root.after(0, lambda: self.telegram_btn.config(
                    state='normal', text="📤 В Telegram"))

        # Запускаем в отдельном потоке
        threading.Thread(target=send_thread, daemon=True).start()


if __name__ == "__main__":
    root = tk.Tk()
    app = ScreenRecorder(root)
    root.mainloop()