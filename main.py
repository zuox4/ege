import tkinter as tk
from tkinter import scrolledtext
import threading
from openai import OpenAI


class UltraTransparentAssistant:
    def __init__(self, root):
        self.title_bar = None
        self.root = root
        self.root.title("SHADOW")
        self.root.geometry("700x300")

        # Максимальная прозрачность для Windows
        self.current_alpha = 0.05
        self.root.attributes('-alpha', self.current_alpha)

        # Прозрачный фон окна
        self.root.configure(bg='#2b2b2b')

        # Установка темного заголовка для Windows
        try:
            from ctypes import windll, byref, sizeof, c_int
            # Получаем HWND окна
            HWND = windll.user32.GetParent(root.winfo_id())
            # Устанавливаем темный заголовок (DWMWA_USE_IMMERSIVE_DARK_MODE = 20)
            windll.dwmapi.DwmSetWindowAttribute(HWND, 20, byref(c_int(1)), sizeof(c_int))
        except:
            pass  # Если не Windows, пропускаем

        self.client = OpenAI(
            api_key='sk-cfc4609bed994c85bc26d8c29d433030',
            base_url="https://api.deepseek.com"
        )

        self.create_ui()
        self.setup_bindings()

    def create_ui(self):
        # Минималистичные полупрозрачные цвета
        dark_bg = '#2b2b2b'
        card_bg = '#2b2b2b'
        text_color = '#fffff3'
        accent = '#2b2b2b'

        # Создаем кастомный заголовок
        self.title_bar = tk.Frame(self.root, bg=dark_bg, height=30)
        self.title_bar.pack(fill=tk.X, side=tk.TOP)

        # Название программы в заголовке
        title_label = tk.Label(self.title_bar,
                               text="👻",
                               bg=dark_bg,
                               fg=text_color,
                               font=('Arial', 10, 'bold'))
        title_label.pack(side=tk.LEFT, padx=10, pady=5)

        # Кнопки управления окном (свернуть/закрыть)
        controls_frame = tk.Frame(self.title_bar, bg=dark_bg)
        controls_frame.pack(side=tk.RIGHT, padx=5)

        # Кнопка свернуть
        minimize_btn = tk.Button(controls_frame,
                                 text="─",
                                 bg=dark_bg,
                                 fg=text_color,
                                 font=('Arial', 10),
                                 borderwidth=0,
                                 command=self.root.iconify)
        minimize_btn.pack(side=tk.LEFT, padx=2)

        # Кнопка закрыть
        close_btn = tk.Button(controls_frame,
                              text="×",
                              bg=dark_bg,
                              fg=text_color,
                              font=('Arial', 12),
                              borderwidth=0,
                              command=self.root.quit)
        close_btn.pack(side=tk.LEFT, padx=2)

        # Минимальные отступы для большего эффекта прозрачности
        main_frame = tk.Frame(self.root, bg=dark_bg, padx=10, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Поле ввода БЕЗ скроллбара
        self.input_text = tk.Text(main_frame,
                                  height=3,
                                  bg=card_bg,
                                  fg=text_color,
                                  insertbackground=text_color,
                                  font=('Arial', 9),
                                  wrap=tk.WORD,
                                  relief='flat',
                                  borderwidth=1)
        self.input_text.pack(fill=tk.X, pady=5)

        # Кнопки
        btn_frame = tk.Frame(main_frame, bg=dark_bg)
        btn_frame.pack(fill=tk.X, pady=5)

        self.solve_btn = tk.Button(btn_frame,
                                   text="Решить",
                                   bg=accent,
                                   fg=text_color,
                                   font=('Arial', 8),
                                   command=self.solve_problem)
        self.solve_btn.pack(side=tk.LEFT, padx=(0, 5))

        tk.Button(btn_frame,
                  text="Очистить",
                  bg='#555555',
                  fg=text_color,
                  font=('Arial', 8),
                  command=self.clear_all).pack(side=tk.LEFT)

        # Поле вывода БЕЗ скроллбара
        self.output_text = tk.Text(main_frame,
                                   bg=card_bg,
                                   fg=text_color,
                                   insertbackground=text_color,
                                   font=('Arial', 9),
                                   wrap=tk.WORD,
                                   relief='flat',
                                   borderwidth=1)
        self.output_text.pack(fill=tk.BOTH, expand=True)

        # Статус
        self.status = tk.Label(main_frame,
                               text=f"Прозрачность: {int(self.current_alpha * 100)}%",
                               bg=dark_bg,
                               fg='#888888',
                               font=('Arial', 7))
        self.status.pack(fill=tk.X, pady=(5, 0))

        self.input_text.focus()

    def setup_bindings(self):
        self.root.bind('<Control-Return>', lambda e: self.solve_problem())
        self.root.bind('<Control-plus>', lambda e: self.more_transparent())
        self.root.bind('<Control-minus>', lambda e: self.less_transparent())

        # Добавляем скроллинг колесиком мыши
        self.input_text.bind('<MouseWheel>', self._scroll_text)
        self.output_text.bind('<MouseWheel>', self._scroll_text)

        # Скроллинг на тачпаде
        self.input_text.bind('<Button-4>', self._scroll_text)
        self.input_text.bind('<Button-5>', self._scroll_text)
        self.output_text.bind('<Button-4>', self._scroll_text)
        self.output_text.bind('<Button-5>', self._scroll_text)

        # Перетаскивание окна за кастомный заголовок
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

    def _scroll_text(self, event):
        """Обработка скроллинга для текстовых полей"""
        if event.delta:
            # Для Windows/Mac
            lines = -1 if event.delta < 0 else 1
        else:
            # Для Linux
            lines = -1 if event.num == 5 else 1

        event.widget.yview_scroll(lines, "units")

    def more_transparent(self):
        if self.current_alpha > 0.05:
            self.current_alpha -= 0.05
            self.root.attributes('-alpha', self.current_alpha)
            self.status.config(text=f"Прозрачность: {int(self.current_alpha * 100)}%")

    def less_transparent(self):
        if self.current_alpha < 1.0:
            self.current_alpha += 0.05
            self.root.attributes('-alpha', self.current_alpha)
            self.status.config(text=f"Прозрачность: {int(self.current_alpha * 100)}%")

    def solve_problem(self, event=None):
        problem = self.input_text.get('1.0', tk.END).strip()
        if not problem:
            return

        self.solve_btn.config(state='disabled')
        self.status.config(text="Решаем...")

        threading.Thread(target=self.solve_thread, args=(problem,), daemon=True).start()

    def solve_thread(self, problem):
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": f"Реши задачу ЕГЭ по информатике: {problem}"}]
            )
            result = response.choices[0].message.content
            self.root.after(0, self.show_result, result)
        except Exception as e:
            self.root.after(0, self.show_result, f"Ошибка: {e}")

    def show_result(self, text):
        self.solve_btn.config(state='normal')
        self.output_text.delete('1.0', tk.END)
        self.output_text.insert('1.0', text)
        self.status.config(text=f"Прозрачность: {int(self.current_alpha * 100)}%")

    def clear_all(self):
        self.input_text.delete('1.0', tk.END)
        self.output_text.delete('1.0', tk.END)
        self.input_text.focus()


if __name__ == "__main__":
    root = tk.Tk()
    app = UltraTransparentAssistant(root)
    root.mainloop()