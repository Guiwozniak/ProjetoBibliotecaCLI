import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog
import sqlite3
from datetime import datetime, timedelta

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# ======== BANCO DE DADOS ========
conn = sqlite3.connect("biblioteca.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario TEXT UNIQUE,
    senha TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS livros (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo TEXT UNIQUE,
    descricao TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS emprestimos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario TEXT,
    livro TEXT,
    data_emprestimo TEXT,
    data_devolucao TEXT,
    status TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS compras (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario TEXT,
    livro TEXT,
    data_compra TEXT
)
""")

conn.commit()
conn.close()


# ======== LOGIN ========
def verificar_login():
    usuario = entrada_usuario.get()
    senha = entrada_senha.get()

    conn = sqlite3.connect("biblioteca.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE usuario = ? AND senha = ?", (usuario, senha))
    resultado = cursor.fetchone()
    conn.close()

    if resultado:
        abrir_tela_principal(usuario)
    else:
        messagebox.showerror("Erro", "Usuário ou senha incorretos!")


# ======== CADASTRO ========
def cadastrar_usuario():
    usuario = entrada_usuario.get()
    senha = entrada_senha.get()

    if not usuario or not senha:
        messagebox.showwarning("Aviso", "Preencha todos os campos!")
        return

    try:
        conn = sqlite3.connect("biblioteca.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO usuarios (usuario, senha) VALUES (?, ?)", (usuario, senha))
        conn.commit()
        conn.close()
        messagebox.showinfo("Sucesso", "Usuário cadastrado com sucesso!")
        limpar_campos()
    except sqlite3.IntegrityError:
        messagebox.showerror("Erro", "Usuário já existe!")


def limpar_campos():
    entrada_usuario.delete(0, tk.END)
    entrada_senha.delete(0, tk.END)


# ======== TELA DE GERENCIAMENTO ========
def abrir_tela_comprar_emprestar():
    tela = tk.Toplevel()
    tela.title("Gerenciar Livros")
    tela.geometry("500x440")
    tela.config(bg="#2E2E2E")

    tk.Label(tela, text="Gerenciar Livros", font=("Arial", 16, "bold"), bg="#2E2E2E", fg="white").pack(pady=10)

    frame = tk.Frame(tela, bg="#2E2E2E")
    frame.pack(pady=10)

    lista = tk.Listbox(frame, width=60, height=10)
    lista.pack(side=tk.LEFT, padx=5)

    scroll = tk.Scrollbar(frame, command=lista.yview)
    scroll.pack(side=tk.RIGHT, fill=tk.Y)
    lista.config(yscrollcommand=scroll.set)

    def carregar_livros():
        lista.delete(0, tk.END)
        conn = sqlite3.connect("biblioteca.db")
        cursor = conn.cursor()
        cursor.execute("SELECT titulo FROM livros ORDER BY titulo")
        for row in cursor.fetchall():
            lista.insert(tk.END, row[0])
        conn.close()

    carregar_livros()

    tk.Label(tela, text="Selecione uma opção:", bg="#2E2E2E", fg="white", font=("Arial", 11)).pack(pady=5)

    opcao_var = tk.StringVar(value="Compra")
    for texto in ["Compra", "Empréstimo", "Devolução"]:
        tk.Radiobutton(tela, text=texto, variable=opcao_var, value=texto, bg="#2E2E2E", fg="white").pack()

    tk.Label(tela, text="Usuário:", bg="#2E2E2E", fg="white").pack(pady=3)
    entrada_usuario_local = tk.Entry(tela, width=30)
    entrada_usuario_local.pack(pady=3)

    def confirmar_acao():
        selecionado = lista.curselection()
        usuario = entrada_usuario_local.get().strip()

        if not selecionado:
            messagebox.showwarning("Aviso", "Selecione um livro da lista.")
            return
        if not usuario:
            messagebox.showwarning("Aviso", "Digite o nome do usuário.")
            return

        livro = lista.get(selecionado)
        opcao = opcao_var.get()
        conn = sqlite3.connect("biblioteca.db")
        cursor = conn.cursor()

        if opcao == "Compra":
            data_compra = datetime.now().strftime("%d/%m/%Y %H:%M")
            cursor.execute("INSERT INTO compras (usuario, livro, data_compra) VALUES (?, ?, ?)",
                           (usuario, livro, data_compra))
            conn.commit()
            messagebox.showinfo("Compra", f"Livro '{livro}' foi comprado e registrado.")

        elif opcao == "Empréstimo":
            data_emprestimo = datetime.now().strftime("%d/%m/%Y")
            data_devolucao = (datetime.now() + timedelta(days=7)).strftime("%d/%m/%Y")
            cursor.execute("""
                INSERT INTO emprestimos (usuario, livro, data_emprestimo, data_devolucao, status)
                VALUES (?, ?, ?, ?, ?)
            """, (usuario, livro, data_emprestimo, data_devolucao, "Emprestado"))
            conn.commit()
            messagebox.showinfo("Empréstimo", f"Livro '{livro}' emprestado a {usuario} até {data_devolucao}.")

        elif opcao == "Devolução":
            cursor.execute("SELECT * FROM emprestimos WHERE usuario = ? AND livro = ? AND status = 'Emprestado'",
                           (usuario, livro))
            emprestimo = cursor.fetchone()
            if emprestimo:
                cursor.execute("UPDATE emprestimos SET status = 'Devolvido' WHERE id = ?", (emprestimo[0],))
                conn.commit()
                messagebox.showinfo("Devolução", f"Livro '{livro}' devolvido com sucesso!")
            else:
                messagebox.showwarning("Aviso", "Nenhum empréstimo ativo encontrado para este livro.")

        conn.close()

    tk.Button(tela, text="Confirmar", command=confirmar_acao, bg="lightgreen", width=20).pack(pady=10)
    tk.Button(tela, text="Fechar", command=tela.destroy, bg="tomato", fg="white", width=10).pack(pady=5)


# ======== PERFIL DO USUÁRIO ========
def abrir_perfil_usuario(usuario):
    perfil = tk.Toplevel()
    perfil.title("Perfil do Usuário")
    perfil.geometry("400x420")
    perfil.config(bg="#2E2E2E")

    tk.Label(perfil, text=f"Perfil de {usuario}", font=("Arial", 14, "bold"), bg="#2E2E2E", fg="white").pack(pady=10)

    # Se quiser mostrar foto (opcional)
    img_label = tk.Label(perfil, text="(sem foto)", bg="#2E2E2E", fg="white", width=20, height=6)
    img_label.pack(pady=5)

    if PIL_AVAILABLE:
        def selecionar_foto():
            caminho = filedialog.askopenfilename(filetypes=[("Imagens", "*.png;*.jpg;*.jpeg")])
            if caminho:
                imagem = Image.open(caminho).resize((150, 150))
                img = ImageTk.PhotoImage(imagem)
                img_label.config(image=img, text="")
                img_label.image = img
        tk.Button(perfil, text="Selecionar Foto", command=selecionar_foto, bg="blue", fg="white").pack(pady=5)

    # Mostrar histórico do usuário
    conn = sqlite3.connect("biblioteca.db")
    cursor = conn.cursor()
    cursor.execute("SELECT livro, data_emprestimo, data_devolucao, status FROM emprestimos WHERE usuario = ?", (usuario,))
    emprestimos = cursor.fetchall()
    cursor.execute("SELECT livro, data_compra FROM compras WHERE usuario = ?", (usuario,))
    compras = cursor.fetchall()
    conn.close()

    tk.Label(perfil, text="Histórico de Empréstimos:", bg="#2E2E2E", fg="lightblue", font=("Arial", 11, "bold")).pack(pady=5)
    if emprestimos:
        for e in emprestimos:
            tk.Label(perfil, text=f"📖 {e[0]} - {e[3]} (Devolver até: {e[2]})", bg="#2E2E2E", fg="white").pack()
    else:
        tk.Label(perfil, text="Nenhum empréstimo registrado.", bg="#2E2E2E", fg="gray").pack()

    tk.Label(perfil, text="Histórico de Compras:", bg="#2E2E2E", fg="lightblue", font=("Arial", 11, "bold")).pack(pady=5)
    if compras:
        for c in compras:
            tk.Label(perfil, text=f"📘 {c[0]} - {c[1]}", bg="#2E2E2E", fg="white").pack()
    else:
        tk.Label(perfil, text="Nenhuma compra registrada.", bg="#2E2E2E", fg="gray").pack()

    tk.Button(perfil, text="Fechar", command=perfil.destroy, bg="gray", fg="white").pack(pady=15)


# ======== TELA PRINCIPAL ========
def abrir_tela_principal(usuario):
    tela_login.withdraw()
    tela_principal = tk.Toplevel()
    tela_principal.title("Biblioteca - Catálogo de Livros")
    tela_principal.geometry("450x460")
    tela_principal.config(bg="#2E2E2E")

    tk.Label(tela_principal, text=f"Bem-vindo, {usuario}!", font=("Arial", 14), bg="#2E2E2E", fg="white").pack(pady=10)
    tk.Label(tela_principal, text="📚 Catálogo de Livros", font=("Arial", 12, "bold"), bg="#2E2E2E", fg="lightblue").pack(pady=5)

    lista = tk.Listbox(tela_principal, width=55, height=10)
    lista.pack(pady=10)

    def carregar_livros():
        lista.delete(0, tk.END)
        conn = sqlite3.connect("biblioteca.db")
        cursor = conn.cursor()
        cursor.execute("SELECT titulo FROM livros ORDER BY titulo")
        for row in cursor.fetchall():
            lista.insert(tk.END, row[0])
        conn.close()

    carregar_livros()

    def adicionar_livro():
        novo_livro = simpledialog.askstring("Adicionar Livro", "Digite o nome do livro:")
        if novo_livro:
            conn = sqlite3.connect("biblioteca.db")
            cursor = conn.cursor()
            try:
                cursor.execute("INSERT INTO livros (titulo) VALUES (?)", (novo_livro,))
                conn.commit()
                messagebox.showinfo("Sucesso", f"Livro '{novo_livro}' adicionado com sucesso!")
            except sqlite3.IntegrityError:
                messagebox.showwarning("Aviso", "Esse livro já existe no catálogo.")
            conn.close()
            carregar_livros()

    def remover_livro():
        selecionado = lista.curselection()
        if not selecionado:
            messagebox.showwarning("Aviso", "Selecione um livro para remover.")
            return
        livro = lista.get(selecionado)
        if messagebox.askyesno("Confirmar", f"Remover '{livro}'?"):
            conn = sqlite3.connect("biblioteca.db")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM livros WHERE titulo = ?", (livro,))
            conn.commit()
            conn.close()
            carregar_livros()
            messagebox.showinfo("Removido", f"Livro '{livro}' foi removido.")

    def descricao_livro():
        selecionado = lista.curselection()
        if not selecionado:
            messagebox.showwarning("Aviso", "Selecione um livro primeiro.")
            return
        livro = lista.get(selecionado)
        conn = sqlite3.connect("biblioteca.db")
        cursor = conn.cursor()
        cursor.execute("SELECT descricao FROM livros WHERE titulo = ?", (livro,))
        resultado = cursor.fetchone()
        if resultado and resultado[0]:
            messagebox.showinfo(f"Descrição - {livro}", resultado[0])
        else:
            nova_desc = simpledialog.askstring("Adicionar Descrição", f"Adicione uma descrição para '{livro}':")
            if nova_desc:
                cursor.execute("UPDATE livros SET descricao = ? WHERE titulo = ?", (nova_desc, livro))
                conn.commit()
                messagebox.showinfo("Sucesso", "Descrição adicionada com sucesso!")
        conn.close()

    frame_botoes = tk.Frame(tela_principal, bg="#2E2E2E")
    frame_botoes.pack(pady=5)

    tk.Button(frame_botoes, text="Adicionar Livro", command=adicionar_livro, bg="green", fg="white", width=15).grid(row=0, column=0, padx=5)
    tk.Button(frame_botoes, text="Remover Livro", command=remover_livro, bg="red", fg="white", width=15).grid(row=0, column=1, padx=5)
    tk.Button(frame_botoes, text="Descrição", command=descricao_livro, bg="blue", fg="white", width=15).grid(row=0, column=2, padx=5)

    tk.Button(tela_principal, text="Gerenciar Livros", command=abrir_tela_comprar_emprestar, bg="lightblue", fg="white", width=20).pack(pady=10)

    # --- PERFIL ---
    tk.Button(tela_principal, text="Perfil", command=lambda: abrir_perfil_usuario(usuario), bg="purple", fg="white", width=12).pack(pady=5)

    tk.Button(tela_principal, text="Sair", command=lambda: [tela_principal.destroy(), tela_login.deiconify()], bg="tomato", fg="white", width=10).pack(pady=10)


# ======== LOGIN PRINCIPAL ========
tela_login = tk.Tk()
tela_login.title("Login - Biblioteca Virtual")
tela_login.geometry("350x250")
tela_login.config(bg="#1E1E1E")

tk.Label(tela_login, text="Biblioteca Virtual", font=("Arial", 16, "bold"), bg="#1E1E1E", fg="white").pack(pady=10)
tk.Label(tela_login, text="Usuário:", bg="#1E1E1E", fg="white").pack()
entrada_usuario = tk.Entry(tela_login, width=30)
entrada_usuario.pack(pady=5)

tk.Label(tela_login, text="Senha:", bg="#1E1E1E", fg="white").pack()
entrada_senha = tk.Entry(tela_login, show="*", width=30)
entrada_senha.pack(pady=5)

frame_botoes = tk.Frame(tela_login, bg="#1E1E1E")
frame_botoes.pack(pady=10)

tk.Button(frame_botoes, text="Login", command=verificar_login, bg="lightblue", width=10).grid(row=0, column=0, padx=5)
tk.Button(frame_botoes, text="Cadastrar", command=cadastrar_usuario, bg="green", fg="white", width=10).grid(row=0, column=1, padx=5)

tela_login.mainloop()
