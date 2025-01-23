import customtkinter as ctk
import os
from tkinter import messagebox
from tkinter import PhotoImage
import subprocess
import ctypes
import sys
import time
import threading
from PIL import Image
import json
from infi.systray import SysTrayIcon

# Vérifier les privilèges administratifs
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if not is_admin():
    # Relancer le script avec des privilèges administratifs
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    sys.exit()

def resource_path(relative_path):
    """Convertit un chemin relatif en chemin absolu pour les fichiers inclus avec PyInstaller."""
    if hasattr(sys, '_MEIPASS'):
        # Si l'application est exécutée en mode "frozen" (fichier exécutable)
        base_path = sys._MEIPASS
    else:
        # Si l'application est exécutée en mode script
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Configuration de CustomTkinter
ctk.set_appearance_mode("dark")  # Mode sombre
ctk.set_default_color_theme("green")  # Thème de couleur

# Commandes pour gérer Vanguard
disable_vanguard_stop = "sc config vgc start= disabled & sc config vgk start= disabled & net stop vgc & net stop vgk & taskkill /IM vgtray.exe"
enable_vanguard = "sc config vgc start= demand & sc config vgk start= system"

# Chemin du fichier de configuration
CONFIG_FILE = "config.json"

# Chemin du dossier de démarrage
STARTUP_FOLDER = os.path.join(os.getenv("APPDATA"), "Microsoft", "Windows", "Start Menu", "Programs", "Startup")

systray_icon = None  # Variable pour stocker l'icône de la barre des tâches

# Charger la configuration
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {"auto_mode": False}  # Par défaut, le mode automatique est désactivé

# Sauvegarder la configuration
def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)

# Ajouter ou supprimer le raccourci au démarrage
def manage_startup_shortcut(enable):
    script_path = os.path.abspath(sys.argv[0])  # Chemin absolu du script Python
    shortcut_path = os.path.join(STARTUP_FOLDER, "Controll Vanguard.lnk")

    if enable:
        # Créer un raccourci dans le dossier de démarrage
        if not os.path.exists(shortcut_path):
            try:
                import winshell
                from win32com.client import Dispatch

                shell = Dispatch('WScript.Shell')
                shortcut = shell.CreateShortCut(shortcut_path)
                shortcut.Targetpath = script_path
                shortcut.WorkingDirectory = os.path.dirname(script_path)
                shortcut.save()
                print("Raccourci créé dans le dossier de démarrage.")
            except ImportError:
                messagebox.showerror("Erreur", "Les modules 'winshell' ou 'pywin32' ne sont pas installés.")
            except Exception as e:
                print(f"Erreur lors de la création du raccourci : {e}")
    else:
        # Supprimer le raccourci du dossier de démarrage
        if os.path.exists(shortcut_path):
            try:
                os.remove(shortcut_path)
                print("Raccourci supprimé du dossier de démarrage.")
            except Exception as e:
                print(f"Erreur lors de la suppression du raccourci : {e}")

