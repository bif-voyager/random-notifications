import tkinter as tk
from tkinter import ttk, messagebox
import uuid
from notification_manager import NotificationManager


class ReminderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Уведомлялка")
        self.root.geometry("600x500")
        
        self.manager = NotificationManager()
        self.manager.load_reminders()
        self.manager.start_background_thread()
        
        self.create_widgets()
        self.refresh_reminder_list()
        
        # Обработка закрытия окна
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def create_widgets(self):
        # Фрейм для добавления напоминания
        add_frame = ttk.LabelFrame(self.root, text="Добавить напоминание", padding=10)
        add_frame.pack(fill="x", padx=10, pady=10)
        
        # Текст уведомления
        ttk.Label(add_frame, text="Текст уведомления:").grid(row=0, column=0, sticky="w", pady=5)
        self.text_entry = ttk.Entry(add_frame, width=50)
        self.text_entry.grid(row=0, column=1, columnspan=3, pady=5, padx=5)
        
        # Частота
        ttk.Label(add_frame, text="Раз в день:").grid(row=1, column=0, sticky="w", pady=5)
        self.frequency_spinbox = ttk.Spinbox(add_frame, from_=1, to=20, width=10)
        self.frequency_spinbox.set(3)
        self.frequency_spinbox.grid(row=1, column=1, sticky="w", pady=5, padx=5)
        
        # Случайное время
        self.is_random_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(add_frame, text="Случайное время", variable=self.is_random_var).grid(
            row=1, column=2, columnspan=2, sticky="w", pady=5
        )
        
        # Время начала и конца
        ttk.Label(add_frame, text="Время работы:").grid(row=2, column=0, sticky="w", pady=5)
        
        time_frame = ttk.Frame(add_frame)
        time_frame.grid(row=2, column=1, columnspan=3, sticky="w", pady=5, padx=5)
        
        ttk.Label(time_frame, text="с").pack(side="left", padx=2)
        self.start_hour_spinbox = ttk.Spinbox(time_frame, from_=0, to=23, width=5)
        self.start_hour_spinbox.set(8)
        self.start_hour_spinbox.pack(side="left", padx=2)
        
        ttk.Label(time_frame, text="до").pack(side="left", padx=2)
        self.end_hour_spinbox = ttk.Spinbox(time_frame, from_=0, to=23, width=5)
        self.end_hour_spinbox.set(22)
        self.end_hour_spinbox.pack(side="left", padx=2)
        
        ttk.Label(time_frame, text="часов").pack(side="left", padx=2)
        
        # Кнопка добавить
        ttk.Button(add_frame, text="➕ Добавить напоминание", command=self.add_reminder).grid(
            row=3, column=0, columnspan=4, pady=10
        )
        
        # Фрейм со списком напоминаний
        list_frame = ttk.LabelFrame(self.root, text="Активные напоминания", padding=10)
        list_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Treeview для отображения напоминаний
        columns = ("text", "frequency", "type", "times")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=10)
        
        self.tree.heading("text", text="Текст")
        self.tree.heading("frequency", text="Раз/день")
        self.tree.heading("type", text="Тип")
        self.tree.heading("times", text="Время")
        
        self.tree.column("text", width=250)
        self.tree.column("frequency", width=70)
        self.tree.column("type", width=100)
        self.tree.column("times", width=150)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Кнопки управления
        button_frame = ttk.Frame(self.root)
        button_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Button(button_frame, text="🗑️ Удалить", command=self.delete_reminder).pack(side="left", padx=5)
        ttk.Button(button_frame, text="⏸️ Выкл/Вкл", command=self.toggle_reminder).pack(side="left", padx=5)
        ttk.Button(button_frame, text="🔄 Обновить", command=self.refresh_reminder_list).pack(side="left", padx=5)
        
    def add_reminder(self):
        text = self.text_entry.get().strip()
        if not text:
            messagebox.showwarning("Внимание", "Введите текст уведомления!")
            return
            
        try:
            frequency = int(self.frequency_spinbox.get())
            start_hour = int(self.start_hour_spinbox.get())
            end_hour = int(self.end_hour_spinbox.get())
            
            if start_hour >= end_hour:
                messagebox.showwarning("Внимание", "Время начала должно быть меньше времени окончания!")
                return
                
            if frequency <= 0:
                messagebox.showwarning("Внимание", "Частота должна быть больше 0!")
                return
                
        except ValueError:
            messagebox.showwarning("Внимание", "Проверьте введенные числа!")
            return
            
        is_random = self.is_random_var.get()
        reminder_id = str(uuid.uuid4())
        
        self.manager.add_reminder(
            reminder_id=reminder_id,
            text=text,
            frequency=frequency,
            is_random=is_random,
            start_hour=start_hour,
            end_hour=end_hour
        )
        
        self.text_entry.delete(0, tk.END)
        self.refresh_reminder_list()
        messagebox.showinfo("Успех", "Напоминание добавлено!")
        
    def delete_reminder(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите напоминание для удаления!")
            return
            
        item = self.tree.item(selected[0])
        reminder_id = item['values'][0] if item['values'] else None
        
        # Найти reminder_id по тексту (так как мы не отображаем ID)
        for reminder in self.manager.reminders:
            if reminder['text'] == item['values'][0]:
                reminder_id = reminder['id']
                break
                
        if reminder_id:
            self.manager.remove_reminder(reminder_id)
            self.refresh_reminder_list()
            messagebox.showinfo("Успех", "Напоминание удалено!")
            
    def toggle_reminder(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите напоминание!")
            return
            
        item = self.tree.item(selected[0])
        
        # Найти reminder_id по тексту
        for reminder in self.manager.reminders:
            if reminder['text'] == item['values'][0]:
                reminder_id = reminder['id']
                new_state = not reminder['enabled']
                self.manager.toggle_reminder(reminder_id, new_state)
                self.refresh_reminder_list()
                status = "включено" if new_state else "выключено"
                messagebox.showinfo("Успех", f"Напоминание {status}!")
                break
                
    def refresh_reminder_list(self):
        # Очистить список
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # Заполнить список
        for reminder in self.manager.reminders:
            text = reminder['text']
            if not reminder['enabled']:
                text = f"[ВЫКЛ] {text}"
                
            frequency = reminder['frequency']
            reminder_type = "Случайно" if reminder['is_random'] else "Равномерно"
            
            times = self.manager.get_next_notification_times(reminder['id'])
            times_str = ", ".join(times[:3])  # Показать первые 3 времени
            if len(times) > 3:
                times_str += "..."
                
            self.tree.insert("", "end", values=(text, frequency, reminder_type, times_str))
            
    def on_closing(self):
        self.manager.stop()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = ReminderApp(root)
    root.mainloop()
