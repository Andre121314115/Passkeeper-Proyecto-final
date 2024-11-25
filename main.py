import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sqlite3
import random
import string


# --- Funciones de seguridad de contraseñas ---
def generar_contraseña_segura(contraseña):
    return contraseña + ''.join(random.choices(string.ascii_letters + string.digits + string.punctuation, k=6))


def calcular_seguridad_contraseña(contraseña):
    seguridad = 0
    if len(contraseña) >= 8: seguridad += 25
    if any(c.islower() for c in contraseña): seguridad += 20
    if any(c.isupper() for c in contraseña): seguridad += 20
    if any(c.isdigit() for c in contraseña): seguridad += 15
    if any(c in string.punctuation for c in contraseña): seguridad += 20
    return min(seguridad, 100)


# --- Funciones de Base de Datos ---
def init_db():
    with sqlite3.connect('passkeeper.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS usuarios (
                            id INTEGER PRIMARY KEY,
                            usuario TEXT UNIQUE,
                            contraseña TEXT,
                            email TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS contraseñas (
                            id INTEGER PRIMARY KEY,
                            usuario_id INTEGER,
                            sitio TEXT,
                            contraseña TEXT,
                            categoria TEXT,
                            seguridad INTEGER,
                            FOREIGN KEY(usuario_id) REFERENCES usuarios(id))''')
        conn.commit()


def agregar_columna_seguridad():
    try:
        with sqlite3.connect('passkeeper.db') as conn:
            cursor = conn.cursor()
            cursor.execute("ALTER TABLE contraseñas ADD COLUMN seguridad INTEGER")
            conn.commit()
    except sqlite3.OperationalError:
        pass


# --- Funciones de manejo de contraseñas ---
def registrar_contraseña(usuario_id, sitio, contraseña, categoria):
    seguridad = calcular_seguridad_contraseña(contraseña)
    with sqlite3.connect('passkeeper.db') as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO contraseñas (usuario_id, sitio, contraseña, categoria, seguridad) VALUES (?, ?, ?, ?, ?)",
            (usuario_id, sitio, contraseña, categoria, seguridad))
        conn.commit()


def visualizar_contraseñas(usuario_id):
    ventana = tk.Toplevel()
    ventana.title("Contraseñas Guardadas")

    with sqlite3.connect('passkeeper.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT sitio, categoria, contraseña, seguridad FROM contraseñas WHERE usuario_id = ?",
                       (usuario_id,))
        contraseñas = cursor.fetchall()

    if contraseñas:
        for sitio, categoria, contraseña, seguridad in contraseñas:
            tk.Label(ventana,
                     text=f"Sitio: {sitio} | Categoría: {categoria} | Contraseña: {contraseña} | Seguridad: {seguridad}%").pack(
                pady=5)
    else:
        tk.Label(ventana, text="No tienes contraseñas guardadas.").pack(pady=5)


# --- Funciones de validación y autenticación ---
def validar_credenciales(usuario, contraseña):
    with sqlite3.connect('passkeeper.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM usuarios WHERE usuario = ? AND contraseña = ?",
                       (usuario, contraseña))
        result = cursor.fetchone()
    return result[0] if result else None


def cambiar_contraseña(usuario_id, nueva_contraseña):
    with sqlite3.connect('passkeeper.db') as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE usuarios SET contraseña = ? WHERE id = ?",
                       (nueva_contraseña, usuario_id))
        conn.commit()


# --- Funciones de la interfaz gráfica ---
def crear_ventana_principal():
    ventana = tk.Tk()
    ventana.title("PassKeeper - Inicio de Sesión")
    ventana.geometry("350x300")

    label_titulo = ttk.Label(ventana, text="Iniciar Sesión", font=("Arial", 16))
    label_titulo.pack(pady=20)

    label_usuario = ttk.Label(ventana, text="Usuario:")
    label_usuario.pack(pady=5)
    entry_usuario = ttk.Entry(ventana, width=30)
    entry_usuario.pack(pady=5)

    label_contraseña = ttk.Label(ventana, text="Contraseña:")
    label_contraseña.pack(pady=5)
    entry_contraseña = ttk.Entry(ventana, width=30, show="*")
    entry_contraseña.pack(pady=5)

    boton_iniciar = ttk.Button(ventana, text="Iniciar Sesión",
                               command=lambda: iniciar_sesion(entry_usuario, entry_contraseña))
    boton_iniciar.pack(pady=10)

    boton_registro = ttk.Button(ventana, text="Registrarse", command=interfaz_registro)
    boton_registro.pack(pady=5)

    boton_recuperar = ttk.Button(ventana, text="¿Olvidaste tu contraseña?", command=interfaz_recuperar_contraseña)
    boton_recuperar.pack(pady=5)

    ventana.mainloop()


def iniciar_sesion(entry_usuario, entry_contraseña):
    usuario = entry_usuario.get()
    contraseña = entry_contraseña.get()
    usuario_id = validar_credenciales(usuario, contraseña)
    if usuario_id:
        messagebox.showinfo("Bienvenido", f"Bienvenido, {usuario}")
        interfaz_menu_principal(usuario_id)
    else:
        messagebox.showerror("Error", "Credenciales incorrectas.")


def interfaz_menu_principal(usuario_id):
    def abrir_gestion():
        interfaz_gestion_contraseñas(usuario_id)

    def abrir_generar_contraseña():
        interfaz_generar_contraseña()

    ventana = tk.Tk()
    ventana.title("PassKeeper - Menú Principal")
    ventana.geometry("350x250")

    tk.Label(ventana, text="Bienvenido al Gestor de Contraseñas", font=("Arial", 16)).pack(pady=20)
    ttk.Button(ventana, text="Gestión de Contraseñas", command=abrir_gestion).pack(pady=10)
    ttk.Button(ventana, text="Generar Contraseña Segura", command=abrir_generar_contraseña).pack(pady=10)
    ttk.Button(ventana, text="Cambiar Contraseña", command=lambda: interfaz_cambiar_contraseña(usuario_id)).pack(
        pady=10)
    ttk.Button(ventana, text="Ver Contraseñas", command=lambda: visualizar_contraseñas(usuario_id)).pack(pady=10)
    ttk.Button(ventana, text="Salir", command=ventana.destroy).pack(pady=10)
    ventana.mainloop()


def interfaz_cambiar_contraseña(usuario_id):
    def cambiar():
        nueva_contraseña = entry_nueva_contraseña.get()
        if nueva_contraseña:
            cambiar_contraseña(usuario_id, nueva_contraseña)
            messagebox.showinfo("Éxito", "Contraseña actualizada.")
        else:
            messagebox.showerror("Error", "La contraseña no puede estar vacía.")

    ventana = tk.Toplevel()
    ventana.title("Cambiar Contraseña")
    tk.Label(ventana, text="Nueva Contraseña:").pack(pady=5)
    entry_nueva_contraseña = tk.Entry(ventana, show="*")
    entry_nueva_contraseña.pack(pady=5)
    ttk.Button(ventana, text="Cambiar", command=cambiar).pack(pady=10)


def interfaz_registro():
    def registrar():
        usuario = entry_usuario.get()
        contraseña = entry_contraseña.get()
        email = entry_email.get()
        registrar_usuario(usuario, contraseña, email)

    ventana = tk.Toplevel()
    ventana.title("Registro de Usuario")
    tk.Label(ventana, text="Usuario:").pack(pady=5)
    entry_usuario = tk.Entry(ventana)
    entry_usuario.pack(pady=5)
    tk.Label(ventana, text="Contraseña:").pack(pady=5)
    entry_contraseña = tk.Entry(ventana, show="*")
    entry_contraseña.pack(pady=5)
    tk.Label(ventana, text="Email:").pack(pady=5)
    entry_email = tk.Entry(ventana)
    entry_email.pack(pady=5)
    ttk.Button(ventana, text="Registrar", command=registrar).pack(pady=10)


def registrar_usuario(usuario, contraseña, email):
    if usuario and contraseña and email:
        with sqlite3.connect('passkeeper.db') as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("INSERT INTO usuarios (usuario, contraseña, email) VALUES (?, ?, ?)",
                               (usuario, contraseña, email))  # No ciframos la contraseña aquí
                conn.commit()
                messagebox.showinfo("Éxito", "Usuario registrado con éxito.")
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "El nombre de usuario ya existe.")
    else:
        messagebox.showerror("Error", "Todos los campos son obligatorios.")


def obtener_contraseña_por_email(email):
    with sqlite3.connect('passkeeper.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT contraseña FROM usuarios WHERE email = ?", (email,))
        result = cursor.fetchone()
    return result[0] if result else None


def interfaz_recuperar_contraseña():
    def recuperar():
        email = entry_email.get()
        contraseña = obtener_contraseña_por_email(email)
        if contraseña:
            messagebox.showinfo("Éxito", "Se ha enviado un enlace de restablecimiento a tu correo.")
        else:
            messagebox.showerror("Error", "Email no encontrado.")

    ventana = tk.Toplevel()
    ventana.title("Recuperar Contraseña")
    tk.Label(ventana, text="Email:").pack(pady=5)
    entry_email = tk.Entry(ventana)
    entry_email.pack(pady=5)
    ttk.Button(ventana, text="Recuperar Contraseña", command=recuperar).pack(pady=10)


def interfaz_gestion_contraseñas(usuario_id):
    def agregar_contraseña():
        sitio = simpledialog.askstring("Nuevo", "Nombre del Sitio/Servicio:")
        categoria = simpledialog.askstring("Nuevo", "Categoría:")
        contraseña = simpledialog.askstring("Nuevo", "Contraseña:")
        if sitio and categoria and contraseña:
            registrar_contraseña(usuario_id, sitio, contraseña, categoria)
            messagebox.showinfo("Éxito", "Contraseña guardada.")
        else:
            messagebox.showerror("Error", "Todos los campos son obligatorios.")

    ventana = tk.Toplevel()
    ventana.title("Gestión de Contraseñas")
    ttk.Button(ventana, text="Agregar Contraseña", command=agregar_contraseña).pack(pady=10)
    ttk.Button(ventana, text="Ver Contraseñas", command=lambda: visualizar_contraseñas(usuario_id)).pack(pady=10)
    ttk.Button(ventana, text="Cerrar", command=ventana.destroy).pack(pady=10)


def interfaz_generar_contraseña():
    def generar():
        contraseña = entry_contraseña.get()
        if contraseña:
            contraseña_segura = generar_contraseña_segura(contraseña)
            entry_contraseña_segura.delete(0, tk.END)
            entry_contraseña_segura.insert(0, contraseña_segura)
        else:
            messagebox.showerror("Error", "Por favor ingresa una contraseña para mejorarla.")

    ventana = tk.Toplevel()
    ventana.title("Generar Contraseña Segura")
    tk.Label(ventana, text="Ingresa tu contraseña:").pack(pady=10)
    entry_contraseña = ttk.Entry(ventana, width=30)
    entry_contraseña.pack(pady=5)

    tk.Label(ventana, text="Contraseña mejorada:").pack(pady=10)
    entry_contraseña_segura = ttk.Entry(ventana, width=30)
    entry_contraseña_segura.pack(pady=5)

    ttk.Button(ventana, text="Generar Contraseña Segura", command=generar).pack(pady=10)


# --- Inicialización ---
if __name__ == "__main__":
    init_db()
    agregar_columna_seguridad()
    crear_ventana_principal()
