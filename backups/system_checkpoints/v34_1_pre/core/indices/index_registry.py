class IndexRegistry:
    def __init__(self):
        self.indices = {}

    def set(self, nombre, valor, escala=None, meta=None):
        self.indices[nombre] = {
            "valor": valor,
            "escala": escala,
            "meta": meta or {}
        }

    def get(self, nombre):
        return self.indices.get(nombre)

    def all(self):
        return self.indices

    def normalize(self, nombre, valor, minimo, maximo):
        if maximo == minimo:
            esc = 0
        else:
            x = (valor - minimo) / (maximo - minimo)
            x = max(0, min(1, x))
            esc = x * 100
        self.set(nombre, valor, esc)
        return esc