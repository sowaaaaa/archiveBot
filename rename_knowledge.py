"""
Переименовывает папки и файлы в data/knowledge/ в короткие snake_case имена.
Запуск: python rename_knowledge.py
"""
import os
import shutil

KNOWLEDGE_DIR = "data/knowledge"

RENAMES = {
    # Папки
    "Basics of Facial Reconstruction Based on the Skull": "skull_reconstruction",
    "Beard Growth Scale":                                  "beard_scale",
    "Body Types":                                          "body_types",
    "Bunak's Eye Color Scale":                             "eye_color_scale",
    "Chin Protrusion on the Eikstedt Scale":               "chin_protrusion",
    "Comparison of a broadsheet and a tabloid":            "head_shape_comparison",
    "Degrees of horizontal facial contouring":             "horizontal_contouring_degrees",
    "Depth of eye placement":                              "eye_depth",
    "Differences between a simple epicanthal fold and an epicanthal (Mongolian) fold, as illustrated by a Caucasoid and a Mongoloid": "epicanthal_fold",
    "Examples of strong and weak horizontal facial contours": "facial_contours_examples",
    "Eye Position":                                        "eye_position",
    "eye sockets in profile":                              "eye_sockets_profile",
    "Horizontal profiling":                                "horizontal_profiling",
    "Morphological Characteristics of the Chin's Structure": "chin_morphology",
    "Shapes_Types_of_Eye_Sockets":                         "eye_socket_shapes",
    "The Fischer-Zaller Hair Scale":                       "hair_color_scale",
    "Thomas Fitzpatrick's Skin Type Scale":                "skin_type_scale",
    "Types of Facial Pointers":                            "facial_pointers",
    "Types of lips":                                       "lips_types",
    "Types of Main Index":                                 "main_facial_index",
    "Vertical profiling":                                  "vertical_profiling",

    # Файлы .txt
    "Types of nasal indicators.txt":                       "nasal_indicators.txt",
    "Types of orbital pointers.txt":                       "orbital_pointers.txt",
}

def rename_all():
    entries = os.listdir(KNOWLEDGE_DIR)
    renamed = 0
    skipped = 0

    for old_name in entries:
        if old_name not in RENAMES:
            continue

        new_name = RENAMES[old_name]
        old_path = os.path.join(KNOWLEDGE_DIR, old_name)
        new_path = os.path.join(KNOWLEDGE_DIR, new_name)

        if os.path.exists(new_path):
            print(f"  ⏭  {old_name!r} → уже существует {new_name!r}")
            skipped += 1
            continue

        os.rename(old_path, new_path)
        print(f"  ✅ {old_name!r}")
        print(f"     → {new_name!r}")
        renamed += 1

    # Всё что не в списке
    remaining = [e for e in os.listdir(KNOWLEDGE_DIR) if e not in RENAMES.values() and e != "ПРИМЕР.txt"]
    if remaining:
        print(f"\n⚠️  Не переименовано ({len(remaining)} шт.) — добавь в RENAMES если нужно:")
        for r in remaining:
            print(f"   {r!r}")

    print(f"\n✅ Переименовано: {renamed}, пропущено: {skipped}")

if __name__ == "__main__":
    print("📁 Переименование папок в data/knowledge/")
    print("=" * 50)
    rename_all()