# Vérifier si un service est en cours d'exécution
def is_service_running(service_name):
    try:
        result = subprocess.run(f"sc query {service_name}", shell=True, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
        return "RUNNING" in result.stdout
    except subprocess.CalledProcessError:
        return False

def is_process_running(process_name):
    try:
        result = subprocess.run(f"tasklist /FI \"IMAGENAME eq {process_name}\"", shell=True, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
        return process_name in result.stdout
    except subprocess.CalledProcessError:
        return False

def simulate_restart():
    try:
        # Arrêter les services Vanguard (s'ils sont en cours d'exécution)
        if is_service_running("vgc"):
            subprocess.run("net stop vgc", shell=True, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
        else:
            print("Le service vgc n'est pas lancé. Ignorer l'arrêt.")

        if is_service_running("vgk"):
            subprocess.run("net stop vgk", shell=True, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
        else:
            print("Le service vgk n'est pas lancé. Ignorer l'arrêt.")

        # Redémarrer les services Vanguard
        if not is_service_running("vgc"):
            subprocess.run("net start vgc", shell=True, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
        else:
            print("Le service vgc est déjà en cours d'exécution. Ignorer le démarrage.")

        if not is_service_running("vgk"):
            subprocess.run("net start vgk", shell=True, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
        else:
            print("Le service vgk est déjà en cours d'exécution. Ignorer le démarrage.")

        # Relancer vgtray.exe (si nécessaire)
        vgtray_path = r"C:\Program Files\Riot Vanguard\vgtray.exe"  # Chemin par défaut
        if os.path.exists(vgtray_path):
            subprocess.Popen(vgtray_path, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)

        messagebox.showinfo("Succès", "Les services Vanguard ont été redémarrés avec succès.")
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Erreur", f"Une erreur s'est produite : {e}")

# Fonction pour désactiver et arrêter Vanguard
def disable_and_stop():
    os.system(disable_vanguard_stop)
    messagebox.showinfo("Succès", "Vanguard a été désactivé et arrêté avec succès.")

# Fonction pour activer et simuler un redémarrage
def enable_and_restart():
    os.system(enable_vanguard)
    simulate_restart()

# Fonction pour surveiller le client Riot
def monitor_riot_client(stop_event):
    while not stop_event.is_set():
        config = load_config()
        if not config.get("auto_mode", False):
            break  # Arrêter la surveillance si le mode automatique est désactivé

        if is_process_running("RiotClientServices.exe"):
            if not is_service_running("vgc"):
                enable_and_restart()
        else:
            if is_service_running("vgc"):
                disable_and_stop()
        time.sleep(10)  # Vérifier toutes les 10 secondes

# Fonction pour créer l'icône dans la zone de notification
def create_systray_icon(window):
    # Charger votre image pour l'icône
    image_path = resource_path("imgVanguardCross.png")
    if not os.path.exists(image_path):
        messagebox.showerror("Erreur", f"L'image {image_path} n'a pas été trouvée.")
        return None

    image = Image.open(image_path)

    # Créer un menu contextuel pour l'icône
    menu_options = (
        ("Ouvrir", None, lambda systray: window.deiconify()),
        ("Quitter", None, lambda systray: (window.destroy(), systray.shutdown())),
    )

    # Créer l'icône dans la zone de notification
    systray = SysTrayIcon(image, "Controll Vanguard", menu_options)

    # Masquer la fenêtre principale lors de la minimisation
    def on_minimize(event=None):
        window.withdraw()

    window.bind("<Unmap>", on_minimize)

    # Démarrer l'icône
    systray.start()
    return systray

# Interface principale
def main():
    # Création de la fenêtre
    window = ctk.CTk()
    # Charger l'image pour l'icône de la fenêtre principale
    icon_path = resource_path("imgVanguardCross.png")  # Utiliser resource_path
    if not os.path.exists(icon_path):
        messagebox.showerror("Erreur", f"L'image {icon_path} n'a pas été trouvée.")
        sys.exit()

    # Définir l'icône de la fenêtre principale
    icon_image = PhotoImage(file=icon_path)
    window.iconphoto(True, icon_image)
    window.title("Controll Vanguard")
    window.geometry("400x450")
    window.resizable(False, False)

    # Titre de l'application
    title_label = ctk.CTkLabel(window, text="Controll Vanguard", font=("Arial", 24, "bold"))
    title_label.pack(pady=20)

    # Bouton switch pour le mode automatique
    config = load_config()
    auto_mode_var = ctk.BooleanVar(value=config.get("auto_mode", False))

    # Événement pour arrêter la surveillance
    stop_event = threading.Event()

    def toggle_auto_mode():
        config["auto_mode"] = auto_mode_var.get()
        save_config(config)
        manage_startup_shortcut(auto_mode_var.get())  # Gérer le raccourci au démarrage

        global systray_icon
    
        if auto_mode_var.get():
            # Activer le mode automatique
            threading.Thread(target=create_systray_icon, args=(window,), daemon=True).start()

            # Vérifier si aucune application Riot n'est en cours d'exécution
            if not is_process_running("RiotClientServices.exe"):
                disable_and_stop()  # Désactiver Vanguard si Riot n'est pas lancé

            # Démarrer la surveillance du client Riot
            stop_event.clear()  # Réinitialiser l'événement d'arrêt
            if not systray_icon:
                systray_icon = create_systray_icon(window)
            threading.Thread(target=monitor_riot_client, args=(stop_event,), daemon=True).start()

            messagebox.showinfo("Mode automatique", "Le mode automatique est activé. L'application se lancera au démarrage et gérera Vanguard automatiquement.")
        else:
            # Désactiver le mode automatique
            stop_event.set()  # Signaler aux threads en cours de s'arrêter
            if systray_icon:
                systray_icon.shutdown()  # Arrêter l'icône de la zone de notification
                systray_icon = None
            messagebox.showinfo("Mode automatique", "Le mode automatique est désactivé. L'application ne se lancera pas au démarrage.")

    switch_auto_mode = ctk.CTkSwitch(window, text="Mode automatique", variable=auto_mode_var, command=toggle_auto_mode)
    switch_auto_mode.pack(pady=10)

    # Bouton pour désactiver et arrêter Vanguard
    btn_disable_stop = ctk.CTkButton(window, text="Désactiver et arrêter Vanguard", command=disable_and_stop, fg_color="#FF5555", hover_color="#CC0000", font=("Arial", 14))
    btn_disable_stop.pack(pady=10, padx=20, fill="x")

    # Bouton pour activer et simuler un redémarrage
    btn_enable_restart = ctk.CTkButton(window, text="Activer et simuler un redémarrage", command=enable_and_restart, fg_color="#4CAF50", hover_color="#45a049", font=("Arial", 14))
    btn_enable_restart.pack(pady=10, padx=20, fill="x")

    # Bouton pour quitter
    def quit_app():
        if auto_mode_var.get():
            window.withdraw()  # Minimiser dans la zone des icônes cachées
        else:
            if systray_icon:
                systray_icon.shutdown()  # Arrêter l'icône de la zone de notification
            window.destroy()  # Fermer l'application

    btn_quit = ctk.CTkButton(window, text="Quitter", command=quit_app, fg_color="#666666", hover_color="#444444", font=("Arial", 14))
    btn_quit.pack(pady=10, padx=20, fill="x")

    # Gérer la croix de fermeture
    def on_close():
        if auto_mode_var.get():
            threading.Thread(target=create_systray_icon, args=(window,), daemon=True).start()
            window.withdraw()  # Minimiser dans la zone des icônes cachées
        else:
            if systray_icon:
                systray_icon.shutdown()  # Arrêter l'icône de la zone de notification
            window.destroy()  # Fermer l'application

    window.protocol("WM_DELETE_WINDOW", on_close)

    # Démarrer la surveillance du client Riot dans un thread séparé
    if auto_mode_var.get():
        threading.Thread(target=monitor_riot_client, args=(stop_event,), daemon=True).start()

    # Créer l'icône dans la zone de notification
    if auto_mode_var.get():
        threading.Thread(target=create_systray_icon, args=(window,), daemon=True).start()

    # Lancer la boucle principale
    window.mainloop()

if __name__ == "__main__":
    main()