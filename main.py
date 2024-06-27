import customtkinter as ctk
import sqlite3
from tkinter import messagebox
from tkinter import ttk
import datetime

# Устанавливаем тему и внешний вид
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

# Основное окно приложения
app = ctk.CTk()
app.title("Система управления задачами")
app.geometry("902x313")

# Подключаемся к базе данных и создаем таблицы
conn = sqlite3.connect('task_management.db')
cursor = conn.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS users
(id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, role TEXT)
''')
cursor.execute('''
CREATE TABLE IF NOT EXISTS tasks
(id INTEGER PRIMARY KEY, title TEXT, description TEXT, reason TEXT, 
status TEXT DEFAULT 'Новая', priority TEXT, assigned_to TEXT,
created_by TEXT, created_at DATETIME)
''')
conn.commit()

def show_frame(frame):
    frame.tkraise()

def login():
    username = username_entry.get()
    password = password_entry.get()
    
    cursor.execute("SELECT role FROM users WHERE username=? AND password=?", (username, password))
    result = cursor.fetchone()
    
    if result:
        role = result[0]
        if role == 'client':
            client_frame.tkraise()
        elif role == 'manager':
            admin_frame.tkraise()
            load_tasks()
        elif role == 'worker':
            worker_frame.tkraise()
            load_worker_tasks(username)
    else:
        messagebox.showerror("Ошибка", "Неверное имя пользователя или пароль")

def submit_task():
    title = title_entry.get()
    description = description_entry.get()
    reason = reason_entry.get()
    created_by = client_welcome_label.cget("text").split(", ")[1][:-1]
    created_at = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    
    cursor.execute('''
    INSERT INTO tasks (title, description, reason, created_by, created_at)
    VALUES (?, ?, ?, ?, ?)
    ''', (title, description, reason, created_by, created_at))
    conn.commit()
    
    messagebox.showinfo("Успех", "Заявка отправлена!")
    title_entry.delete(0, ctk.END)
    description_entry.delete(0, ctk.END)
    reason_entry.delete(0, ctk.END)

def load_tasks():
    for row in tree.get_children():
        tree.delete(row)
    cursor.execute("SELECT * FROM tasks")
    for row in cursor.fetchall():
        tree.insert('', 'end', values=row)

def on_double_click(event):
    item = tree.selection()[0]
    values = tree.item(item, "values")
    edit_task(values)

def edit_task(values):
    edit_window = ctk.CTkToplevel(app)
    edit_window.title("Редактировать")
    edit_window.geometry("400x500")

    def save_changes():
        new_title = title_entry.get()
        new_description = description_entry.get()
        new_reason = reason_entry.get()
        new_priority = priority_option.get()
        new_assigned_to = assigned_to_option.get()
        new_status = "Назначено" if new_assigned_to and new_assigned_to != values[6] else values[4]

        cursor.execute('''
        UPDATE tasks SET title=?, description=?, reason=?, status=?, priority=?, assigned_to=?
        WHERE id=?
        ''', (new_title, new_description, new_reason, new_status, new_priority, new_assigned_to, values[0]))
        conn.commit()
        
        load_tasks()
        edit_window.destroy()

    fields = ['Заголовок', 'Описание', 'Причина', 'Приоритет', 'Назначено']
    title_label = ctk.CTkLabel(edit_window, text="Заголовок")
    title_label.pack()
    title_entry = ctk.CTkEntry(edit_window)
    title_entry.insert(0, values[1])
    title_entry.pack()
    
    description_label = ctk.CTkLabel(edit_window, text="Описание")
    description_label.pack()
    description_entry = ctk.CTkEntry(edit_window)
    description_entry.insert(0, values[2])
    description_entry.pack()
    
    reason_label = ctk.CTkLabel(edit_window, text="Причина")
    reason_label.pack()
    reason_entry = ctk.CTkEntry(edit_window)
    reason_entry.insert(0, values[3])
    reason_entry.pack()
    
    priority_label = ctk.CTkLabel(edit_window, text="Приоритет")
    priority_label.pack()
    priority_option = ctk.CTkOptionMenu(edit_window, values=["Низкий", "Средний", "Высокий"])
    priority_option.set(values[5])
    priority_option.pack()
    
    assigned_to_label = ctk.CTkLabel(edit_window, text="Назначено")
    assigned_to_label.pack()
    assigned_to_option = ctk.CTkOptionMenu(edit_window, values=[""] + get_workers())
    assigned_to_option.set(values[6])
    assigned_to_option.pack()

    save_button = ctk.CTkButton(edit_window, text="Сохранить", command=save_changes)
    save_button.pack(pady=10)

def get_workers():
    cursor.execute("SELECT username FROM users WHERE role='worker'")
    return [row[0] for row in cursor.fetchall()]

def load_worker_tasks(username):
    for row in worker_tree.get_children():
        worker_tree.delete(row)
    cursor.execute("SELECT * FROM tasks WHERE assigned_to=?", (username,))
    for row in cursor.fetchall():
        worker_tree.insert('', 'end', values=row)

def worker_on_double_click(event):
    item = worker_tree.selection()[0]
    values = worker_tree.item(item, "values")
    worker_edit_task(values)

def worker_edit_task(values):
    edit_window = ctk.CTkToplevel(app)
    edit_window.title("Редактировать")
    edit_window.geometry("400x400")

    def save_changes():
        new_reason = reason_entry.get()
        cursor.execute('UPDATE tasks SET reason=? WHERE id=?', (new_reason, values[0]))
        conn.commit()
        load_worker_tasks(values[6])
        edit_window.destroy()

    def change_status(new_status):
        cursor.execute("UPDATE tasks SET status=? WHERE id=?", (new_status, values[0]))
        conn.commit()
        load_worker_tasks(values[6])
        edit_window.destroy()

    reason_label = ctk.CTkLabel(edit_window, text="Причина поломки")
    reason_label.pack()
    reason_entry = ctk.CTkEntry(edit_window)
    reason_entry.insert(0, values[3])
    reason_entry.pack()

    save_button = ctk.CTkButton(edit_window, text="Сохранить изменения", command=save_changes)
    save_button.pack(pady=5)
    start_button = ctk.CTkButton(edit_window, text="Начать работу", command=lambda: change_status("В работе"))
    start_button.pack(pady=5)
    finish_button = ctk.CTkButton(edit_window, text="Завершить работу", command=lambda: change_status("Выполнено"))
    finish_button.pack(pady=5)

login_frame = ctk.CTkFrame(app)
client_frame = ctk.CTkFrame(app)
admin_frame = ctk.CTkFrame(app)
worker_frame = ctk.CTkFrame(app)

for frame in (login_frame, client_frame, admin_frame, worker_frame):
    frame.grid(row=0, column=0, sticky='nsew')

login_frame_content = ctk.CTkFrame(login_frame)
login_frame_content.pack(expand=True, padx=20, pady=20, fill="both")

ctk.CTkLabel(login_frame_content, text="Авторизация", font=("Roboto", 24)).pack(pady=12)

username_entry = ctk.CTkEntry(login_frame_content, placeholder_text="Имя пользователя", justify="center")
username_entry.pack(pady=12)

password_entry = ctk.CTkEntry(login_frame_content, placeholder_text="Пароль", show="*", justify="center")
password_entry.pack(pady=12)

ctk.CTkButton(login_frame_content, text="Войти", command=login).pack(pady=12)

client_welcome_label = ctk.CTkLabel(client_frame, text="", font=("Roboto", 24))
client_welcome_label.pack(pady=10)

title_label = ctk.CTkLabel(client_frame, text="Заголовок")
title_label.pack()
title_entry = ctk.CTkEntry(client_frame)
title_entry.pack()

description_label = ctk.CTkLabel(client_frame, text="Описание")
description_label.pack()
description_entry = ctk.CTkEntry(client_frame)
description_entry.pack()

reason_label = ctk.CTkLabel(client_frame, text="Причина")
reason_label.pack()
reason_entry = ctk.CTkEntry(client_frame)
reason_entry.pack()

ctk.CTkButton(client_frame, text="Отправить", command=submit_task).pack(pady=10)
ctk.CTkButton(client_frame, text="Выйти", command=lambda: show_frame(login_frame)).pack(pady=10)

columns = ('ID', 'Заголовок', 'Описание', 'Причина', 'Статус', 'Приоритет', 'Работник', 'Клиент', 'Время создания')
tree = ttk.Treeview(admin_frame, columns=columns, show='headings')
for col in columns:
    tree.heading(col, text=col)
    tree.column(col, width=100)
tree.pack(fill="both", expand=True)
tree.bind('<Double-1>', on_double_click)

ctk.CTkButton(admin_frame, text="Выйти", command=lambda: show_frame(login_frame)).pack(pady=10)

worker_tree = ttk.Treeview(worker_frame, columns=columns, show='headings')
for col in columns:
    worker_tree.heading(col, text=col)
    worker_tree.column(col, width=100)
worker_tree.pack(fill="both", expand=True)
worker_tree.bind('<Double-1>', worker_on_double_click)

ctk.CTkButton(worker_frame, text="Выйти", command=lambda: show_frame(login_frame)).pack(pady=10)

show_frame(login_frame)
app.mainloop()
