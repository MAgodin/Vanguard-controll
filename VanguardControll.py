import customtkinter as ctk
import os
from tkinter import messagebox
import subprocess
import ctypes
import sys

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

# Configuration de CustomTkinter
ctk.set_appearance_mode("dark")  # Mode sombre
ctk.set_default_color_theme("green")  # Thème de couleur

# Commandes pour gérer Vanguard
disable_vanguard_stop = "sc config vgc start= disabled & sc config vgk start= disabled & net stop vgc & net stop vgk & taskkill /IM vgtray.exe"
enable_vanguard = "sc config vgc start= demand & sc config vgk start= system"

# Vérifier si un service est en cours d'exécution
def is_service_running(service_name):
    try:
        result = subprocess.run(f"sc query {service_name}", shell=True, capture_output=True, text=True)
        return "RUNNING" in result.stdout
    except subprocess.CalledProcessError:
        return False

# Simuler un redémarrage pour Vanguard
def simulate_restart():
    try:
        # Arrêter les services Vanguard (s'ils sont en cours d'exécution)
        if is_service_running("vgc"):
            subprocess.run("net stop vgc", shell=True, check=True)
        else:
            print("Le service vgc n'est pas lancé. Ignorer l'arrêt.")

        if is_service_running("vgk"):
            subprocess.run("net stop vgk", shell=True, check=True)
        else:
            print("Le service vgk n'est pas lancé. Ignorer l'arrêt.")

        # Redémarrer les services Vanguard
        if not is_service_running("vgc"):
            subprocess.run("net start vgc", shell=True, check=True)
        else:
            print("Le service vgc est déjà en cours d'exécution. Ignorer le démarrage.")

        if not is_service_running("vgk"):
            subprocess.run("net start vgk", shell=True, check=True)
        else:
            print("Le service vgk est déjà en cours d'exécution. Ignorer le démarrage.")

        # Relancer vgtray.exe (si nécessaire)
        vgtray_path = r"C:\Program Files\Riot Vanguard\vgtray.exe"  # Chemin par défaut
        if os.path.exists(vgtray_path):
            subprocess.Popen(vgtray_path, shell=True)

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

# Interface principale
def main():
    # Création de la fenêtre
    window = ctk.CTk()
    window.title("Controll Vanguard")
    window.geometry("400x400")
    window.resizable(False, False)

    # Titre de l'application
    title_label = ctk.CTkLabel(window, text="Controll Vanguard", font=("Arial", 24, "bold"))
    title_label.pack(pady=20)

    # Bouton pour désactiver et arrêter Vanguard
    btn_disable_stop = ctk.CTkButton(window, text="Désactiver et arrêter Vanguard", command=disable_and_stop, fg_color="#FF5555", hover_color="#CC0000", font=("Arial", 14))
    btn_disable_stop.pack(pady=20, padx=20, fill="x")

    # Bouton pour activer et simuler un redémarrage
    btn_enable_restart = ctk.CTkButton(window, text="Activer et simuler un redémarrage", command=enable_and_restart, fg_color="#4CAF50", hover_color="#45a049", font=("Arial", 14))
    btn_enable_restart.pack(pady=20, padx=20, fill="x")

    # Bouton pour quitter
    btn_quit = ctk.CTkButton(window, text="Quitter", command=window.quit, fg_color="#666666", hover_color="#444444", font=("Arial", 14))
    btn_quit.pack(pady=20, padx=20, fill="x")

    # Lancer la boucle principale
    window.mainloop()

if __name__ == "__main__":
    main()