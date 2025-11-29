import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
from openai import OpenAI
import sqlite3
from datetime import datetime


class EGEAssistant:
    def __init__(self, root):
        self.root = root
        self.root.title("👻 Ассистент ЕГЭ по информатике")
        self.root.geometry("1200x800")
        # self.root.overrideredirect(True)
        # Цвета PyCharm темной темы
        self.colors = {
            'bg': '#1E1F22',
            'card_bg': '#1E1F22',
            'text': '#a9b7c6',
            'accent': '#1E1F22',
            'secondary': '#1E1F22',
            'success': '#499c54',
            'warning': '#d0b344',
            'error': '#c75450',
            'user_msg': '#365880',
            'assistant_msg': '#2d5a7a',
            'system_msg': '#5d4a2a'
        }

        self.root.configure(bg=self.colors['bg'])

        # Настройки прозрачности (минимум)
        self.current_alpha = 0.3
        self.root.attributes('-alpha', self.current_alpha)

        # Переменные для перемещения окна
        self.x = 0
        self.y = 0

        # Инициализация OpenAI клиента
        self.client = OpenAI(
            api_key='sk-cfc4609bed994c85bc26d8c29d433030',
            base_url="https://api.deepseek.com"
        )

        # Инициализация базы данных
        self.init_database()

        self.setup_styles()
        self.create_widgets()
        self.setup_bindings()

        # Загрузка истории чата
        self.load_chat_history()

    def init_database(self):
        """Инициализация SQLite базы данных"""
        self.db_path = "chat_history.db"
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()

        # Создание таблицы для истории чата
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                message_type TEXT NOT NULL
            )
        ''')

        # Создание таблицы для сессий
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')

        # Создание текущей сессии
        current_time = datetime.now().isoformat()
        self.cursor.execute(
            'INSERT INTO chat_sessions (title, created_at, updated_at) VALUES (?, ?, ?)',
            ('Сессия ' + datetime.now().strftime("%d.%m.%Y %H:%M"), current_time, current_time)
        )
        self.current_session_id = self.cursor.lastrowid
        self.conn.commit()

    def save_message(self, role, content, message_type="text"):
        """Сохранение сообщения в базу данных"""
        timestamp = datetime.now().isoformat()
        self.cursor.execute(
            'INSERT INTO chat_history (timestamp, role, content, message_type) VALUES (?, ?, ?, ?)',
            (timestamp, role, content, message_type)
        )
        self.conn.commit()

        # Обновление времени сессии
        self.cursor.execute(
            'UPDATE chat_sessions SET updated_at = ? WHERE id = ?',
            (timestamp, self.current_session_id)
        )
        self.conn.commit()

    def load_chat_history(self):
        """Загрузка истории чата из базы данных"""
        self.cursor.execute('''
            SELECT role, content, message_type, timestamp 
            FROM chat_history 
            ORDER BY timestamp ASC
        ''')
        return self.cursor.fetchall()

    def clear_chat_history(self):
        """Очистка истории чата"""
        self.cursor.execute('DELETE FROM chat_history')
        self.conn.commit()
        self.chat_display.config(state='normal')
        self.chat_display.delete('1.0', tk.END)
        self.chat_display.config(state='disabled')

    def setup_styles(self):
        """Настройка стилей для темной темы PyCharm"""
        self.style = ttk.Style()
        self.style.theme_use('clam')

        # Конфигурация стилей
        self.style.configure('TFrame', background=self.colors['bg'])
        self.style.configure('TButton',
                             background=self.colors['secondary'],
                             foreground=self.colors['text'],
                             borderwidth=0,
                             focuscolor='none')
        self.style.map('TButton',
                       background=[('active', self.colors['accent']),
                                   ('pressed', self.colors['accent'])])

        self.style.configure('TLabel',
                             background=self.colors['bg'],
                             foreground=self.colors['text'])

        self.style.configure('TEntry',
                             fieldbackground=self.colors['card_bg'],
                             foreground=self.colors['text'],
                             borderwidth=0)

    def create_widgets(self):
        """Создание всех элементов интерфейса"""
        self.create_header()
        self.create_chat_tab()
        self.create_status_bar()

    def create_header(self):
        """Создание верхней панели с возможностью перемещения"""
        header_frame = tk.Frame(self.root, bg=self.colors['bg'], height=40)
        header_frame.pack(fill=tk.X, padx=0, pady=0)
        header_frame.pack_propagate(False)

        # Привязываем события для перемещения к заголовку
        header_frame.bind('<Button-1>', self.start_move)
        header_frame.bind('<B1-Motion>', self.on_move)

        # Заголовок
        title_label = tk.Label(header_frame,
                               text="👻",
                               bg=self.colors['bg'],
                               fg=self.colors['text'],
                               font=('Arial', 12, 'bold'))
        title_label.pack(side=tk.LEFT, padx=10)
        title_label.bind('<Button-1>', self.start_move)
        title_label.bind('<B1-Motion>', self.on_move)

        # Кнопки управления
        control_frame = tk.Frame(header_frame, bg=self.colors['bg'])
        control_frame.pack(side=tk.RIGHT, padx=5)

        # Кнопка прозрачности
        transparency_btn = tk.Button(control_frame,
                                     text="🔍",
                                     bg=self.colors['secondary'],
                                     fg=self.colors['text'],
                                     font=('Arial', 10),
                                     command=self.toggle_transparency_menu,
                                     width=3,
                                     relief='flat')
        transparency_btn.pack(side=tk.LEFT, padx=2)

        # Кнопка закрытия
        close_btn = tk.Button(control_frame,
                              text="✕",
                              bg=self.colors['bg'],
                              fg=self.colors['text'],
                              font=('Arial', 10, 'bold'),
                              width=3,
                              command=self.cleanup_and_exit,
                              relief='flat')
        close_btn.pack(side=tk.LEFT, padx=2)

    def create_chat_tab(self):
        """Создание вкладки чата с историей"""
        self.chat_frame = tk.Frame(self.root, bg=self.colors['bg'])
        self.chat_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Панель управления чатом
        chat_control_frame = tk.Frame(self.chat_frame, bg=self.colors['bg'])
        chat_control_frame.pack(fill=tk.X, pady=(0, 10))

        # clear_chat_btn = tk.Button(chat_control_frame,
        #                            text="🗑️ Очистить историю",
        #                            bg=self.colors['secondary'],
        #                            fg=self.colors['text'],
        #                            font=('Arial', 9),
        #                            command=self.clear_chat_history,
        #                            relief='flat')
        # clear_chat_btn.pack(side=tk.LEFT, padx=(0, 10))

        # export_btn = tk.Button(chat_control_frame,
        #                        text="📤 Экспорт чата",
        #                        bg=self.colors['secondary'],
        #                        fg=self.colors['text'],
        #                        font=('Arial', 9),
        #                        command=self.export_chat,
        #                        relief='flat')
        # export_btn.pack(side=tk.LEFT)

        # Область отображения чата
        chat_display_frame = tk.Frame(self.chat_frame, bg=self.colors['bg'])
        chat_display_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Создаем Text виджет без скроллбара
        self.chat_display = tk.Text(chat_display_frame,
                                    bg=self.colors['card_bg'],
                                    fg=self.colors['text'],
                                    insertbackground=self.colors['text'],
                                    font=('Consolas', 10),
                                    wrap=tk.WORD,
                                    relief='flat',
                                    padx=15,
                                    pady=15,
                                    borderwidth=0,
                                    highlightthickness=0)
        self.chat_display.pack(fill=tk.BOTH, expand=True)
        self.chat_display.config(state='disabled')

        # Область ввода сообщения
        input_frame = tk.Frame(self.chat_frame, bg=self.colors['bg'])
        input_frame.pack(fill=tk.X)

        # Создаем Text виджет для ввода без скроллбара
        self.chat_input = tk.Text(input_frame,
                                  height=4,
                                  bg=self.colors['card_bg'],
                                  fg=self.colors['text'],
                                  insertbackground=self.colors['text'],
                                  font=('Consolas', 10),
                                  wrap=tk.WORD,
                                  relief='flat',
                                  padx=10,
                                  pady=10,
                                  borderwidth=0,
                                  highlightthickness=0)
        self.chat_input.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        send_btn = tk.Button(input_frame,
                             text="📤\nОтправить",
                             bg=self.colors['accent'],
                             fg=self.colors['text'],
                             font=('Arial', 9, 'bold'),
                             command=self.send_chat_message,
                             width=8,
                             height=4,
                             relief='flat')
        send_btn.pack(side=tk.RIGHT)

    def create_status_bar(self):
        """Создание строки состояния"""
        self.status_frame = tk.Frame(self.root, bg=self.colors['secondary'], height=25)
        self.status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        self.status_frame.pack_propagate(False)

        self.status_label = tk.Label(self.status_frame,
                                     text="Готов к работе | Сообщения: 0",
                                     bg=self.colors['secondary'],
                                     fg=self.colors['text'],
                                     font=('Arial', 8))
        self.status_label.pack(side=tk.LEFT, padx=10)

        # Привязываем события для перемещения к статус бару
        self.status_frame.bind('<Button-1>', self.start_move)
        self.status_frame.bind('<B1-Motion>', self.on_move)
        self.status_label.bind('<Button-1>', self.start_move)
        self.status_label.bind('<B1-Motion>', self.on_move)

    def setup_bindings(self):
        """Настройка горячих клавиш"""
        self.root.bind('<Control-Return>', lambda e: self.send_chat_message())
        self.root.bind('<Control-plus>', lambda e: self.increase_transparency())
        self.root.bind('<Control-minus>', lambda e: self.decrease_transparency())
        self.root.bind('<Control-s>', lambda e: self.send_chat_message())

        # Привязываем колесо мыши к прокрутке
        self.chat_display.bind('<MouseWheel>', self.on_mousewheel)
        self.chat_input.bind('<MouseWheel>', self.on_mousewheel)

    def on_mousewheel(self, event):
        """Обработка прокрутки колесом мыши"""
        if event.delta:
            if event.widget == self.chat_display:
                self.chat_display.yview_scroll(int(-1 * (event.delta / 120)), "units")
            elif event.widget == self.chat_input:
                self.chat_input.yview_scroll(int(-1 * (event.delta / 120)), "units")

    # Функции для перемещения окна
    def start_move(self, event):
        """Начало перемещения окна"""
        self.x = event.x
        self.y = event.y

    def on_move(self, event):
        """Перемещение окна"""
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{x}+{y}")

    def send_chat_message(self):
        """Отправка сообщения в чат"""
        message = self.chat_input.get('1.0', tk.END).strip()
        if not message:
            return

        # Сохраняем сообщение пользователя
        self.save_message("user", message)
        self.display_chat_message("user", message)

        # Очищаем поле ввода
        self.chat_input.delete('1.0', tk.END)

        # Показываем статус "печатает"
        self.show_status("Ассистент печатает...", "accent")

        # Отправляем запрос в отдельном потоке
        threading.Thread(target=self.process_chat_message, args=(message,), daemon=True).start()

    def process_chat_message(self, message):
        """Обработка сообщения в отдельном потоке"""
        try:
            # Получаем историю диалога для контекста
            history = self.load_chat_history()
            messages = []

            # Добавляем системный промпт
            messages.append({
                "role": "system",
                "content": """Ты эксперт по ЕГЭ по информатике. Помогай решать задачи, объясняй концепции и давай подробные объяснения. Будь дружелюбным и полезным ассистентом."""
            })

            # Добавляем историю диалога
            for role, content, msg_type, timestamp in history[-10:]:  # Последние 10 сообщений
                messages.append({"role": role, "content": content})

            # Добавляем текущее сообщение
            messages.append({"role": "user", "content": message})

            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=messages,
                stream=False
            )

            assistant_response = response.choices[0].message.content

            # Сохраняем и отображаем ответ
            self.save_message("assistant", assistant_response)
            self.root.after(0, self.display_chat_message, "assistant", assistant_response)
            self.root.after(0, self.show_status, "Сообщение отправлено", "success")

        except Exception as e:
            error_msg = f"Ошибка: {str(e)}"
            self.save_message("system", error_msg)
            self.root.after(0, self.display_chat_message, "system", error_msg)
            self.root.after(0, self.show_status, "Ошибка при отправке", "error")

    def display_chat_message(self, role, content):
        """Отображение сообщения в чате"""
        self.chat_display.config(state='normal')

        # Настройка цвета в зависимости от роли
        if role == "user":
            bg_color = self.colors['user_msg']
            prefix = "👤 Вы: "
        elif role == "assistant":
            bg_color = self.colors['assistant_msg']
            prefix = "🤖 Ассистент: "
        else:
            bg_color = self.colors['system_msg']
            prefix = "⚙️ Система: "

        # Добавляем сообщение
        self.chat_display.insert(tk.END, prefix, 'bold')
        self.chat_display.insert(tk.END, f"{content}\n\n")

        # Прокручиваем вниз
        self.chat_display.see(tk.END)
        self.chat_display.config(state='disabled')

        # Обновляем счетчик сообщений
        self.update_message_count()

    def update_message_count(self):
        """Обновление счетчика сообщений в статусе"""
        count = len([msg for msg in self.load_chat_history() if msg[0] in ['user', 'assistant']])
        self.status_label.config(text=f"Готов к работе | Сообщения: {count}")

    def export_chat(self):
        """Экспорт истории чата в файл"""
        try:
            filename = f"chat_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("Экспорт истории чата - Ассистент ЕГЭ\n")
                f.write("=" * 50 + "\n\n")

                for role, content, msg_type, timestamp in self.load_chat_history():
                    time_str = datetime.fromisoformat(timestamp).strftime("%d.%m.%Y %H:%M")
                    role_str = "Вы" if role == "user" else "Ассистент" if role == "assistant" else "Система"
                    f.write(f"[{time_str}] {role_str}:\n{content}\n{'=' * 30}\n\n")

            self.show_status(f"Чат экспортирован в {filename}", "success")
        except Exception as e:
            self.show_status(f"Ошибка экспорта: {e}", "error")

    def toggle_transparency_menu(self):
        """Меню настройки прозрачности"""
        menu = tk.Menu(self.root, tearoff=0, bg=self.colors['card_bg'], fg=self.colors['text'])
        menu.add_command(label="Увеличить прозрачность (Ctrl+-)", command=self.decrease_transparency)
        menu.add_command(label="Уменьшить прозрачность (Ctrl++)", command=self.increase_transparency)
        menu.add_separator()

        for value in [100, 90, 80, 70, 60, 50, 40, 30]:
            menu.add_command(label=f"{value}%",
                             command=lambda v=value: self.set_transparency(v / 100))

        # Показываем меню рядом с кнопкой
        menu.post(self.root.winfo_pointerx(), self.root.winfo_pointery())

    def increase_transparency(self):
        """Уменьшение прозрачности (окно более непрозрачное)"""
        if self.current_alpha < 1.0:
            self.current_alpha = min(1.0, self.current_alpha + 0.1)
            self.root.attributes('-alpha', self.current_alpha)
            self.update_status_transparency()

    def decrease_transparency(self):
        """Увеличение прозрачности (окно более прозрачное)"""
        if self.current_alpha > 0.1:
            self.current_alpha = max(0.1, self.current_alpha - 0.1)
            self.root.attributes('-alpha', self.current_alpha)
            self.update_status_transparency()

    def set_transparency(self, value):
        """Установка конкретного значения прозрачности"""
        self.current_alpha = max(0.1, min(1.0, value))
        self.root.attributes('-alpha', self.current_alpha)
        self.update_status_transparency()

    def update_status_transparency(self):
        """Обновление отображения прозрачности в статусе"""
        for widget in self.status_frame.winfo_children():
            if "Прозрачность" in widget.cget('text'):
                widget.config(text=f"Прозрачность: {int(self.current_alpha * 100)}%")

    def show_status(self, message, type_="normal"):
        """Показ сообщения в статусе"""
        color_map = {
            "normal": self.colors['text'],
            "success": self.colors['success'],
            "warning": self.colors['warning'],
            "error": self.colors['error'],
            "accent": self.colors['accent']
        }
        self.status_label.config(text=message, fg=color_map.get(type_, self.colors['text']))

    def cleanup_and_exit(self):
        """Очистка ресурсов и выход"""
        if hasattr(self, 'conn'):
            self.conn.close()
        self.root.quit()


if __name__ == "__main__":
    root = tk.Tk()
    app = EGEAssistant(root)
    root.mainloop()