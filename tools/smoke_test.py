def smoke_test():
    print("Iniciando smoke test...")

    try:
        from core.ui.main_ui import MainUI
    except Exception as e:
        print("[ERROR] Error importando módulos:", e)
        return

    try:
        ui = MainUI()
        ui.iniciar()
        estado = ui.mostrar_estado()
        print("\n=== METEOSER - SMOKE TEST ===\n")
        print("[Sensores]")
        for nombre, valor in estado.get("sensores", {}).items():
            print(f" - {nombre}: {valor}")
        print("\n[Índices]")
        for nombre, valor in estado.get("indices", {}).items():
            print(f" - {nombre}: {valor}")
        print("\n[Recomendación]")
        rec = estado.get("recomendacion", {})
        print(f" -> {rec.get('estado')}")
        print(f"   Motivos: {rec.get('motivos')}")

        print("\nOK Smoke test completado sin errores.")
    except Exception as e:
        print("ERROR Error ejecutando el sistema:", e)


if __name__ == "__main__":
    smoke_test()
