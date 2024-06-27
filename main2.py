import tkinter as tk
from tkinter import ttk
import sqlite3
from tkinter import messagebox
import datetime

# Подключаемся к базе данных и создаем таблицы
conn = sqlite3.connect('database.db')
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

def login():
    username = username_entry.get()
    password = password_entry.get()
    
    cursor.execute("SELECT role FROM users WHERE username=? AND password=?", (username, password))
    result = cursor.fetchone()
    
    if result:
        role = result[0]
        if role == 'client':
            client_window()
        elif role == 'manager':
            admin_window()
        elif role == 'worker':
            worker_window(username)
    else:
        messagebox.showerror("Ошибка", "Неверное имя пользователя или пароль")

def client_window():
    client_window = tk.Toplevel(root)
    client_window.title("Клиент")
    client_window.geometry("400x300")

    client_welcome_label = tk.Label(client_window, text=f"Добро пожаловать, {username_entry.get()}!", font=("Arial", 14))
    client_welcome_label.pack(pady=10)

    title_label = tk.Label(client_window, text="Заголовок")
    title_label.pack()
    title_entry = tk.Entry(client_window)
    title_entry.pack()

    description_label = tk.Label(client_window, text="Описание")
    description_label.pack()
    description_entry = tk.Entry(client_window)
    description_entry.pack()

    reason_label = tk.Label(client_window, text="Причина")
    reason_label.pack()
    reason_entry = tk.Entry(client_window)
    reason_entry.pack()

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
        title_entry.delete(0, tk.END)
        description_entry.delete(0, tk.END)
        reason_entry.delete(0, tk.END)

    submit_button = tk.Button(client_window, text="Отправить", command=submit_task)
    submit_button.pack(pady=10)

def admin_window():
    admin_window = tk.Toplevel(root)
    admin_window.title("Администратор")
    admin_window.geometry("800x400")

    tree = ttk.Treeview(admin_window, columns=('ID', 'Заголовок', 'Описание', 'Причина', 'Статус', 'Приоритет', 'Работник', 'Клиент', 'Время'), show='headings')
    for col in ('ID', 'Заголовок', 'Описание', 'Причина', 'Статус', 'Приоритет', 'Работник', 'Клиент', 'Время'):
        tree.heading(col, text=col)
        tree.column(col, width=100)
    tree.pack(fill="both", expand=True)

    def load_tasks():
        for row in tree.get_children():
            tree.delete(row)
        cursor.execute("SELECT * FROM tasks")
        for row in cursor.fetchall():
            tree.insert('', 'end', values=row)

    load_tasks()

    def on_double_click(event):
        item = tree.selection()[0]
        values = tree.item(item, "values")
        edit_task(values)

    def edit_task(values):
        edit_window = tk.Toplevel(admin_window)
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
        title_label = tk.Label(edit_window, text="Заголовок")
        title_label.pack()
        title_entry = tk.Entry(edit_window)
        title_entry.insert(0, values[1])
        title_entry.pack()

        description_label = tk.Label(edit_window, text="Описание")
        description_label.pack()
        description_entry = tk.Entry(edit_window)
        description_entry.insert(0, values[2])
        description_entry.pack()

        reason_label = tk.Label(edit_window, text="Причина")
        reason_label.pack()
        reason_entry = tk.Entry(edit_window)
        reason_entry.insert(0, values[3])
        reason_entry.pack()

        priority_label = tk.Label(edit_window, text="Приоритет")
        priority_label.pack()
        priority_option = tk.StringVar(edit_window)
        priority_option.set(values[5])
        priority_options = ["Низкий", "Средний", "Высокий"]
        priority_dropdown = tk.OptionMenu(edit_window, priority_option, *priority_options)
        priority_dropdown.pack()

        assigned_to_label = tk.Label(edit_window, text="Назначено")
        assigned_to_label.pack()
        assigned_to_option = tk.StringVar(edit_window)
        assigned_to_option.set(values[6])
        assigned_to_options = get_workers()
        assigned_to_dropdown = tk.OptionMenu(edit_window, assigned_to_option, *assigned_to_options)
        assigned_to_dropdown.pack()

        save_button = tk.Button(edit_window, text="Сохранить", command=save_changes)
        save_button.pack(pady=10)

    tree.bind('<Double-1>', on_double_click)

    def get_workers():
        cursor.execute("SELECT username FROM users WHERE role='worker'")
        return [row[0] for row in cursor.fetchall()]

def worker_window(username):
    worker_window = tk.Toplevel(root)
    worker_window.title("Работник")
    worker_window.geometry("800x400")

    tree = ttk.Treeview(worker_window, columns=('ID', 'Заголовок', 'Описание', 'Причина', 'Статус', 'Приоритет', 'Работник', 'Клиент', 'Время'), show='headings')
    for col in ('ID', 'Заголовок', 'Описание', 'Причина', 'Статус', 'Приоритет', 'Работник', 'Клиент', 'Время'):
        tree.heading(col, text=col)
        tree.column(col, width=100)
    tree.pack(fill="both", expand=True)

    def load_worker_tasks():
        for row in tree.get_children():
            tree.delete(row)
        cursor.execute("SELECT * FROM tasks WHERE assigned_to=?", (username,))
        for row in cursor.fetchall():
            tree.insert('', 'end', values=row)

    load_worker_tasks()

    def on_double_click(event):
        item = tree.selection()[0]
        values = tree.item(item, "values")
        edit_task(values)

    def edit_task(values):
        edit_window = tk.Toplevel(worker_window)
        edit_window.title("Редактировать")
        edit_window.geometry("400x200")

        def save_changes():
            new_reason = reason_entry.get()
            cursor.execute('UPDATE tasks SET reason=? WHERE id=?', (new_reason, values[0]))
            conn.commit()
            load_worker_tasks()
            edit_window.destroy()

        reason_label = tk.Label(edit_window, text="Причина поломки")
        reason_label.pack()
        reason_entry = tk.Entry(edit_window)
        reason_entry.insert(0, values[3])
        reason_entry.pack()

        save_button = tk.Button(edit_window, text="Сохранить", command=save_changes)
        save_button.pack(pady=5)

    tree.bind('<Double-1>', on_double_click)

# Основное окно приложения
root = tk.Tk()
root.title("Куватов прогс")
root.geometry("300x200")

username_label = tk.Label(root, text="Имя пользователя")
username_label.pack()
username_entry = tk.Entry(root)
username_entry.pack()

password_label = tk.Label(root, text="Пароль")
password_label.pack()
password_entry = tk.Entry(root, show="*")
password_entry.pack()

login_button = tk.Button(root, text="Войти", command=login)
login_button.pack(pady=10)

root.mainloop()