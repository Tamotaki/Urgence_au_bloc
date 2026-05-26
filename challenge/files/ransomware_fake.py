#!/usr/bin/env python3
"""
S0lar1s Decryptor v2.4
Outil de recuperation de donnees - Hopital Saint-Louis

Algorithme : XOR symetrique repete

Usage : python3 ransomware_fake.py <fichier.xor> <cle>
"""
import sys
import os
import time
import hashlib


BANNER = r"""
   _____  ___  _      ___  ____  ___  ____
  / ___/ / _ \| |    / _ \|  _ \|_ _|/ ___|
  \___ \| | | | |   | | | | |_) || | \___ \
   ___) | |_| | |___| |_| |  _ < | |  ___) |
  |____/ \___/|_____|\___/|_| \_\___||____/

           D E C R Y P T O R   v 2 . 4
"""


# Petit effet typewriter
def slow_print(text, delay=0.012):
    for c in text:
        sys.stdout.write(c)
        sys.stdout.flush()
        time.sleep(delay)
    print()


# Barre de progression factice
def progress_bar(label, duration=1.5, width=40):
    sys.stdout.write(f"  {label} ")
    sys.stdout.flush()
    steps = 20
    for i in range(steps + 1):
        pct = int(i * 100 / steps)
        bar = "#" * int(i * width / steps) + "." * (width - int(i * width / steps))
        sys.stdout.write(f"\r  {label} [{bar}] {pct:3d}%")
        sys.stdout.flush()
        time.sleep(duration / steps)
    print()


# Dechiffre data avec une cle XOR repetee
def xor_decrypt(data: bytes, key: str) -> bytes:
    key_bytes = key.encode()
    if not key_bytes:
        raise ValueError("Cle vide")
    return bytes([b ^ key_bytes[i % len(key_bytes)] for i, b in enumerate(data)])


# Heuristique pour detecter si le resultat ressemble a du texte lisible
def looks_like_text(data: bytes, threshold: float = 0.85) -> bool:
    if not data:
        return False
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return False
    printable = sum(1 for c in text if c.isprintable() or c in "\n\r\t ")
    return printable / len(text) >= threshold


# Validation des arguments
def validate_args():
    if len(sys.argv) != 3:
        print(__doc__)
        print("[!] Erreur : nombre d'arguments invalide.")
        print("    Usage : python3 ransomware_fake.py <fichier.xor> <cle>")
        print("    Exemple : python3 ransomware_fake.py /tmp/backup.xor S3cr3tK3y!")
        sys.exit(1)

    filepath, key = sys.argv[1], sys.argv[2]

    if not os.path.exists(filepath):
        print(f"[!] Fichier introuvable : {filepath}")
        sys.exit(2)

    if not os.path.isfile(filepath):
        print(f"[!] Ce n'est pas un fichier regulier : {filepath}")
        sys.exit(2)

    size = os.path.getsize(filepath)
    if size == 0:
        print(f"[!] Fichier vide : {filepath}")
        sys.exit(2)

    if not key:
        print("[!] Cle vide - fournis une cle non nulle.")
        sys.exit(3)

    return filepath, key, size


def main():
    print(BANNER)
    slow_print("  [*] Initialisation du moteur de dechiffrement...")
    time.sleep(0.3)

    filepath, key, size = validate_args()

    print()
    print(f"  Fichier cible  : {filepath}")
    print(f"  Taille         : {size} octets")
    print(f"  Longueur cle   : {len(key)} caracteres")
    print(f"  Empreinte cle  : sha256:{hashlib.sha256(key.encode()).hexdigest()[:16]}...")
    print()

    # Lecture du fichier chiffre
    progress_bar("Lecture du fichier chiffre", duration=0.8)
    with open(filepath, "rb") as f:
        encrypted = f.read()

    # Dechiffrement
    progress_bar("Application du XOR inverse", duration=1.2)
    try:
        decrypted = xor_decrypt(encrypted, key)
    except ValueError as e:
        print(f"[!] Erreur cryptographique : {e}")
        sys.exit(4)

    # Verification heuristique
    progress_bar("Verification d'integrite ", duration=0.6)

    if looks_like_text(decrypted):
        try:
            result = decrypted.decode("utf-8")
        except UnicodeDecodeError:
            result = decrypted.decode("utf-8", errors="replace")

        print()
        print("  [+] DECHIFFREMENT REUSSI - DONNEES RESTAUREES")
        print()
        print("=" * 64)
        print(result)
        print("=" * 64)

        # Sauvegarde optionnelle du resultat
        out_path = filepath + ".decrypted"
        try:
            with open(out_path, "w") as f:
                f.write(result)
            print(f"\n  [+] Copie sauvegardee dans : {out_path}")
        except OSError as e:
            print(f"\n  [!] Impossible d'ecrire la copie ({e})")
        sys.exit(0)
    else:
        print()
        print("  [!] ECHEC - la cle semble incorrecte")
        print()
        print("  Le resultat ne ressemble pas a du texte lisible.")
        print("  Verifie la cle et reessaie.")
        print()
        print("  Indices :")
        print("   - La cle est sensible a la casse.")
        print("   - Les caracteres speciaux comptent (! ? @ etc.).")
        print("   - Tu as peut-etre inclus un espace en trop.")
        print()
        preview = decrypted[:32].hex()
        print(f"  Apercu hex (32 premiers octets) : {preview}")
        sys.exit(5)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[!] Interrompu par l'utilisateur.")
        sys.exit(130)