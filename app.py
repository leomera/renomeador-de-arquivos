import os
import re
import shutil
import string
import logging
from datetime import datetime
from typing import List, Tuple, Optional
from abc import ABC, abstractmethod
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading

class RenameOption(ABC):
    """Classe base abstrata para opções de renomeação."""
    
    @abstractmethod
    def preview(self, files: List[str], suffix: str) -> List[Tuple[str, str]]:
        """Gera uma pré-visualização das renomeações com base no sufixo."""
        pass
    
    def execute(self, files: List[str], suffix: str) -> List[Tuple[str, str]]:
        """Executa as renomeações (padrão: mesma lógica da pré-visualização)."""
        return self.preview(files, suffix)

class AddZeroAfterUnderscore(RenameOption):
    """Adiciona '0' após '_' (ex.: exemplo_1.jpg -> exemplo_01.jpg)."""
    
    def preview(self, files: List[str], suffix: str) -> List[Tuple[str, str]]:
        changes = []
        for f in files:
            if suffix in f:
                name, ext = os.path.splitext(f)
                parts = name.split(suffix)
                if len(parts) >= 2 and parts[1] and parts[1][0].isdigit():
                    new_suffix = "0" + parts[1]
                    new_name = f"{parts[0]}{suffix}{new_suffix}{ext}"
                    changes.append((f, new_name))
        return changes

class RemoveUnderscoreOne(RenameOption):
    """Remove '_1' do nome (ex.: exemplo_1.jpg -> exemplo.jpg)."""
    
    def preview(self, files: List[str], suffix: str) -> List[Tuple[str, str]]:
        return [(f, f.replace(f"{suffix}1", "")) for f in files if f"{suffix}1" in f]

class IncrementSuffixByTwo(RenameOption):
    """Incrementa sufixo numérico em +2 (ex.: exemplo_1.jpg -> exemplo_3.jpg)."""
    
    def preview(self, files: List[str], suffix: str) -> List[Tuple[str, str]]:
        changes = []
        for f in files:
            if suffix in f:
                name, ext = os.path.splitext(f)
                parts = name.split(suffix)
                if len(parts) >= 2 and parts[-1].isdigit():
                    num = int(parts[-1]) + 2
                    new_name = f"{suffix.join(parts[:-1])}{suffix}{num}{ext}"
                    changes.append((f, new_name))
        return changes

class SequenceZeroPadding(RenameOption):
    """Converte sufixo para sequência 00, 01, 02... (ex.: exemplo_1.jpg -> exemplo_00.jpg)."""
    
    def preview(self, files: List[str], suffix: str) -> List[Tuple[str, str]]:
        changes = []
        for f in files:
            if suffix in f:
                name, ext = os.path.splitext(f)
                parts = name.split(suffix)
                if len(parts) >= 2 and parts[-1].isdigit():
                    base = suffix.join(parts[:-1])
                    num = int(parts[-1])
                    new_num = f"{num-1:02d}" if num > 0 else "00"
                    new_name = f"{base}{suffix}{new_num}{ext}"
                    changes.append((f, new_name))
        return changes

