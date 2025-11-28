import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog
import sqlite3
from datetime import datetime, timedelta

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


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
    descricao TEXT,
    quantidade INTEGER DEFAULT 1
)
""")


cursor.execute("PRAGMA table_info(livros)")
cols = [c[1] for c in cursor.fetchall()]
if "quantidade" not in cols:
    try:
        cursor.execute("ALTER TABLE livros ADD COLUMN quantidade INTEGER DEFAULT 1")
    except Exception:
        pass  

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


cursor.execute("""
CREATE TABLE IF NOT EXISTS punicoes (
    usuario TEXT PRIMARY KEY,
    ate TEXT
)
""")

conn.commit()
conn.close()



def usuario_punido(usuario):
    conn = sqlite3.connect("biblioteca.db")
    cursor = conn.cursor()
    cursor.execute("SELECT ate FROM punicoes WHERE usuario = ?", (usuario,))
    resultado = cursor.fetchone()
    conn.close()

    if not resultado:
        return False

    data_fim = datetime.strptime(resultado[0], "%d/%m/%Y")
    hoje = datetime.now()

    return hoje <= data_fim


def punir_usuario(usuario, dias=3):
    data_punicao = (datetime.now() + timedelta(days=dias)).strftime("%d/%m/%Y")

    conn = sqlite3.connect("biblioteca.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO punicoes (usuario, ate)
        VALUES (?, ?)
        ON CONFLICT(usuario) DO UPDATE SET ate = ?
    """, (usuario, data_punicao, data_punicao))
    conn.commit()
    conn.close()



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



def abrir_tela_comprar_emprestar():
    tela = tk.Toplevel()
    tela.title("Gerenciar Livros")
    tela.geometry("520x480")
    tela.config(bg="#2E2E2E")

    tk.Label(tela, text="Gerenciar Livros", font=("Arial", 16, "bold"), bg="#2E2E2E", fg="white").pack(pady=10)

    frame = tk.Frame(tela, bg="#2E2E2E")
    frame.pack(pady=10)

    lista = tk.Listbox(frame, width=70, height=12)
    lista.pack(side=tk.LEFT, padx=5)

    scroll = tk.Scrollbar(frame, command=lista.yview)
    scroll.pack(side=tk.RIGHT, fill=tk.Y)
    lista.config(yscrollcommand=scroll.set)

    def carregar_livros():
        lista.delete(0, tk.END)
        conn = sqlite3.connect("biblioteca.db")
        cursor = conn.cursor()
        cursor.execute("SELECT titulo, quantidade FROM livros ORDER BY titulo")
        for row in cursor.fetchall():
            titulo, qt = row
            if qt and qt > 0:
                lista.insert(tk.END, f"{titulo} ({qt} disponíveis)")
            else:
                lista.insert(tk.END, f"{titulo} (esgotado)")
        conn.close()

    carregar_livros()

    tk.Label(tela, text="Selecione uma opção:", bg="#2E2E2E", fg="white", font=("Arial", 11)).pack(pady=5)

    opcao_var = tk.StringVar(value="Compra")
    for texto in ["Compra", "Empréstimo", "Devolução"]:
        tk.Radiobutton(tela, text=texto, variable=opcao_var, value=texto, bg="#2E2E2E", fg="white").pack(anchor="w")

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

        item_text = lista.get(selecionado)

        livro = item_text.split(" (")[0]
        opcao = opcao_var.get()
        conn = sqlite3.connect("biblioteca.db")
        cursor = conn.cursor()

       
        if opcao == "Empréstimo":
            if usuario_punido(usuario):
                conn.close()
                messagebox.showerror("Punição ativa", f"{usuario} está punido e não pode emprestar livros.")
                return

           
            cursor.execute("""
                SELECT data_devolucao FROM emprestimos
                WHERE usuario = ? AND status = 'Emprestado'
            """, (usuario,))
            emprestimos_user = cursor.fetchall()

            hoje = datetime.now()

            for emp in emprestimos_user:
                data_dev = datetime.strptime(emp[0], "%d/%m/%Y")
                if hoje > data_dev:
                    punir_usuario(usuario, dias=3)
                    conn.close()
                    messagebox.showerror("Atraso detectado",
                                         f"{usuario} tinha um livro atrasado e foi punido por 3 dias.")
                    return

       
        cursor.execute("SELECT quantidade FROM livros WHERE titulo = ?", (livro,))
        resultado_qt = cursor.fetchone()
        if not resultado_qt:
            conn.close()
            messagebox.showerror("Erro", "Livro não encontrado no banco.")
            return
        quantidade_atual = resultado_qt[0] or 0

      
        if opcao == "Compra":
            if quantidade_atual <= 0:
                
                conn.close()
                messagebox.showwarning("Indisponível", f"O livro '{livro}' está esgotado e não pode ser comprado.")
                return
           
            data_compra = datetime.now().strftime("%d/%m/%Y %H:%M")
            cursor.execute("INSERT INTO compras (usuario, livro, data_compra) VALUES (?, ?, ?)",
                           (usuario, livro, data_compra))
            cursor.execute("UPDATE livros SET quantidade = quantidade - 1 WHERE titulo = ?", (livro,))
            conn.commit()
            messagebox.showinfo("Compra", f"Livro '{livro}' foi comprado e estoque atualizado.")
            carregar_livros()

       
        elif opcao == "Empréstimo":
            if quantidade_atual <= 0:
                conn.close()
                messagebox.showwarning("Indisponível", f"O livro '{livro}' está esgotado e não pode ser emprestado.")
                return
            data_emprestimo = datetime.now().strftime("%d/%m/%Y")
            data_devolucao = (datetime.now() + timedelta(days=7)).strftime("%d/%m/%Y")
            cursor.execute("""
                INSERT INTO emprestimos (usuario, livro, data_emprestimo, data_devolucao, status)
                VALUES (?, ?, ?, ?, ?)
            """, (usuario, livro, data_emprestimo, data_devolucao, "Emprestado"))
            cursor.execute("UPDATE livros SET quantidade = quantidade - 1 WHERE titulo = ?", (livro,))
            conn.commit()
            messagebox.showinfo("Empréstimo", f"Livro '{livro}' emprestado a {usuario} até {data_devolucao}.")
            carregar_livros()

    
        elif opcao == "Devolução":
            cursor.execute("SELECT * FROM emprestimos WHERE usuario = ? AND livro = ? AND status = 'Emprestado'",
                           (usuario, livro))
            emprestimo = cursor.fetchone()
            if emprestimo:
                cursor.execute("UPDATE emprestimos SET status = 'Devolvido' WHERE id = ?", (emprestimo[0],))
                cursor.execute("UPDATE livros SET quantidade = quantidade + 1 WHERE titulo = ?", (livro,))
                conn.commit()
                messagebox.showinfo("Devolução", f"Livro '{livro}' devolvido com sucesso! Estoque atualizado.")
                carregar_livros()
            else:
                messagebox.showwarning("Aviso", "Nenhum empréstimo ativo encontrado para este livro.")

        conn.close()

    tk.Button(tela, text="Confirmar", command=confirmar_acao, bg="lightgreen", width=20).pack(pady=10)
    tk.Button(tela, text="Fechar", command=tela.destroy, bg="tomato", fg="white", width=10).pack(pady=5)



