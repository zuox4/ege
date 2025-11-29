import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import time
import os
from PIL import ImageGrab
import cv2
import numpy as np
from datetime import datetime
import requests
import tempfile
import json


class ScreenRecorder:
    def __init__(self, root):
        self.root = root
        self.root.title("SHADOW RECORDER")
        self.root.geometry("350x450")  # Немного увеличил для чекбоксов

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

        # Настройки Telegram бота
        self.bot_token = "6032408418:AAG_hIpCb1KuTrPoj05m828zLuc9YbFMos8"

        # Словарь пользователей: Имя -> chat_id
        self.users_dict = {
            "Найдюк Кирилл Константинович": "411532169",
            "Гущин Алексей Генадьевич": "772810355",
            "Серегина Екатерина Игоревна": "477524759",
        }

        # Выбранные пользователи (по умолчанию все)
        self.selected_users = {name: True for name in self.users_dict.keys()}

        # Для хранения сообщений
        self.messages = []
        self.last_update_id = 0
        self.api_errors_count = 0
        self.max_api_errors = 5

        # Инициализация UI
        self.create_compact_ui()
        self.setup_bindings()

        # Запуск получения сообщений
        self.start_message_polling()

    def create_compact_ui(self):
        # Цвета
        dark_bg = '#2b2b2b'
        text_color = '#fffff3'

        # Основной контейнер
        main_frame = tk.Frame(self.root, bg=dark_bg)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Верхняя панель с кнопками-значками
        top_frame = tk.Frame(main_frame, bg=dark_bg, height=40)
        top_frame.pack(fill=tk.X, pady=(0, 5))
        top_frame.pack_propagate(False)

        # Кнопка записи
        self.record_btn = tk.Button(top_frame,
                                    text="🔴",
                                    bg='#ff5555',
                                    fg=text_color,
                                    font=('Arial', 14),
                                    width=3,
                                    height=1,
                                    relief='flat',
                                    command=self.start_recording)
        self.record_btn.pack(side=tk.LEFT, padx=2)

        # Кнопка остановки
        self.stop_btn = tk.Button(top_frame,
                                  text="⏹️",
                                  bg='#555555',
                                  fg=text_color,
                                  font=('Arial', 12),
                                  width=3,
                                  height=1,
                                  relief='flat',
                                  command=self.stop_recording,
                                  state='disabled')
        self.stop_btn.pack(side=tk.LEFT, padx=2)

        # Кнопка отправки ВЫБРАННЫМ
        self.telegram_btn = tk.Button(top_frame,
                                      text="📤",
                                      bg='#555555',
                                      fg=text_color,
                                      font=('Arial', 12),
                                      width=3,
                                      height=1,
                                      relief='flat',
                                      command=self.send_to_selected_users,
                                      state='disabled')
        self.telegram_btn.pack(side=tk.LEFT, padx=2)




        # Кнопка прозрачности
        self.alpha_btn = tk.Button(top_frame,
                                   text="⚪",
                                   bg='#555555',
                                   fg=text_color,
                                   font=('Arial', 12),
                                   width=3,
                                   height=1,
                                   relief='flat',
                                   command=self.toggle_transparency)
        self.alpha_btn.pack(side=tk.LEFT, padx=2)

        # Статус записи
        self.status_label = tk.Label(top_frame,
                                     text="⏹️",
                                     bg=dark_bg,
                                     fg='#ff5555',
                                     font=('Arial', 10))
        self.status_label.pack(side=tk.RIGHT, padx=5)

        # Панель выбора пользователей
        users_selector_frame = tk.Frame(main_frame, bg=dark_bg, height=60)
        users_selector_frame.pack(fill=tk.X, pady=(0, 5))
        users_selector_frame.pack_propagate(False)

        # Заголовок выбора пользователей
        selector_header = tk.Label(users_selector_frame,
                                   text="👥 Выберите получателей:",
                                   bg='#3a3a3a',
                                   fg=text_color,
                                   font=('Arial', 8, 'bold'))
        selector_header.pack(fill=tk.X, pady=(2, 0))

        # Фрейм для чекбоксов пользователей
        self.checkboxes_frame = tk.Frame(users_selector_frame, bg=dark_bg)
        self.checkboxes_frame.pack(fill=tk.X, padx=5, pady=2)

        # Создаем чекбоксы для пользователей
        self.user_checkboxes = {}
        self._create_user_checkboxes()

        # Чат
        chat_frame = tk.Frame(main_frame, bg=dark_bg)
        chat_frame.pack(fill=tk.BOTH, expand=True)

        # Заголовок чата
        selected_count = sum(self.selected_users.values())
        self.chat_header = tk.Label(chat_frame,
                                    text=f"💬 Telegram Chat [👥{selected_count}/{len(self.users_dict)}]",
                                    bg='#3a3a3a',
                                    fg=text_color,
                                    font=('Arial', 9, 'bold'))
        self.chat_header.pack(fill=tk.X, pady=(0, 2))

        # Область сообщений без видимого скролла
        self.chat_display = tk.Text(chat_frame,
                                    bg='#1a1a1a',
                                    fg=text_color,
                                    font=('Arial', 8),
                                    width=30,
                                    height=12,
                                    relief='flat',
                                    borderwidth=1,
                                    wrap=tk.WORD,
                                    padx=5,
                                    pady=5)

        # Создаем скроллбар но скрываем его
        self.scrollbar = tk.Scrollbar(chat_frame,
                                      orient=tk.VERTICAL,
                                      command=self.chat_display.yview,
                                      width=0)
        self.chat_display.configure(yscrollcommand=self.scrollbar.set)

        self.chat_display.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.scrollbar.configure(troughcolor='#1a1a1a',
                                 bg='#1a1a1a',
                                 activebackground='#1a1a1a')

        self.chat_display.config(state='disabled')

        # Нижняя панель информации
        bottom_frame = tk.Frame(main_frame, bg=dark_bg, height=20)
        bottom_frame.pack(fill=tk.X, pady=(5, 0))
        bottom_frame.pack_propagate(False)

        self.info_label = tk.Label(bottom_frame,
                                   text=f"α:{int(self.current_alpha * 100)}% | F9:rec | AVI",
                                   bg=dark_bg,
                                   fg='#888888',
                                   font=('Arial', 7))
        self.info_label.pack(side=tk.LEFT)

        self.message_count = tk.Label(bottom_frame,
                                      text="Msgs: 0",
                                      bg=dark_bg,
                                      fg='#888888',
                                      font=('Arial', 7))
        self.message_count.pack(side=tk.RIGHT)

        # Статус API
        self.api_status = tk.Label(bottom_frame,
                                   text="",
                                   bg=dark_bg,
                                   fg='#00ff00',
                                   font=('Arial', 7))
        self.api_status.pack(side=tk.RIGHT, padx=5)

    def _create_user_checkboxes(self):
        """Создание чекбоксов для выбора пользователей"""
        # Очищаем старые чекбоксы
        for widget in self.checkboxes_frame.winfo_children():
            widget.destroy()

        self.user_checkboxes = {}

        # Создаем чекбоксы для каждого пользователя
        for i, (name, chat_id) in enumerate(self.users_dict.items()):
            var = tk.BooleanVar(value=self.selected_users.get(name, True))

            checkbox = tk.Checkbutton(self.checkboxes_frame,
                                      text=f"{name[:15]}...",
                                      variable=var,
                                      bg='#2b2b2b',
                                      fg='#ffffff',
                                      selectcolor='#1a1a1a',
                                      activebackground='#2b2b2b',
                                      activeforeground='#ffffff',
                                      font=('Arial', 7),
                                      command=lambda n=name, v=var: self._on_user_selection_change(n, v))

            # Размещаем в две колонки
            if i % 2 == 0:
                checkbox.pack(side=tk.LEFT, padx=(0, 10))
            else:
                checkbox.pack(side=tk.LEFT)

            self.user_checkboxes[name] = var

    def _on_user_selection_change(self, username, var):
        """Обработчик изменения выбора пользователя"""
        self.selected_users[username] = var.get()
        selected_count = sum(self.selected_users.values())
        self.chat_header.config(text=f"💬 Telegram Chat [👥{selected_count}/{len(self.users_dict)}]")




    def _update_chat_header(self):
        """Обновление заголовка чата"""
        selected_count = sum(self.selected_users.values())
        self.chat_header.config(text=f"💬 Telegram Chat [👥{selected_count}/{len(self.users_dict)}]")

    def start_recording(self):
        try:
            temp_dir = tempfile.gettempdir()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Записываем в AVI для лучшего качества
            self.output_file = os.path.join(temp_dir, f"record_{timestamp}.avi")

            screen_width, screen_height = ImageGrab.grab().size

            # Используем XVID кодек для AVI (лучшее качество)
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            self.video_writer = cv2.VideoWriter(
                self.output_file,
                fourcc,
                30.0,  # Высокий FPS для плавности
                (screen_width, screen_height)
            )

            self.recording = True
            self.start_time = time.time()

            self.record_btn.config(state='disabled', bg='#555555')
            self.stop_btn.config(state='normal', bg='#00ff00')
            self.telegram_btn.config(state='disabled')
            self.status_label.config(text="🔴", fg='#00ff00')

            self.recording_thread = threading.Thread(target=self.record_screen, daemon=True)
            self.recording_thread.start()

            self.add_message_to_chat("SYSTEM", "🎥 Запись начата (качество: AVI)")

        except Exception as e:
            self.add_message_to_chat("SYSTEM", f"Ошибка записи: {e}")

    def send_to_selected_users(self):
        """Отправка видео выбранным пользователям"""
        if not self.output_file or not os.path.exists(self.output_file):
            self.add_message_to_chat("SYSTEM", "Нет файла для отправки")
            return

        # Получаем выбранных пользователей
        selected_users = {name: chat_id for name, chat_id in self.users_dict.items()
                          if self.selected_users.get(name, False)}

        if not selected_users:
            self.add_message_to_chat("SYSTEM", "❌ Не выбрано ни одного пользователя")
            return

        def send_to_selected_thread():
            try:
                self.telegram_btn.config(state='disabled', text="⏳")
                total_users = len(selected_users)
                successful_sends = 0

                file_size = os.path.getsize(self.output_file) / (1024 * 1024)
                self.add_message_to_chat("SYSTEM", f"📤 Отправка {total_users} пользователям ({file_size:.1f}MB AVI)...")

                for i, (name, chat_id) in enumerate(selected_users.items(), 1):
                    try:
                        success = self._send_to_single_user(name, chat_id, i, total_users)
                        if success:
                            successful_sends += 1
                    except Exception as e:
                        self.add_message_to_chat("SYSTEM", f"❌ Ошибка для {name}: {str(e)[:30]}")

                # Итоговый отчет
                if successful_sends == total_users:
                    self.add_message_to_chat("SYSTEM", f"✅ Успешно отправлено всем {total_users} пользователям")
                else:
                    self.add_message_to_chat("SYSTEM", f"📊 Отправлено {successful_sends}/{total_users} пользователям")

                self.api_errors_count = 0

            except Exception as e:
                self.add_message_to_chat("SYSTEM", f"❌ Общая ошибка отправки: {str(e)[:50]}")
                self.api_errors_count += 1
            finally:
                self.telegram_btn.config(state='normal', text="📤")
                self._update_api_status()

        threading.Thread(target=send_to_selected_thread, daemon=True).start()

    def _send_to_single_user(self, name, chat_id, current_num, total_users):
        """Отправка видео одному пользователю"""
        url = f"https://api.telegram.org/bot{self.bot_token}/sendVideo"

        caption = f'Запись экрана {datetime.now().strftime("%H:%M:%S")}'

        with open(self.output_file, 'rb') as video_file:
            files = {'video': video_file}
            data = {
                'chat_id': chat_id,
                'caption': caption
            }
            response = requests.post(url, files=files, data=data, timeout=60)

        if response.status_code == 200:
            short_name = name.split()[0]  # Берем только имя
            self.add_message_to_chat("BOT", f"✅ [{current_num}/{total_users}] {short_name}")
            return True
        else:
            error_msg = self._parse_telegram_error(response)
            short_name = name.split()[0]
            self.add_message_to_chat("BOT", f"❌ [{current_num}/{total_users}] {short_name}: {error_msg}")
            return False

    # Остальные методы остаются без изменений
    def toggle_transparency(self):
        if self.current_alpha == 0.05:
            self.current_alpha = 0.3
            self.alpha_btn.config(text="🔵")
        elif self.current_alpha == 0.3:
            self.current_alpha = 0.7
            self.alpha_btn.config(text="🔘")
        else:
            self.current_alpha = 0.05
            self.alpha_btn.config(text="⚪")

        self.root.attributes('-alpha', self.current_alpha)
        self.info_label.config(text=f"α:{int(self.current_alpha * 100)}% | F9:rec | AVI")

    def setup_bindings(self):
        self.root.bind('<F9>', lambda e: self.toggle_recording())
        self.root.bind('<Control-plus>', lambda e: self.more_transparent())
        self.root.bind('<Control-minus>', lambda e: self.less_transparent())

        self.chat_display.bind("<MouseWheel>", self._on_mousewheel)
        self.chat_display.bind("<Button-4>", self._on_mousewheel)
        self.chat_display.bind("<Button-5>", self._on_mousewheel)

    def _on_mousewheel(self, event):
        if event.delta:
            self.chat_display.yview_scroll(int(-1 * (event.delta / 120)), "units")
        else:
            if event.num == 4:
                self.chat_display.yview_scroll(-1, "units")
            elif event.num == 5:
                self.chat_display.yview_scroll(1, "units")

    def more_transparent(self):
        if self.current_alpha > 0.05:
            self.current_alpha -= 0.05
            self.root.attributes('-alpha', self.current_alpha)
            self.info_label.config(text=f"α:{int(self.current_alpha * 100)}% | F9:rec | AVI")

    def less_transparent(self):
        if self.current_alpha < 1.0:
            self.current_alpha += 0.05
            self.root.attributes('-alpha', self.current_alpha)
            self.info_label.config(text=f"α:{int(self.current_alpha * 100)}% | F9:rec | AVI")

    def toggle_recording(self):
        if not self.recording:
            self.start_recording()
        else:
            self.stop_recording()

    def stop_recording(self):
        self.recording = False

        if self.video_writer:
            self.video_writer.release()
            self.video_writer = None

        self.record_btn.config(state='normal', bg='#ff5555')
        self.stop_btn.config(state='disabled', bg='#555555')
        self.telegram_btn.config(state='normal', bg='#0088cc')
        self.status_label.config(text="⏹️", fg='#ff5555')

        duration = int(time.time() - self.start_time)
        self.add_message_to_chat("SYSTEM", f"⏹️ Запись остановлена ({duration} сек)")

    def record_screen(self):
        while self.recording:
            try:
                screenshot = ImageGrab.grab()
                frame = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

                if self.video_writer:
                    self.video_writer.write(frame)

                time.sleep(1 / 30)

            except Exception as e:
                self.add_message_to_chat("SYSTEM", f"Ошибка записи: {e}")
                break

    def get_telegram_updates(self):
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/getUpdates"
            params = {
                'timeout': 20,
                'offset': self.last_update_id + 1,
                'limit': 10
            }

            response = requests.get(url, params=params, timeout=25)

            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    if data['result']:
                        for update in data['result']:
                            self.last_update_id = update['update_id']
                            if 'message' in update:
                                msg = update['message']
                                user = msg['from'].get('first_name', 'Unknown')
                                text = msg.get('text', '')
                                if text:
                                    self.add_message_to_chat(user, text)
                    self.api_errors_count = 0
                else:
                    self._handle_api_error(f"API error: {data.get('description', 'Unknown')}")
            else:
                self._handle_api_error(f"HTTP {response.status_code}")

        except requests.exceptions.Timeout:
            pass
        except requests.exceptions.ConnectionError:
            self._handle_api_error("Connection error")
        except requests.exceptions.RequestException as e:
            self._handle_api_error(f"Network error: {str(e)[:30]}")
        except Exception as e:
            self._handle_api_error(f"Unexpected error: {str(e)[:30]}")

        self._update_api_status()

    def _handle_api_error(self, error_msg):
        self.api_errors_count += 1

        if self.api_errors_count >= 3:
            self.root.after(0, lambda: self._show_api_error_in_chat(error_msg))

        if self.api_errors_count > self.max_api_errors:
            time.sleep(10)

    def _show_api_error_in_chat(self, error_msg):
        last_messages = self.messages[-3:] if self.messages else []
        error_shown = any("API Error" in msg for msg in last_messages)

        if not error_shown:
            self.add_message_to_chat("SYSTEM", f"API Error: {error_msg}")

    def _update_api_status(self):
        status_color = '#00ff00' if self.api_errors_count == 0 else '#ff5555'
        status_text = "✓" if self.api_errors_count == 0 else f"⚠{self.api_errors_count}"

        self.api_status.config(text=status_text, fg=status_color)

    def _parse_telegram_error(self, response):
        try:
            error_data = response.json()
            if not error_data.get('ok'):
                description = error_data.get('description', 'Unknown error')
                if "bot was blocked" in description.lower():
                    return "Бот заблокирован"
                elif "chat not found" in description.lower():
                    return "Чат не найден"
                elif "too large" in description.lower():
                    return "Файл слишком большой"
                else:
                    return f"API: {description[:40]}"
        except:
            pass
        return f"HTTP {response.status_code}"

    def start_message_polling(self):
        def poll():
            while True:
                self.get_telegram_updates()

                if self.api_errors_count == 0:
                    time.sleep(2)
                elif self.api_errors_count <= 2:
                    time.sleep(5)
                else:
                    time.sleep(10)

        threading.Thread(target=poll, daemon=True).start()

    def add_message_to_chat(self, user, message):
        timestamp = datetime.now().strftime("%H:%M:%S")

        if len(message) > 50:
            message = message[:47] + "..."

        formatted_message = f"[{timestamp}] {user}: {message}\n"

        self.chat_display.config(state='normal')
        self.chat_display.insert('end', formatted_message)
        self.chat_display.see('end')
        self.chat_display.config(state='disabled')

        self.messages.append(formatted_message)
        if len(self.messages) > 100:
            self.messages = self.messages[-100:]

        self.message_count.config(text=f"Msgs: {len(self.messages)}")


if __name__ == "__main__":
    root = tk.Tk()
    app = ScreenRecorder(root)
    root.mainloop()