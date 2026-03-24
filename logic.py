import os
from typing import List, Tuple
from abc import ABC, abstractmethod

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