def abrir_perfil_usuario(usuario):
    perfil = tk.Toplevel()
    perfil.title("Perfil do Usuário")
    perfil.geometry("420x460")
    perfil.config(bg="#2E2E2E")

    tk.Label(perfil, text=f"Perfil de {usuario}", font=("Arial", 14, "bold"), bg="#2E2E2E", fg="white").pack(pady=10)

 
    conn = sqlite3.connect("biblioteca.db")
    cursor = conn.cursor()
    cursor.execute("SELECT ate FROM punicoes WHERE usuario = ?", (usuario,))
    pun = cursor.fetchone()
    if pun:
        tk.Label(perfil, text=f"⚠ Punido até {pun[0]}", fg="red", bg="#2E2E2E",
                 font=("Arial", 11, "bold")).pack(pady=5)

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



def abrir_tela_principal(usuario):
    tela_login.withdraw()
    tela_principal = tk.Toplevel()
    tela_principal.title("Biblioteca - Catálogo de Livros")
    tela_principal.geometry("470x480")
    tela_principal.config(bg="#2E2E2E")

    tk.Label(tela_principal, text=f"Bem-vindo, {usuario}!", font=("Arial", 14), bg="#2E2E2E", fg="white").pack(pady=10)
    tk.Label(tela_principal, text="📚 Catálogo de Livros", font=("Arial", 12, "bold"), bg="#2E2E2E", fg="lightblue").pack(pady=5)

    lista = tk.Listbox(tela_principal, width=60, height=12)
    lista.pack(pady=10)

    def carregar_livros():
        lista.delete(0, tk.END)
        conn = sqlite3.connect("biblioteca.db")
        cursor = conn.cursor()
        
        cursor.execute("SELECT titulo, quantidade FROM livros WHERE quantidade > 0 ORDER BY titulo")
        for row in cursor.fetchall():
            titulo, qt = row
            lista.insert(tk.END, titulo)  
        conn.close()

    carregar_livros()


    def mostrar_descricao_evento(event):
        selecionado = lista.curselection()
        if not selecionado:
            return
        livro = lista.get(selecionado)

        conn = sqlite3.connect("biblioteca.db")
        cursor = conn.cursor()
        cursor.execute("SELECT descricao, quantidade FROM livros WHERE titulo = ?", (livro,))
        resultado = cursor.fetchone()
        conn.close()

        descricao = resultado[0] if (resultado and resultado[0]) else "(sem descrição)"
        quantidade = resultado[1] if resultado else 0

        messagebox.showinfo(f"{livro} — Disponibilidade", f"Descrição: {descricao}\n\nQuantidade disponível: {quantidade}")

    lista.bind("<<ListboxSelect>>", mostrar_descricao_evento)

    def adicionar_livro():
        novo_livro = simpledialog.askstring("Adicionar Livro", "Digite o nome do livro:")
        if not novo_livro:
            return
        quantidade = simpledialog.askinteger("Quantidade", "Quantidade inicial (inteiro >=1):", minvalue=1, initialvalue=1)
        if not quantidade:
            quantidade = 1
        conn = sqlite3.connect("biblioteca.db")
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO livros (titulo, quantidade) VALUES (?, ?)", (novo_livro, quantidade))
            conn.commit()
            messagebox.showinfo("Sucesso", f"Livro '{novo_livro}' adicionado com sucesso ({quantidade} unidades).")
        except sqlite3.IntegrityError:
            
            cursor.execute("SELECT quantidade FROM livros WHERE titulo = ?", (novo_livro,))
            atual = cursor.fetchone()
            if atual:
                atual_qt = atual[0] or 0
                if messagebox.askyesno("Livro existe", f"'{novo_livro}' já existe com {atual_qt} unidades.\nDeseja adicionar mais {quantidade}?"):
                    cursor.execute("UPDATE livros SET quantidade = quantidade + ? WHERE titulo = ?", (quantidade, novo_livro))
                    conn.commit()
                    messagebox.showinfo("Sucesso", f"Estoque atualizado: {novo_livro} agora tem {atual_qt + quantidade} unidades.")
        conn.close()
        carregar_livros()

    def remover_livro():
        selecionado = lista.curselection()
        if not selecionado:
            messagebox.showwarning("Aviso", "Selecione um livro para remover.")
            return
        livro = lista.get(selecionado)
        if messagebox.askyesno("Confirmar", f"Remover '{livro}' (apaga registro)?"):
            conn = sqlite3.connect("biblioteca.db")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM livros WHERE titulo = ?", (livro,))
            conn.commit()
            conn.close()
            carregar_livros()
            messagebox.showinfo("Removido", f"Livro '{livro}' foi removido do sistema.")

    def descricao_livro():
        selecionado = lista.curselection()
        if not selecionado:
            messagebox.showwarning("Aviso", "Selecione um livro primeiro.")
            return
        livro = lista.get(selecionado)
        conn = sqlite3.connect("biblioteca.db")
        cursor = conn.cursor()
        cursor.execute("SELECT descricao, quantidade FROM livros WHERE titulo = ?", (livro,))
        resultado = cursor.fetchone()
        if resultado and resultado[0]:
            messagebox.showinfo(f"Descrição - {livro}", f"{resultado[0]}\n\nQuantidade disponível: {resultado[1]}")
        else:
            nova_desc = simpledialog.askstring("Adicionar Descrição", f"Adicione uma descrição para '{livro}':")
            if nova_desc is not None:
                cursor.execute("UPDATE livros SET descricao = ? WHERE titulo = ?", (nova_desc, livro))
                conn.commit()
                messagebox.showinfo("Sucesso", "Descrição adicionada com sucesso!")
        conn.close()
        carregar_livros()

    frame_botoes = tk.Frame(tela_principal, bg="#2E2E2E")
    frame_botoes.pack(pady=5)

    tk.Button(frame_botoes, text="Adicionar Livro", command=adicionar_livro, bg="green", fg="white", width=15).grid(row=0, column=0, padx=5)
    tk.Button(frame_botoes, text="Remover Livro", command=remover_livro, bg="red", fg="white", width=15).grid(row=0, column=1, padx=5)
    tk.Button(frame_botoes, text="Descrição", command=descricao_livro, bg="blue", fg="white", width=15).grid(row=0, column=2, padx=5)

    tk.Button(tela_principal, text="Gerenciar Livros", command=abrir_tela_comprar_emprestar, bg="lightblue", fg="white", width=20).pack(pady=10)

    tk.Button(tela_principal, text="Perfil", command=lambda: abrir_perfil_usuario(usuario), bg="purple", fg="white", width=12).pack(pady=5)

    tk.Button(tela_principal, text="Sair", command=lambda: [tela_principal.destroy(), tela_login.deiconify()], bg="tomato", fg="white", width=10).pack(pady=10)


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
