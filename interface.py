import tkinter as tk
from tkinter import ttk, messagebox
from threading import Thread, Semaphore
import time

# Semáforos e variáveis globais
remote = Semaphore(1)   
mutex = Semaphore(1)    
outside = Semaphore(0)  
canal_atual = "Nenhum"  
tv = 0                  
waiting = 0             

# Função myTimer para contar tempo
def myTimer(n, update_callback):
    start = time.time()
    passed_time = 0
    while passed_time < n:
        time.sleep(0.1)
        passed_time = time.time() - start
        remaining_time = max(0, n - passed_time)
        update_callback(int(remaining_time))

# Classe Hospede
class Hospede(Thread):
    def __init__(self, parent, id, canal, watch_time, rest_time, log_box, tree):
        super().__init__()
        self.id = id
        self.canal = canal
        self.watch_time = watch_time
        self.rest_time = rest_time
        self.log_box = log_box
        self.tree = tree
        self.status = "Descansando"
        self.running = True
        self.remaining_watch_time = 0
        self.remaining_rest_time = 0
        self.update_ui()

    def update_ui(self):
        """Atualiza os dados do hóspede na interface"""
        for i in self.tree.get_children():
            if self.tree.item(i, "values")[0] == self.id:
                self.tree.item(i, values=(self.id, self.canal, self.status, self.remaining_watch_time, self.remaining_rest_time))

    def log_event(self, event):
        """Adiciona eventos ao log"""
        self.log_box.insert(tk.END, f"{time.strftime('%H:%M:%S')} - {event}")
        self.log_box.see(tk.END)

    def check_tv_is_available(self):
        global tv, waiting
        if tv == 0:
            remote.release()
            if waiting > 0:
                outside.release(waiting)
                waiting = 0

    def watch(self):
        global canal_atual
        self.status = "Assistindo"
        self.log_event(f"{self.id} está assistindo no canal {self.canal}")
        self.remaining_watch_time = self.watch_time
        self.update_ui()
        myTimer(self.watch_time, self.update_watch_time)
        self.remaining_watch_time = 0
        self.update_ui()

    def rest(self):
        self.status = "Descansando"
        self.log_event(f"{self.id} está descansando")
        self.remaining_rest_time = self.rest_time
        self.update_ui()
        myTimer(self.rest_time, self.update_rest_time)
        self.remaining_rest_time = 0
        self.update_ui()

    def update_watch_time(self, remaining_time):
        self.remaining_watch_time = remaining_time
        self.update_ui()

    def update_rest_time(self, remaining_time):
        self.remaining_rest_time = remaining_time
        self.update_ui()

    def run(self):
        global canal_atual, tv, waiting
        while self.running:
            mutex.acquire()
            self.log_event(f"{self.id} chegou para assistir")

            if tv == 0:
                remote.acquire()
                canal_atual = self.canal
                self.log_event(f"{self.id} pegou o controle e colocou no canal {self.canal}")

            if self.canal == canal_atual:
                tv += 1
                mutex.release()
                self.watch()

                mutex.acquire()
                tv -= 1
                self.log_event(f"{self.id} saiu da TV")
                self.check_tv_is_available()
                mutex.release()
                self.rest()

            else:
                waiting += 1
                mutex.release()
                self.log_event(f"{self.id} está esperando")
                self.status = "Dormindo"
                self.update_ui()
                outside.acquire()

    def stop(self):
        """Encerra a thread"""
        self.running = False

# GUI Principal
class TVManagerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Gerenciador de Hóspedes - Problema da TV")
        self.geometry("900x600")

        # Variáveis
        self.hospedes = []
        self.hospede_counter = 1

        # Widgets principais
        self.create_widgets()

    def create_widgets(self):
        # Input Frame
        input_frame = tk.Frame(self, bd=2, relief="raised", padx=5, pady=5)
        input_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(input_frame, text="ID do Hóspede:").grid(row=0, column=0, padx=5, pady=5)
        self.id_entry = tk.Entry(input_frame)
        self.id_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(input_frame, text="Canal Preferido:").grid(row=0, column=2, padx=5, pady=5)
        self.canal_entry = tk.Entry(input_frame)
        self.canal_entry.grid(row=0, column=3, padx=5, pady=5)

        tk.Label(input_frame, text="Tempo Assistindo (s):").grid(row=1, column=0, padx=5, pady=5)
        self.watch_time_entry = tk.Entry(input_frame)
        self.watch_time_entry.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(input_frame, text="Tempo Descansando (s):").grid(row=1, column=2, padx=5, pady=5)
        self.rest_time_entry = tk.Entry(input_frame)
        self.rest_time_entry.grid(row=1, column=3, padx=5, pady=5)

        tk.Button(input_frame, text="Criar Hóspede", command=self.add_hospede).grid(row=0, column=4, rowspan=2, padx=10)

        # Canal Atual
        self.canal_label = tk.Label(self, text="Canal Atual: Nenhum", font=("Arial", 14, "bold"))
        self.canal_label.pack(pady=5)

        # TreeView para mostrar os hóspedes
        columns = ("ID", "Canal", "Status", "Tempo Assistindo", "Tempo Descansando")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=8)
        for col in columns:
            self.tree.heading(col, text=col)
        self.tree.pack(pady=5, padx=10)

        # Log de eventos
        tk.Label(self, text="Log de Eventos").pack()
        self.log_box = tk.Listbox(self, height=8)
        self.log_box.pack(fill="x", padx=10, pady=5)

    def add_hospede(self):
        try:
            hospede_id = self.id_entry.get() or f"Hospede {self.hospede_counter}"
            canal = int(self.canal_entry.get())
            watch_time = int(self.watch_time_entry.get())
            rest_time = int(self.rest_time_entry.get())

            # Cria e inicia a thread do hóspede
            hospede = Hospede(self, hospede_id, canal, watch_time, rest_time, self.log_box, self.tree)
            self.hospedes.append(hospede)
            self.hospede_counter += 1

            # Adiciona o hóspede à interface
            self.tree.insert("", "end", values=(hospede_id, canal, "Descansando", 0, 0))
            hospede.start()
        except ValueError:
            messagebox.showerror("Erro", "Preencha todos os campos corretamente!")

    def on_closing(self):
        """Encerra todas as threads ao fechar"""
        for hospede in self.hospedes:
            hospede.stop()
        self.destroy()

if __name__ == "__main__":
    app = TVManagerApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
