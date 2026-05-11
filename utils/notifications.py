from tkinter import messagebox


# =========================================
# NOTIFICACION EXITO
# =========================================

def success_message(
    title,
    message
):

    messagebox.showinfo(
        title,
        message
    )


# =========================================
# NOTIFICACION ERROR
# =========================================

def error_message(
    title,
    message
):

    messagebox.showerror(
        title,
        message
    )


# =========================================
# NOTIFICACION ALERTA
# =========================================

def warning_message(
    title,
    message
):

    messagebox.showwarning(
        title,
        message
    )