class PrefixExtWithLetters(RenameOption):
    """Converte sufixo numérico para letras (ex.: 773827336223_1.jpg -> EXT_773827336223_A.jpg)."""
    
    def preview(self, files: List[str], suffix: str) -> List[Tuple[str, str]]:
        changes = []
        for f in files:
            if suffix in f:
                name, ext = os.path.splitext(f)
                parts = name.split(suffix)
                if len(parts) >= 2 and parts[-1].isdigit():
                    base = parts[0]
                    num = int(parts[-1])
                    letra = (chr(num + 64) if num <= 26 else
                             chr((num // 26) + 64) + chr((num % 26) + 64) if num % 26 != 0 else
                             chr((num // 26) - 1 + 64) + "Z")
                    new_name = f"EXT_{base}{suffix}{letra}{ext}"
                    changes.append((f, new_name))
        return changes

class DecrementSuffix(RenameOption):
    """Diminui sufixo numérico em 1 (ex.: 73683297483_2.jpg -> 73683297483_1.jpg)."""
    
    def preview(self, files: List[str], suffix: str) -> List[Tuple[str, str]]:
        changes = []
        for f in files:
            if suffix in f:
                name, ext = os.path.splitext(f)
                parts = name.split(suffix)
                if len(parts) >= 2 and parts[-1].isdigit():
                    base = suffix.join(parts[:-1])
                    num = max(0, int(parts[-1]) - 1)
                    new_name = f"{base}{suffix}{num}{ext}"
                    changes.append((f, new_name))
        return changes

class ReplaceUnderscoreWithDot(RenameOption):
    """Substitui '_' por '.' (ex.: exemplo_1.jpg -> exemplo.1.jpg)."""
    
    def preview(self, files: List[str], suffix: str) -> List[Tuple[str, str]]:
        valid_extensions = {'.jpg', '.jpeg', '.png', '.webp'}
        changes = []
        for f in files:
            name, ext = os.path.splitext(f)
            if suffix in f and ext.lower() in valid_extensions:
                new_name = name.replace(suffix, ".") + ext
                changes.append((f, new_name))
        return changes

class RemoveLastCharBeforeSeparator(RenameOption):
    """Remove o último caractere antes de '_' ou '.' (ex.: exemplo_1.jpg -> exempl_1.jpg)."""
    
    def preview(self, files: List[str], suffix: str) -> List[Tuple[str, str]]:
        changes = []
        for f in files:
            if not f.lower().endswith('.jpg'):
                continue
            name, ext = os.path.splitext(f)
            if suffix in name:
                parts = name.split(suffix, 1)
                if len(parts[0]) > 0:
                    new_name = parts[0][:-1] + suffix + parts[1] + ext
                    changes.append((f, new_name))
        return changes

class CustomPrefixOrSuffix(RenameOption):
    """Adiciona um prefixo e/ou sufixo personalizado fornecido pelo usuário."""
    
    def __init__(self, prefix: str = "", suffix: str = "", apply_prefix: bool = True, apply_suffix: bool = False):
        self.prefix = prefix
        self.suffix = suffix
        self.apply_prefix = apply_prefix
        self.apply_suffix = apply_suffix
    
    def preview(self, files: List[str], suffix: str) -> List[Tuple[str, str]]:
        changes = []
        for f in files:
            if suffix not in f:
                continue
            name, ext = os.path.splitext(f)
            new_name = name
            if self.apply_prefix and self.prefix:
                new_name = self.prefix + new_name
            if self.apply_suffix and self.suffix:
                new_name = new_name + self.suffix
            new_name = new_name + ext
            changes.append((f, new_name))
        return changes

class ReplaceUnderscoreNumberWithLetter(RenameOption):
    """Substitui '_numero' por letra do alfabeto (ex.: 12345_1.jpg -> 12345A.jpg)."""
    
    def preview(self, files: List[str], suffix: str) -> List[Tuple[str, str]]:
        changes = []
        for f in files:
            if suffix in f:
                name, ext = os.path.splitext(f)
                parts = name.split(suffix)
                if len(parts) >= 2 and parts[-1].isdigit():
                    base = suffix.join(parts[:-1])
                    num = int(parts[-1])
                    if num > 0 and num <= 26:  # Limita a A-Z
                        letter = chr(64 + num)  # 1 -> A, 2 -> B, etc.
                        new_name = f"{base}{letter}{ext}"
                        changes.append((f, new_name))
        return changes

class ReplaceNumberWithUnderscoreLetter(RenameOption):
    """Substitui 'numero' após underscore por '_letra' (ex.: 12345_1.jpg -> 12345_A.jpg)."""
    
    def preview(self, files: List[str], suffix: str) -> List[Tuple[str, str]]:
        changes = []
        for f in files:
            if suffix in f:
                name, ext = os.path.splitext(f)
                parts = name.split(suffix)
                if len(parts) >= 2 and parts[-1].isdigit():
                    base = suffix.join(parts[:-1])
                    num = int(parts[-1])
                    if num > 0 and num <= 26:  # Limita a A-Z
                        letter = chr(64 + num)  # 1 -> A, 2 -> B, etc.
                        new_name = f"{base}{suffix}{letter}{ext}"
                        changes.append((f, new_name))
        return changes

class AddZeroPrefixAndGallerySuffix(RenameOption):
    """Adiciona '00' ao prefixo e renomeia sufixos: _1 remove _1, _2+ adiciona _gNN (ex.: 12345_1.jpg -> 0012345.jpg, 12345_2.jpg -> 0012345_g01.jpg)."""
    
    def preview(self, files: List[str], suffix: str) -> List[Tuple[str, str]]:
        changes = []
        for f in sorted(files):  # Ordenar para garantir consistência
            if suffix in f:
                name, ext = os.path.splitext(f)
                parts = name.split(suffix)
                if len(parts) >= 2 and parts[-1].isdigit():
                    base = suffix.join(parts[:-1])
                    num = int(parts[-1])
                    if num == 1:
                        # Para _1: adicionar 00 no início e remover _1
                        new_name = f"00{base}{ext}"
                    elif num >= 2:
                        # Para _2+: adicionar 00 no início e _gNN (NN = num-1, com dois dígitos)
                        gallery_num = f"{num-1:02d}"
                        new_name = f"00{base}{suffix}g{gallery_num}{ext}"
                    changes.append((f, new_name))
        return changes

class AddPAfterProductNumber(RenameOption):
    """Adiciona 'P' após o número do produto (ex.: 12345_1.jpg -> 12345P_1.jpg)."""
    
    def preview(self, files: List[str], suffix: str) -> List[Tuple[str, str]]:
        changes = []
        for f in files:
            if suffix in f:
                name, ext = os.path.splitext(f)
                parts = name.split(suffix)
                if len(parts) >= 2 and parts[-1].isdigit():
                    base = suffix.join(parts[:-1])
                    num = parts[-1]
                    new_name = f"{base}P{suffix}{num}{ext}"
                    changes.append((f, new_name))
        return changes

class IncrementSuffixByOne(RenameOption):
    """Incrementa sufixo numérico em +1 (ex.: 12345_1.jpg -> 12345_2.jpg)."""
    
    def preview(self, files: List[str], suffix: str) -> List[Tuple[str, str]]:
        changes = []
        for f in files:
            if suffix in f:
                name, ext = os.path.splitext(f)
                parts = name.split(suffix)
                if len(parts) >= 2 and parts[-1].isdigit():
                    num = int(parts[-1]) + 1
                    new_name = f"{suffix.join(parts[:-1])}{suffix}{num}{ext}"
                    changes.append((f, new_name))
        return changes

class FlywheelManager:
    """Gerenciador de arquivos com interface gráfica para remoção e renomeação."""
    
    def __init__(self, root: tk.Tk):
        """Inicializa a aplicação com a janela principal."""
        self.root = root
        self.root.title("Gerenciador de Arquivos - Flywheel")
        self.current_dir = tk.StringVar(value=os.getcwd())
        self.theme = tk.StringVar(value="dark")
        
        # Inicializar variáveis de extensões
        self.ext_jpg = tk.BooleanVar(value=True)
        self.ext_png = tk.BooleanVar(value=False)
        self.ext_jpeg = tk.BooleanVar(value=False)
        self.ext_webp = tk.BooleanVar(value=False)
        
        # Variáveis para renomeação personalizada
        self.custom_prefix = tk.StringVar(value="")
        self.custom_suffix = tk.StringVar(value="")
        self.apply_prefix = tk.BooleanVar(value=True)
        self.apply_suffix = tk.BooleanVar(value=False)
        
        # Variável para sufixo na renomeação
        self.rename_suffix_var = tk.StringVar(value="_")
        
        # Lista para armazenar mudanças editadas na pré-visualização
        self.edited_changes = []
        
        # Configurar log
        logging.basicConfig(filename='flywheel_log.txt', level=logging.INFO,
                           format='%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        
        # Configurar janela e widgets
        self._setup_window_geometry()
        self._setup_styles()
        self._create_widgets()
        
        # Opções de renomeação
        self.rename_options = {
            1: AddZeroAfterUnderscore(),
            2: RemoveUnderscoreOne(),
            3: IncrementSuffixByTwo(),
            4: SequenceZeroPadding(),
            5: PrefixExtWithLetters(),
            6: DecrementSuffix(),
            7: ReplaceUnderscoreWithDot(),
            8: RemoveLastCharBeforeSeparator(),
            9: CustomPrefixOrSuffix(self.custom_prefix.get(), self.custom_suffix.get(),
                                 self.apply_prefix.get(), self.apply_suffix.get()),
            10: ReplaceUnderscoreNumberWithLetter(),
            11: ReplaceNumberWithUnderscoreLetter(),
            12: AddZeroPrefixAndGallerySuffix(),
            13: AddPAfterProductNumber(),
            14: IncrementSuffixByOne()
        }

    def _setup_window_geometry(self) -> None:
        """Configura o tamanho e posição da janela."""
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = int(screen_width * 0.7)
        window_height = int(screen_height * 0.7)
        x_position = (screen_width - window_width) // 2
        y_position = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")
        self.root.resizable(True, True)
        self.root.minsize(780, 640)

    def _setup_styles(self) -> None:
        """Configura os estilos da interface."""
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self._apply_theme()

    def _apply_theme(self) -> None:
        """Aplica o tema claro ou escuro."""
        if self.theme.get() == "dark":
            bg, fg, button_bg = '#222222', '#00FF00', '#007BFF'
        else:
            bg, fg, button_bg = '#F0F0F0', '#000000', '#005BB5'
        
        self.root.configure(bg=bg)
        self.style.configure('TFrame', background=bg)
        self.style.configure('TButton', background=button_bg, foreground='white', font=('Arial', 10, 'bold'))
        self.style.configure('TLabel', background=bg, foreground=fg, font=('Arial', 11))
        self.style.configure('Header.TLabel', background=bg, foreground=fg, font=('Arial', 16, 'bold'))
        self.style.configure('Directory.TLabel', background=bg, foreground=fg, font=('Arial', 10))
        self.style.configure('Treeview', background=bg, foreground=fg, fieldbackground=bg, selectbackground=bg, selectforeground=fg)
        self.style.configure('Treeview.Heading', background=button_bg, foreground='white')
        self.style.configure('Listbox', background=bg, foreground=fg, font=('Arial', 11))

    def _create_widgets(self) -> None:
        """Cria os widgets da interface."""
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        main_frame = ttk.Frame(self.root)
        main_frame.grid(row=0, column=0, sticky='nsew', padx=20, pady=9)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(4, weight=1)

        # Título
        ttk.Label(main_frame, text="Gerenciador de Arquivos - Flywheel", style='Header.TLabel').grid(row=0, column=0, sticky='n', pady=(0, 2))

        # Botão Sobre
        ttk.Button(main_frame, text="Sobre", style='TLabel', command=self.show_about).grid(row=1, column=0, sticky='n', pady=(4, 10))

        # Seleção de diretório
        dir_frame = ttk.Frame(main_frame)
        dir_frame.grid(row=2, column=0, sticky='ew', pady=(0, 0))
        dir_frame.grid_columnconfigure(1, weight=1)
        ttk.Label(dir_frame, text="Diretório atual:", style='TLabel').grid(row=0, column=0, sticky='w', padx=(0, 10))
        ttk.Entry(dir_frame, textvariable=self.current_dir, width=60).grid(row=0, column=1, sticky='ew', padx=(0, 10))
        ttk.Button(dir_frame, text="Selecionar pasta", command=self.browse_directory).grid(row=0, column=2, sticky='w')
        ttk.Button(dir_frame, text="Alternar Tema", command=self.toggle_theme).grid(row=0, column=3, sticky='w', padx=(10, 0))

        # Status do diretório
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=3, column=0, sticky='ew', pady=(0, 20))
        self.dir_status = ttk.Label(status_frame, text=f"Pasta selecionada: {self.current_dir.get()}", style='Directory.TLabel')
        self.dir_status.grid(row=0, column=0, sticky='w')

        # Notebook
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=4, column=0, sticky='nsew')

        # Abas
        self.remove_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.remove_tab, text="Remover Arquivos")
        self._setup_remove_tab()

        self.rename_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.rename_tab, text="Renomear Arquivos")
        self._setup_rename_tab()

    def toggle_theme(self) -> None:
        """Alterna entre tema claro ou escuro."""
        self.theme.set("light" if self.theme.get() == "dark" else "dark")
        self._apply_theme()

    def _setup_remove_tab(self) -> None:
        """Configura a aba de remoção de arquivos."""
        if not hasattr(self, 'ext_jpg'):
            raise AttributeError("Variáveis de extensões não inicializadas. Verifique o método __init__.")
        
        self.remove_tab.grid_columnconfigure(0, weight=1)
        self.remove_tab.grid_rowconfigure(4, weight=1)

        # Extensões
        ext_frame = ttk.Frame(self.remove_tab)
        ext_frame.grid(row=0, column=0, sticky='ew', pady=10, padx=4)
        ttk.Label(ext_frame, text="Extensões permitidas:", style='TLabel').grid(row=0, column=0, sticky='w', pady=2, padx=7)
        ttk.Checkbutton(ext_frame, text=".jpg", variable=self.ext_jpg).grid(row=0, column=1, sticky='w', padx=(0, 7))
        ttk.Checkbutton(ext_frame, text=".png", variable=self.ext_png).grid(row=0, column=2, sticky='w', padx=(0, 7))
        ttk.Checkbutton(ext_frame, text=".jpeg", variable=self.ext_jpeg).grid(row=0, column=3, sticky='w', padx=(0, 7))
        ttk.Checkbutton(ext_frame, text=".webp", variable=self.ext_webp).grid(row=0, column=4, sticky='w', padx=(0, 7))

        # Sufixo
        suffix_frame = ttk.Frame(self.remove_tab)
        suffix_frame.grid(row=1, column=0, sticky='ew', pady=10, padx=10)
        ttk.Label(suffix_frame, text="Selecione o tipo de sufixo:", style='TLabel').grid(row=0, column=0, sticky='w', pady=2, padx=1)
        self.suffix_var = tk.StringVar(value="_")
        for i, (text, value) in enumerate([("Arquivos com \"_\"", "_"), ("Arquivos com \"-\"", "-"), ("Arquivos com \".\"", ".")]):
            ttk.Radiobutton(suffix_frame, text=text, variable=self.suffix_var, value=value).grid(row=0, column=i+1, sticky='w', padx=(0, 7))

        # Número inicial
        number_frame = ttk.Frame(self.remove_tab)
        number_frame.grid(row=2, column=0, sticky='ew', pady=10, padx=10)
        ttk.Label(number_frame, text="Remover arquivos a partir do sufixo:", style='TLabel').grid(row=0, column=0, sticky='w', pady=0, padx=2)
        self.number_var = tk.IntVar(value=1)
        number_scale = ttk.Scale(number_frame, from_=1, to=20, variable=self.number_var, orient=tk.HORIZONTAL, length=300)
        number_scale.grid(row=1, column=0, sticky='w', padx=5)
        ttk.Label(number_frame, textvariable=self.number_var, style='TLabel').grid(row=1, column=1, padx=10)
        number_scale.bind("<Motion>", lambda e: self.number_var.set(int(number_scale.get())))

        # Botões de execução
        execute_frame = ttk.Frame(self.remove_tab)
        execute_frame.grid(row=3, column=0, sticky='ew', pady=10, padx=10)
        ttk.Button(execute_frame, text="Pré-visualizar", command=self.preview_remove).grid(row=0, column=0, padx=10)
        ttk.Button(execute_frame, text="Remover Arquivos", command=self.execute_remove).grid(row=0, column=1, padx=10)
        ttk.Button(execute_frame, text="Desfazer Remoção", command=self.undo_remove).grid(row=0, column=2, padx=10)

        # Pré-visualização com Listbox
        preview_frame = ttk.LabelFrame(self.remove_tab, text="Pré-visualização dos arquivos a serem removidos:")
        preview_frame.grid(row=4, column=0, sticky='nsew', pady=10, padx=10)
        preview_frame.grid_columnconfigure(0, weight=1)
        preview_frame.grid_rowconfigure(0, weight=1)
        self.remove_listbox = tk.Listbox(preview_frame, font=('Arial', 11))
        self.remove_listbox.grid(row=0, column=0, sticky='nsew')
        scroll = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=self.remove_listbox.yview)
        scroll.grid(row=0, column=1, sticky='ns')
        self.remove_listbox.configure(yscrollcommand=scroll.set)

    def _setup_rename_tab(self) -> None:
        """Configura a aba de renomeação de arquivos."""
        if not hasattr(self, 'ext_jpg'):
            raise AttributeError("Variáveis de extensões não inicializadas. Verifique o método __init__.")
        
        self.rename_tab.grid_columnconfigure(0, weight=1)
        self.rename_tab.grid_rowconfigure(5, weight=1)

        # Extensões
        ext_frame = ttk.Frame(self.rename_tab)
        ext_frame.grid(row=0, column=0, sticky='ew', pady=10, padx=4)
        ttk.Label(ext_frame, text="Extensões permitidas:", style='TLabel').grid(row=0, column=0, sticky='w', pady=2, padx=7)
        ttk.Checkbutton(ext_frame, text=".jpg", variable=self.ext_jpg).grid(row=0, column=1, sticky='w', padx=(0, 7))
        ttk.Checkbutton(ext_frame, text=".png", variable=self.ext_png).grid(row=0, column=2, sticky='w', padx=(0, 7))
        ttk.Checkbutton(ext_frame, text=".jpeg", variable=self.ext_jpeg).grid(row=0, column=3, sticky='w', padx=(0, 7))
        ttk.Checkbutton(ext_frame, text=".webp", variable=self.ext_webp).grid(row=0, column=4, sticky='w', padx=(0, 7))

        # Sufixo
        suffix_frame = ttk.Frame(self.rename_tab)
        suffix_frame.grid(row=1, column=0, sticky='ew', pady=10, padx=10)
        ttk.Label(suffix_frame, text="Selecione o tipo de sufixo:", style='TLabel').grid(row=0, column=0, sticky='w', pady=2, padx=1)
        for i, (text, value) in enumerate([("Arquivos com \"_\"", "_"), ("Arquivos com \"-\"", "-"), ("Arquivos com \".\"", ".")]):
            ttk.Radiobutton(suffix_frame, text=text, variable=self.rename_suffix_var, value=value).grid(row=0, column=i+1, sticky='w', padx=(0, 7))

        # Opções de renomeação com Combobox
        options_frame = ttk.Frame(self.rename_tab)
        options_frame.grid(row=2, column=0, sticky='ew', pady=10, padx=10)
        ttk.Label(options_frame, text="Selecione a opção de renomeação:", style='TLabel').grid(row=0, column=0, sticky='w', pady=2)
        self.rename_var = tk.IntVar(value=1)
        options = [
            "Adicionar 0 após '_' (ex.: exemplo_1.jpg → exemplo_01.jpg)",
            "Remover '_1' (ex.: exemplo_1.jpg → exemplo.jpg)",
            "Incrementar sufixo em +2 (ex.: exemplo_1.jpg → exemplo_3.jpg)",
            "Sequência 00, 01, 02... (ex.: exemplo_1.jpg → exemplo_00.jpg)",
            "Prefixo EXT_ e letras (ex.: 773827336223_1.jpg → EXT_773827336223_A.jpg)",
            "Diminuir sufixo em 1 (ex.: 73683297483_2.jpg → 73683297483_1.jpg)",
            "Substituir '_' por '.' (ex.: exemplo_1.jpg → exemplo.1.jpg)",
            "Remover último caractere antes de '_' ou '.' (ex.: exemplo_1.jpg → exempl_1.jpg)",
            "Prefixo/Sufixo personalizado (definido pelo usuário)",
            "Substituir '_numero' por letra (ex.: 12345_1.jpg → 12345A.jpg)",
            "Substituir 'numero' por '_letra' (ex.: 12345_1.jpg → 12345_A.jpg)",
            "Adicionar '00' e '_gNN' para _2+ (ex.: 12345_1.jpg → 0012345.jpg, 12345_2.jpg → 0012345_g01.jpg)",
            "Adicionar 'P' após o número do produto (ex.: 12345_1.jpg → 12345P_1.jpg)",
            "Incrementar sufixo em +1 (ex.: 12345_1.jpg → 12345_2.jpg)"
        ]
        self.rename_combobox = ttk.Combobox(options_frame, values=options, state='readonly', width=70)
        self.rename_combobox.grid(row=1, column=0, sticky='ew', pady=2)
        self.rename_combobox.current(0)
        self.rename_combobox.bind('<<ComboboxSelected>>', self._update_rename_options)

        # Frame para opções personalizadas (prefixo/sufixo)
        self.custom_options_frame = ttk.Frame(self.rename_tab)
        self.custom_options_frame.grid(row=3, column=0, sticky='ew', pady=5, padx=10)
        ttk.Label(self.custom_options_frame, text="Prefixo:", style='TLabel').grid(row=0, column=0, sticky='w', padx=5)
        ttk.Entry(self.custom_options_frame, textvariable=self.custom_prefix).grid(row=0, column=1, sticky='ew', padx=5)
        ttk.Label(self.custom_options_frame, text="Sufixo:", style='TLabel').grid(row=1, column=0, sticky='w', padx=5)
        ttk.Entry(self.custom_options_frame, textvariable=self.custom_suffix).grid(row=1, column=1, sticky='ew', padx=5)
        ttk.Checkbutton(self.custom_options_frame, text="Aplicar prefixo", variable=self.apply_prefix).grid(row=0, column=2, sticky='w', padx=5)
        ttk.Checkbutton(self.custom_options_frame, text="Aplicar sufixo", variable=self.apply_suffix).grid(row=1, column=2, sticky='w', padx=5)
        self.custom_options_frame.grid_remove()  # Esconder por padrão

        # Botões de execução
        execute_frame = ttk.Frame(self.rename_tab)
        execute_frame.grid(row=4, column=0, sticky='ew', pady=10, padx=10)
        ttk.Button(execute_frame, text="Pré-visualizar", command=self.preview_rename).grid(row=0, column=0, padx=10)
        ttk.Button(execute_frame, text="Renomear Arquivos", command=self.execute_rename).grid(row=0, column=1, padx=10)

        # Pré-visualização com Treeview
        preview_frame = ttk.LabelFrame(self.rename_tab, text="Pré-visualização dos arquivos a serem renomeados:")
        preview_frame.grid(row=5, column=0, sticky='nsew', pady=10, padx=10)
        preview_frame.grid_columnconfigure(0, weight=1)
        preview_frame.grid_rowconfigure(0, weight=1)
        self.rename_treeview = ttk.Treeview(preview_frame, columns=('Original', 'New'), show='headings')
        self.rename_treeview.heading('Original', text='Nome Original')
        self.rename_treeview.heading('New', text='Novo Nome')
        self.rename_treeview.column('Original', width=300)
        self.rename_treeview.column('New', width=300)
        self.rename_treeview.grid(row=0, column=0, sticky='nsew')
        scroll = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=self.rename_treeview.yview)
        scroll.grid(row=0, column=1, sticky='ns')
        self.rename_treeview.configure(yscrollcommand=scroll.set)
        self.rename_treeview.bind('<Double-1>', self._edit_treeview_cell)

    def _update_rename_options(self, event=None) -> None:
        """Atualiza a interface com base na opção de renomeação selecionada."""
        selected_option = self.rename_combobox.current() + 1
        if selected_option == 9:  # Custom Prefix/Suffix
            self.custom_options_frame.grid()
            self.rename_options[9] = CustomPrefixOrSuffix(
                self.custom_prefix.get(), self.custom_suffix.get(),
                self.apply_prefix.get(), self.apply_suffix.get()
            )
        else:
            self.custom_options_frame.grid_remove()

    def _edit_treeview_cell(self, event) -> None:
        """Permite editar o novo nome no Treeview ao clicar duas vezes, usando um diálogo."""
        item = self.rename_treeview.selection()
        if not item:
            return
        item = item[0]
        column = self.rename_treeview.identify_column(event.x)
        if column != '#2':  # Apenas a coluna 'New Name' é editável
            return
        
        # Obter o valor atual
        old_name, current_new_name = self.rename_treeview.item(item, 'values')
        
        # Criar um diálogo para edição
        dialog = tk.Toplevel(self.root)
        dialog.title("Editar Nome")
        dialog.geometry("300x150")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Novo Nome:", font=('Arial', 11)).pack(pady=5)
        entry = ttk.Entry(dialog)
        entry.insert(0, current_new_name)
        entry.pack(pady=5, padx=10, fill='x')
        entry.focus_set()
        
        def save_edit():
            new_name = entry.get()
            if new_name:  # Validar que o nome não está vazio
                self.rename_treeview.item(item, values=(old_name, new_name))
                # Atualizar self.edited_changes
                for i, (orig, _) in enumerate(self.edited_changes):
                    if orig == old_name:
                        self.edited_changes[i] = (orig, new_name)
                        break
            dialog.destroy()
        
        ttk.Button(dialog, text="Salvar", command=save_edit).pack(pady=5)
        dialog.bind('<Return>', lambda e: save_edit())

    def browse_directory(self) -> None:
        """Abre diálogo para selecionar diretório de trabalho."""
        directory = filedialog.askdirectory(title="Selecione uma pasta")
        if not directory:
            messagebox.showwarning("Aviso", "Nenhum diretório selecionado.")
            return
        if not os.path.isdir(directory):
            messagebox.showerror("Erro", "O diretório selecionado é inválido.")
            return
        if not os.access(directory, os.W_OK):
            messagebox.showerror("Erro", "Sem permissão para modificar o diretório selecionado.")
            return
        self.current_dir.set(directory)
        os.chdir(directory)
        self.dir_status.config(text=f"Pasta selecionada: {directory}")
        messagebox.showinfo("Informação", "Diretório alterado")
        logging.info(f"Diretório alterado para: {directory}")

    def _get_files(self) -> List[str]:
        """Retorna lista de arquivos no diretório atual com base nas extensões e sufixo selecionados."""
        extensions = []
        if self.ext_jpg.get():
            extensions.append('.jpg')
        if self.ext_png.get():
            extensions.append('.png')
        if self.ext_jpeg.get():
            extensions.append('.jpeg')
        if self.ext_webp.get():
            extensions.append('.webp')
        
        if not extensions:
            return []
        
        suffix = self.rename_suffix_var.get() if hasattr(self, 'rename_suffix_var') else "_"
        return [f for f in os.listdir() if os.path.isfile(f) and os.path.splitext(f)[1].lower() in extensions and suffix in os.path.splitext(f)[0]]

    def _check_name_conflicts(self, changes: List[Tuple[str, str]]) -> List[str]:
        """Verifica conflitos de nomes."""
        existing_files = set(self._get_files())
        return [new_name for _, new_name in changes if new_name in existing_files and new_name not in {old for old, _ in changes}]

    def _safe_rename(self, changes: List[Tuple[str, str]]) -> None:
        """Executa renomeação segura usando diretório temporário."""
        temp_dir = os.path.join(self.current_dir.get(), "__temp_rename__")
        os.makedirs(temp_dir, exist_ok=True)
        try:
            for old, new in changes:
                src_path = os.path.join(self.current_dir.get(), old)
                temp_path = os.path.join(temp_dir, new)
                shutil.copy2(src_path, temp_path)
            for old, _ in changes:
                os.remove(os.path.join(self.current_dir.get(), old))
            for _, new in changes:
                shutil.move(os.path.join(temp_dir, new), os.path.join(self.current_dir.get(), new))
        except Exception as e:
            logging.error(f"Erro durante renomeação segura: {str(e)}", exc_info=True)
            raise
        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)

    def _validate_before_operation(self) -> bool:
        """Valida se há extensões selecionadas e arquivos disponíveis."""
        if not any([self.ext_jpg.get(), self.ext_png.get(), self.ext_jpeg.get(), self.ext_webp.get()]):
            messagebox.showwarning("Aviso", "Selecione pelo menos uma extensão de arquivo.")
            return False
        try:
            os.chdir(self.current_dir.get())
            files = self._get_files()
            if not files:
                messagebox.showinfo("Informação", "Nenhum arquivo encontrado no diretório com as extensões e sufixo selecionados.")
                return False
            if self.rename_combobox.current() + 1 == 9:  # Validação para prefixo/sufixo personalizado
                if not (self.apply_prefix.get() and self.custom_prefix.get()) and not (self.apply_suffix.get() and self.custom_suffix.get()):
                    messagebox.showwarning("Aviso", "Digite um prefixo ou sufixo e selecione pelo menos uma opção para aplicar.")
                    return False
                invalid_chars = r'[<>:"/\\|?*]'
                if (self.custom_prefix.get() and re.search(invalid_chars, self.custom_prefix.get())) or \
                   (self.custom_suffix.get() and re.search(invalid_chars, self.custom_suffix.get())):
                    messagebox.showwarning("Aviso", "O prefixo ou sufixo contém caracteres inválidos.")
                    return False
            return True
        except PermissionError:
            messagebox.showerror("Erro", "Sem permissão para acessar o diretório.")
            logging.error("Erro de permissão ao validar operação.")
            return False
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao validar operação: {str(e)}")
            logging.error(f"Erro ao validar operação: {str(e)}")
            return False

    def preview_remove(self) -> None:
        """Pré-visualiza arquivos a serem removidos."""
        self.remove_listbox.delete(0, tk.END)
        if not self._validate_before_operation():
            return
        try:
            files_to_remove = self._get_files_to_remove(self.suffix_var.get(), self.number_var.get())
            if not files_to_remove:
                self.remove_listbox.insert(tk.END, "Nenhum arquivo encontrado para remover.")
                return
            for file in sorted(files_to_remove):
                self.remove_listbox.insert(tk.END, file)
            self.remove_listbox.insert(tk.END, f"Total: {len(files_to_remove)} arquivo(s)")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao pré-visualizar a remoção: {str(e)}")
            logging.error(f"Erro ao pré-visualizar a remoção: {str(e)}")

    def _get_files_to_remove(self, suffix: str, start_number: int) -> List[str]:
        """Busca arquivos a remover com base no sufixo e número inicial."""
        files_to_remove = set()
        extensions = [ext for ext, var in [('.jpg', self.ext_jpg), ('.png', self.ext_png),
                                          ('.jpeg', self.ext_jpeg), ('.webp', self.ext_webp)] if var.get()]
        if not extensions:
            return []
        
        for num in range(start_number, 21):
            pattern = re.compile(rf".*{re.escape(suffix)}{num}\..*$")
            for f in self._get_files():
                if pattern.match(f):
                    files_to_remove.add(f)
        return list(files_to_remove)

    def execute_remove(self) -> None:
        """Executa a remoção de arquivos."""
        if not self._validate_before_operation():
            return
        try:
            files_to_remove = self._get_files_to_remove(self.suffix_var.get(), self.number_var.get())
            if not files_to_remove:
                messagebox.showinfo("Informação", "Nenhum arquivo encontrado para remover.")
                return

            if not messagebox.askyesno("Confirmar remoção", f"Tem certeza que deseja remover {len(files_to_remove)} arquivo(s)?"):
                messagebox.showinfo("Informação", "Operação cancelada pelo usuário.")
                return

            trash_dir = os.path.join(self.current_dir.get(), "__trash__")
            os.makedirs(trash_dir, exist_ok=True)
            log_file = f"log_remocao_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            
            with open(log_file, 'w', encoding='utf-8') as log:
                log.write(f"Log de remoção - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                log.write(f"Diretório: {self.current_dir.get()}\n")
                log.write(f"Sufixo: {self.suffix_var.get()}, Número inicial: {self.number_var.get()}\n\n")
                for file in files_to_remove:
                    try:
                        src_path = os.path.join(self.current_dir.get(), file)
                        dest_path = os.path.join(trash_dir, file)
                        shutil.move(src_path, dest_path)
                        log.write(f"Removido: {file}\n")
                        logging.info(f"Arquivo movido para lixeira: {file}")
                    except Exception as e:
                        log.write(f"ERRO ao remover {file}: {str(e)}\n")
                        logging.error(f"Erro ao remover {file}: {str(e)}")

            messagebox.showinfo("Sucesso", f"{len(files_to_remove)} arquivo(s) movido(s) para lixeira.\nLog gerado: {log_file}")
            self.preview_remove()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao remover arquivos: {str(e)}")
            logging.error(f"Erro geral ao remover arquivos: {str(e)}", exc_info=True)

    def undo_remove(self) -> None:
        """Restaura arquivos da pasta __trash__."""
        try:
            os.chdir(self.current_dir.get())
            trash_dir = os.path.join(self.current_dir.get(), "__trash__")
            if not os.path.exists(trash_dir):
                messagebox.showinfo("Informação", "Nenhum arquivo encontrado na lixeira.")
                return

            files_to_restore = [f for f in os.listdir(trash_dir) if os.path.isfile(os.path.join(trash_dir, f))]
            if not files_to_restore:
                messagebox.showinfo("Informação", "Nenhum arquivo encontrado na lixeira.")
                return

            if not messagebox.askyesno("Confirmar restauração", f"Tem certeza que deseja restaurar {len(files_to_restore)} arquivo(s)?"):
                messagebox.showinfo("Informação", "Operação cancelada pelo usuário.")
                return

            log_file = f"log_restauracao_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(log_file, 'w', encoding='utf-8') as log:
                log.write(f"Log de restauração - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                log.write(f"Diretório: {self.current_dir.get()}\n\n")
                for file in files_to_restore:
                    try:
                        shutil.move(os.path.join(trash_dir, file), os.path.join(self.current_dir.get(), file))
                        log.write(f"Restaurado: {file}\n")
                        logging.info(f"Arquivo restaurado: {file}")
                    except Exception as e:
                        log.write(f"ERRO ao restaurar {file}: {str(e)}\n")
                        logging.error(f"Erro ao restaurar {file}: {str(e)}")

            messagebox.showinfo("Sucesso", f"{len(files_to_restore)} arquivo(s) restaurado(s).\nLog gerado: {log_file}")
            self.preview_remove()
        except PermissionError:
            messagebox.showerror("Erro", "Sem permissão para modificar o diretório.")
            logging.error("Erro de permissão ao restaurar arquivos.")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao restaurar arquivos: {str(e)}")
            logging.error(f"Erro ao restaurar arquivos: {str(e)}")

    def preview_rename(self) -> None:
        """Pré-visualiza renomeações."""
        self.rename_treeview.delete(*self.rename_treeview.get_children())
        self.edited_changes = []
        if not self._validate_before_operation():
            return
        try:
            option = self.rename_options[self.rename_combobox.current() + 1]
            if self.rename_combobox.current() + 1 == 9:  # Atualizar CustomPrefixOrSuffix
                option = CustomPrefixOrSuffix(
                    self.custom_prefix.get(), self.custom_suffix.get(),
                    self.apply_prefix.get(), self.apply_suffix.get()
                )
                self.rename_options[9] = option
            changes = option.preview(self._get_files(), self.rename_suffix_var.get())
            if not changes:
                messagebox.showinfo("Informação", "Nenhum arquivo encontrado para renomear com o sufixo selecionado.")
                return

            conflicts = self._check_name_conflicts(changes)
            if conflicts:
                messagebox.showerror("Erro", f"Conflitos de nomes detectados: {', '.join(conflicts)}")
                return

            self.edited_changes = changes[:]
            for i, (old, new) in enumerate(changes):
                self.rename_treeview.insert('', 'end', iid=str(i), values=(old, new))
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao pré-visualizar a renomeação: {str(e)}")
            logging.error(f"Erro ao pré-visualizar a renomeação: {str(e)}")

    def execute_rename(self) -> None:
        """Executa renomeações."""
        if not self._validate_before_operation():
            return
        try:
            # Atualizar opção personalizada se selecionada
            if self.rename_combobox.current() + 1 == 9:
                self.rename_options[9] = CustomPrefixOrSuffix(
                    self.custom_prefix.get(), self.custom_suffix.get(),
                    self.apply_prefix.get(), self.apply_suffix.get()
                )
                # Regenerar mudanças para refletir prefixo/sufixo atual
                changes = self.rename_options[9].preview(self._get_files(), self.rename_suffix_var.get())
                self.edited_changes = changes[:]
            else:
                changes = self.edited_changes[:]

            if not changes:
                messagebox.showinfo("Informação", "Nenhum arquivo encontrado para renomear com o sufixo selecionado.")
                return

            conflicts = self._check_name_conflicts(changes)
            if conflicts:
                messagebox.showerror("Erro", f"Conflitos de nomes detectados: {', '.join(conflicts)}")
                return

            if not messagebox.askyesno("Confirmar renomeação", f"Tem certeza que deseja renomear {len(changes)} arquivo(s)?"):
                messagebox.showinfo("Informação", "Operação cancelada pelo usuário.")
                return

            self._safe_rename(changes)
            log_file = f"log_renomeacao_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(log_file, 'w', encoding='utf-8') as log:
                log.write(f"Log de renomeação - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                log.write(f"Diretório: {self.current_dir.get()}\n")
                log.write(f"Opção: {self.rename_combobox.get()}\n")
                log.write(f"Sufixo: {self.rename_suffix_var.get()}\n\n")
                for old, new in changes:
                    log.write(f"{old} → {new}\n")
                    logging.info(f"Arquivo renomeado: {old} → {new}")

            messagebox.showinfo("Sucesso", f"{len(changes)} arquivo(s) renomeado(s) com sucesso.\nLog gerado: {log_file}")
            self.preview_rename()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao renomear arquivos: {str(e)}")
            logging.error(f"Erro ao renomear arquivos: {str(e)}", exc_info=True)

    def show_about(self) -> None:
        """Exibe janela com informações sobre o programa."""
        about_window = tk.Toplevel(self.root)
        about_window.title("Sobre o Gerenciador de Arquivos")
        about_window.geometry("500x300")
        about_window.resizable(False, False)
        
        ttk.Label(about_window, text="Gerenciador de Arquivos - Flywheel", font=('Arial', 14, 'bold')).pack(pady=0)
        ttk.Label(about_window, text="Versão: 1.0").pack(pady=0)
        ttk.Label(about_window, text="Desenvolvido por: Leonardo Mera - Intern Content Team").pack(pady=7)
        ttk.Label(about_window, text="Dúvidas ou ideias de novas funcionalidades, entrar em contato por e-mail:").pack(pady=0)
        ttk.Label(about_window, text="leonardo.mera@flywheeldigital.com").pack()
        
        ttk.Button(about_window, text="Fechar", command=about_window.destroy).pack(pady=10)

if __name__ == "__main__":
    root = tk.Tk()
    app = FlywheelManager(root)
    root.mainloop()