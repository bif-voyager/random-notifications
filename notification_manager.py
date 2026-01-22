import random
import datetime
import threading
import time
from winotify import Notification, audio
import json
import os


class NotificationManager:
    def __init__(self):
        self.reminders = []
        self.running = True
        self.scheduled_times = {}
        self.data_file = "reminders.json"
        
    def add_reminder(self, reminder_id, text, frequency, is_random, start_hour=8, end_hour=22):
        """
        Добавить напоминание
        :param reminder_id: уникальный ID напоминания
        :param text: текст уведомления
        :param frequency: сколько раз в день
        :param is_random: случайное время или равномерное
        :param start_hour: начало рабочего дня (час)
        :param end_hour: конец рабочего дня (час)
        """
        reminder = {
            'id': reminder_id,
            'text': text,
            'frequency': frequency,
            'is_random': is_random,
            'start_hour': start_hour,
            'end_hour': end_hour,
            'enabled': True
        }
        self.reminders.append(reminder)
        self._schedule_reminder(reminder)
        self.save_reminders()
        
    def remove_reminder(self, reminder_id):
        """Удалить напоминание"""
        self.reminders = [r for r in self.reminders if r['id'] != reminder_id]
        if reminder_id in self.scheduled_times:
            del self.scheduled_times[reminder_id]
        self.save_reminders()
        
    def toggle_reminder(self, reminder_id, enabled):
        """Включить/выключить напоминание"""
        for reminder in self.reminders:
            if reminder['id'] == reminder_id:
                reminder['enabled'] = enabled
                if enabled:
                    self._schedule_reminder(reminder)
                else:
                    if reminder_id in self.scheduled_times:
                        del self.scheduled_times[reminder_id]
        self.save_reminders()
                
    def _schedule_reminder(self, reminder):
        """Сгенерировать время для напоминания"""
        times = []
        start_hour = reminder['start_hour']
        end_hour = reminder['end_hour']
        frequency = reminder['frequency']
        
        if reminder['is_random']:
            # Случайное время
            for _ in range(frequency):
                hour = random.randint(start_hour, end_hour - 1)
                minute = random.randint(0, 59)
                times.append((hour, minute))
        else:
            # Равномерное распределение
            total_minutes = (end_hour - start_hour) * 60
            interval = total_minutes // frequency
            
            for i in range(frequency):
                minutes_from_start = interval * i + random.randint(0, interval // 2)
                hour = start_hour + minutes_from_start // 60
                minute = minutes_from_start % 60
                times.append((hour, minute))
        
        self.scheduled_times[reminder['id']] = times
        
    def _send_notification(self, text):
        """Отправить Windows уведомление"""
        try:
            toast = Notification(
                app_id="Уведомлялка",
                title="Напоминание!",
                msg=text,
                duration="short",
                icon=""
            )
            toast.set_audio(audio.Default, loop=False)
            toast.show()
        except Exception as e:
            print(f"Ошибка отправки уведомления: {e}")
            
    def check_and_notify(self):
        """Проверить и отправить уведомления (вызывается каждую минуту)"""
        now = datetime.datetime.now()
        current_hour = now.hour
        current_minute = now.minute
        
        print(f"[DEBUG] Проверка времени: {current_hour:02d}:{current_minute:02d}")
        
        for reminder in self.reminders:
            if not reminder['enabled']:
                continue
                
            reminder_id = reminder['id']
            if reminder_id not in self.scheduled_times:
                self._schedule_reminder(reminder)
                
            times = self.scheduled_times[reminder_id]
            print(f"[DEBUG] Напоминание '{reminder['text'][:30]}...' - запланировано: {times}")
            
            for scheduled_hour, scheduled_minute in times:
                if scheduled_hour == current_hour and scheduled_minute == current_minute:
                    print(f"[DEBUG] ✅ Отправка уведомления: {reminder['text']}")
                    self._send_notification(reminder['text'])
                    
        # Пересчитать расписание в начале нового дня
        if current_hour == 0 and current_minute == 0:
            for reminder in self.reminders:
                if reminder['enabled']:
                    self._schedule_reminder(reminder)
                    
    def start_background_thread(self):
        """Запустить фоновый поток для проверки уведомлений"""
        def run():
            while self.running:
                self.check_and_notify()
                time.sleep(60)  # Проверять каждую минуту
                
        thread = threading.Thread(target=run, daemon=True)
        thread.start()
        
    def stop(self):
        """Остановить фоновый поток"""
        self.running = False
        
    def save_reminders(self):
        """Сохранить напоминания в файл"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.reminders, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения: {e}")
            
    def load_reminders(self):
        """Загрузить напоминания из файла"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    self.reminders = json.load(f)
                    
                # Пересоздать расписание для всех напоминаний
                for reminder in self.reminders:
                    if reminder['enabled']:
                        self._schedule_reminder(reminder)
            except Exception as e:
                print(f"Ошибка загрузки: {e}")
                
    def get_next_notification_times(self, reminder_id):
        """Получить время следующих уведомлений для напоминания"""
        if reminder_id in self.scheduled_times:
            times = self.scheduled_times[reminder_id]
            return [f"{h:02d}:{m:02d}" for h, m in sorted(times)]
        return []
