"""
Test face metrics.
Usage: venv\Scripts\python.exe test_metrics.py path\to\photo.jpg
"""
import sys
sys.stdout.reconfigure(encoding="utf-8")
from bot.services.face_metrics import compute_metrics

def main():
    if len(sys.argv) < 2:
        print("Использование: python test_metrics.py путь_к_фото.jpg")
        sys.exit(1)

    path = sys.argv[1]
    with open(path, "rb") as f:
        data = f.read()

    print(f"Анализирую: {path} ({len(data)//1024} KB)")
    print()

    m = compute_metrics(data)

    if not m.detected:
        print(f"Лицо не обнаружено: {m.error}")
        sys.exit(1)

    print(m.to_prompt_text())
    print()
    print(f"Лицевой указатель : {m.facial_index}")
    print(f"Носовой указатель : {m.nasal_index}")
    print(f"Орбитальный       : {m.orbital_index}")
    print(f"Межглазничный     : {m.interocular_ratio}")

if __name__ == "__main__":
    main()
