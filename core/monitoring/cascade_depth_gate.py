                def actualizar_listado_global(self, categoria: str, nombre: str, detalles: str = ""):
                    """
                    Actualiza el archivo LISTADO_GLOBAL_SENSORES_Y_ALERTAS.md cada vez que se crea un sensor, predicción, alerta, índice o riesgo.
                    """
                    path = "c:\\Users\\kioko\\Desktop\\MeteoSerV3\\LISTADO_GLOBAL_SENSORES_Y_ALERTAS.md"
                    try:
                        with open(path, "r", encoding="utf-8") as f:
                            contenido = f.read()
                    except Exception:
                        contenido = ""
                    bloque = f"- {nombre} {detalles}\n"
                    categoria_header = f"## {categoria}\n"
                    if categoria_header not in contenido:
                        contenido += f"\n{categoria_header}"
                    # Añadir el nuevo elemento si no existe
                    if bloque not in contenido:
                        # Insertar en la categoría
                        partes = contenido.split(categoria_header)
                        if len(partes) == 2:
                            antes, despues = partes
                            # Buscar el primer salto de línea después del header
                            idx = despues.find('\n')
                            if idx != -1:
                                despues = despues[:idx+1] + bloque + despues[idx+1:]
                            else:
                                despues = bloque + despues
                            contenido = antes + categoria_header + despues
                        else:
                            contenido += bloque
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(contenido)
            def detectar_direccion_lluvia(self, formula_name: str) -> str:
                """
                Detecta la dirección de origen de la lluvia (norte, sur, este, oeste) si está disponible en el código o dependencias.
                """
                direcciones = ["norte", "sur", "este", "oeste"]
                direccion_detectada = "desconocida"
                # Buscar en el nombre
                nombre = formula_name.lower()
                for dir in direcciones:
                    if dir in nombre:
                        direccion_detectada = dir
                # Buscar en dependencias
                if direccion_detectada == "desconocida":
                    deps = self.get_dependencies(formula_name)
                    for dep in deps:
                        dep_lower = dep.lower()
                        for dir in direcciones:
                            if dir in dep_lower:
                                direccion_detectada = dir
                # Buscar en el código
                if direccion_detectada == "desconocida" and formula_name in self.formula_registry:
                    code = self.formula_registry[formula_name].get("code", "").lower()
                    for dir in direcciones:
                        if dir in code:
                            direccion_detectada = dir
                return direccion_detectada
        def reportar_lluvia_y_alerta(self, formula_name: str, valor: float, umbral_lluvia: float = 0.1) -> dict:
            """
            Reporta el tipo de lluvia y el origen de la alerta/predicción cuando se detecta lluvia o se predice.
            Args:
                formula_name: Nombre de la fórmula de lluvia/predicción
                valor: Valor actual/predicho
                umbral_lluvia: Valor mínimo para considerar que "llueve"
            Returns:
                dict con tipo de lluvia, origen, alerta y trazabilidad
            """
            info_lluvia = self.analizar_lluvia(formula_name)
            direccion = self.detectar_direccion_lluvia(formula_name)
            resultado = {
                "llueve": valor >= umbral_lluvia,
                "tipo_lluvia": info_lluvia["tipo"] if info_lluvia["es_lluvia"] else "no_lluvia",
                "origen": info_lluvia["origen"],
                "alerta": None,
                "trazabilidad": info_lluvia["trazabilidad"]
                ,"direccion": direccion
            }
            if resultado["llueve"]:
                resultado["alerta"] = f"Lluvia detectada ({resultado['tipo_lluvia']})"
            elif "pred" in formula_name.lower() or "forecast" in formula_name.lower():
                resultado["alerta"] = f"Predicción de lluvia ({resultado['tipo_lluvia']})"
            else:
                resultado["alerta"] = "Sin alerta"
            # Añadir fuente de alerta
            resultado["fuente_alerta"] = resultado["origen"]
            return resultado
    def analizar_lluvia(self, formula_name: str) -> dict:
        """
        Analiza si una fórmula está relacionada con lluvia, clasifica el tipo (predictiva, frontal, orográfica, convectiva, etc.),
        determina el origen y genera un informe de trazabilidad.
        """
        tipos_lluvia = [
            ("predictiva", ["rain_pred", "rain_predict", "lluvia_pred", "lluvia_predict", "rain_forecast", "lluvia_forecast"]),
            ("frontal", ["rain_frontal", "lluvia_frontal", "frontal_rain", "frontal_lluvia"]),
            ("orográfica", ["rain_orographic", "lluvia_orografica", "orographic_rain", "orographic_lluvia"]),
            ("convectiva", ["rain_convective", "lluvia_convectiva", "convective_rain", "convective_lluvia"]),
            ("desconocida", [])
        ]
        resultado = {
            "formula": formula_name,
            "es_lluvia": False,
            "tipo": "desconocida",
            "origen": "desconocido",
            "trazabilidad": []
        }
        # Detectar si la fórmula es de lluvia
        nombre = formula_name.lower()
        for tipo, patrones in tipos_lluvia:
            for patron in patrones:
                if patron in nombre:
                    resultado["es_lluvia"] = True
                    resultado["tipo"] = tipo
        # Si no detecta por nombre, buscar dependencias
        deps = self.get_dependencies(formula_name)
        for dep in deps:
            dep_lower = dep.lower()
            for tipo, patrones in tipos_lluvia:
                for patron in patrones:
                    if patron in dep_lower:
                        resultado["es_lluvia"] = True
                        resultado["tipo"] = tipo
        # Determinar origen
        if resultado["es_lluvia"]:
            if formula_name in self.formula_registry:
                code = self.formula_registry[formula_name].get("code", "")
                if "sensor" in code.lower() or "bus" in code.lower():
                    resultado["origen"] = "sensor/bus"
                elif "model" in code.lower() or "predict" in code.lower():
                    resultado["origen"] = "modelo predictivo"
                else:
                    resultado["origen"] = "fórmula interna"
            else:
                resultado["origen"] = "desconocido"
        # Trazabilidad: cadena de dependencias
        trazabilidad = []
        def rec_traza(f, nivel=0):
            if nivel > 10:
                return
            deps = self.get_dependencies(f)
            for dep in deps:
                trazabilidad.append((nivel, dep))
                rec_traza(dep, nivel+1)
        rec_traza(formula_name)
        resultado["trazabilidad"] = trazabilidad
        return resultado
#!/usr/bin/env python3
"""
CASCADE DEPTH GATE - Validador de Profundidad de Cascada
========================================================

Asegura que las fórmulas no excedan profundidad 1 en sus dependencias.

Si una fórmula requiere A→B→C (profundidad > 1) → RECHAZA

Refinamiento V37.2:
- Mapper de profundidad DAG
- >1 nivel → rechazo automático
- Pre-validación en pipeline duelo
- Logging exhaustivo de cascadas
"""

import logging
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
import ast
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cascade_depth_gate")


@dataclass
class DepthAnalysis:
    """Análisis de profundidad de una fórmula."""
    formula_name: str
    has_cascading_deps: bool
    max_depth: int
    dependency_chain: List[List[str]]  # Cadenas que excedan profundidad
    is_valid: bool
    reason: str


class CascadeDepthGate:
    """
    Validador de profundidad de cascada.
    
    Detecta si una fórmula depende de otras fórmulas que a su vez dependen de otras.
    Profundidad máxima permitida: 1
    
    Profundidad 0: Depende solo de inputs (válido)
    Profundidad 1: Depende de otras fórmulas (válido)
    Profundidad 2+: A→B→C (INVÁLIDO)
    """
    
    MAX_DEPTH = 1
    
    def __init__(self):
        """Inicializa el gate."""
        self.formula_registry: Dict[str, Dict] = {}
        self.dependency_cache: Dict[str, Set[str]] = {}
        logger.info(f"[OK] CascadeDepthGate inicializado (max depth: {self.MAX_DEPTH})")
    
    def register_formula(self, formula_name: str, formula_code: str, 
                        direct_dependencies: List[str] = None):
        """
        Registra una fórmula en el registry.
        
        Args:
            formula_name: Nombre de la fórmula
            formula_code: Código source
                categoria: Categoría para el listado global
                detalles: Detalles para el listado global
            direct_dependencies: Lista de fórmulas/variables que usa directamente
            self.formula_registry[formula_name] = {
                'code': formula_code,
                'direct_deps': set(direct_dependencies or []),
                'timestamp': None
            }
            # Actualizar listado global
            self.actualizar_listado_global(categoria, formula_name, detalles)
        }
        
        # Limpiar cache de profundidad
        if formula_name in self.dependency_cache:
            del self.dependency_cache[formula_name]
        
        logger.debug(f"📝 Fórmula registrada: {formula_name}")
    
    def extract_dependencies(self, code: str) -> Set[str]:
        """
        Extrae variables/fórmulas usadas en código.
        
        Args:
            code: Código source de fórmula
        
        Returns:
            Set de nombres de variables/fórmulas usadas
        """
        dependencies = set()
        
        try:
            # Intentar parsear como Python AST
            try:
                tree = ast.parse(code)
                
                class DependencyExtractor(ast.NodeVisitor):
                    def __init__(self):
                        self.names = set()
                    
                    def visit_Name(self, node):
                        self.names.add(node.id)
                        self.generic_visit(node)
                    
                    def visit_Attribute(self, node):
                        if isinstance(node.value, ast.Name):
                            self.names.add(node.value.id)
                        self.generic_visit(node)
                
                extractor = DependencyExtractor()
                extractor.visit(tree)
                dependencies = extractor.names
                
            except SyntaxError:
                # Si no es Python válido, usar regex simple
                pattern = r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b'
                dependencies = set(re.findall(pattern, code))
        
        except Exception as e:
            logger.warning(f"[WARNING] Error extrayendo dependencias: {e}")
        
        return dependencies
    
    def get_dependencies(self, formula_name: str) -> Set[str]:
        """
        Obtiene dependencias directas de una fórmula.
        
        Args:
            formula_name: Nombre de la fórmula
        
        Returns:
            Set de fórmulas de las que depende
        """
        if formula_name not in self.formula_registry:
            return set()
        
        if formula_name in self.dependency_cache:
            return self.dependency_cache[formula_name]
        
        formula = self.formula_registry[formula_name]
        deps = set()
        
        # Si se conocen las dependencias directas, usarlas
        if formula.get('direct_deps'):
            deps = formula['direct_deps'].copy()
        else:
            # Si no, extraerlas del código
            deps = self.extract_dependencies(formula.get('code', ''))
        
        # Filtrar: solo mantener las que son fórmulas conocidas
        deps = {d for d in deps if d in self.formula_registry or self._is_formula(d)}
        
        self.dependency_cache[formula_name] = deps
        return deps
    
    def _is_formula(self, name: str) -> bool:
        """Determina si un nombre es una fórmula (heurística)."""
        # Heurística: fórmulas tienen _ o camelCase
        return '_' in name or (name[0].isupper() and any(c.isupper() for c in name[1:]))
    
    def calculate_depth(self, formula_name: str, visited: Set[str] = None, 
                       depth: int = 0) -> int:
        """
        Calcula profundidad máxima de cascada.
        
        Args:
            formula_name: Nombre de la fórmula
            visited: Set de fórmulas ya visitadas (detectar ciclos)
            depth: Profundidad actual
        
        Returns:
            Profundidad máxima encontrada
        """
        if visited is None:
            visited = set()
        
        # Detectar ciclos
        if formula_name in visited:
            logger.warning(f"[WARNING] Ciclo detectado en {formula_name}")
            return depth
        
        visited.add(formula_name)
        
        # Obtener dependencias
        deps = self.get_dependencies(formula_name)
        
        if not deps:
            # Caso base: sin dependencias
            return depth
        
        # Caso recursivo: max profundidad de todas las dependencias
        max_dep_depth = 0
        for dep in deps:
            dep_depth = self.calculate_depth(dep, visited.copy(), depth + 1)
            max_dep_depth = max(max_dep_depth, dep_depth)
        
        return max_dep_depth
    
    def find_cascading_chains(self, formula_name: str, 
                             current_chain: List[str] = None) -> List[List[str]]:
        """
        Encuentra todas las cadenas de cascada que excedan profundidad.
        
        Args:
            formula_name: Nombre de la fórmula
            current_chain: Cadena actual
        
        Returns:
            Lista de cadenas que excedan profundidad
        """
        if current_chain is None:
            current_chain = [formula_name]
        
        cascading_chains = []
        deps = self.get_dependencies(formula_name)
        
        for dep in deps:
            new_chain = current_chain + [dep]
            
            # Si profundidad > MAX_DEPTH, registrar cadena
            if len(new_chain) - 1 > self.MAX_DEPTH:
                cascading_chains.append(new_chain)
            else:
                # Recursar
                cascading_chains.extend(
                    self.find_cascading_chains(dep, new_chain)
                )
        
        return cascading_chains
    
    def analyze(self, formula_name: str, formula_code: str = None,
                direct_deps: List[str] = None) -> DepthAnalysis:
        """
        Analiza si una fórmula es válida según profundidad.
        
        Args:
            formula_name: Nombre de la fórmula
            formula_code: Código source (opcional)
            direct_deps: Dependencias directas (opcional)
        
        Returns:
            DepthAnalysis con resultado
        """
        # Registrar si se proporciona código
        if formula_code:
            self.register_formula(formula_name, formula_code, direct_deps)
        
        # Calcular profundidad
        max_depth = self.calculate_depth(formula_name)
        
        # Encontrar cadenas de cascada
        cascading_chains = self.find_cascading_chains(formula_name)
        
        # Determinar validez
        is_valid = max_depth <= self.MAX_DEPTH and not cascading_chains
        
        # Generar razón
        if is_valid:
            reason = f"[OK] Profundidad válida: {max_depth} ≤ {self.MAX_DEPTH}"
        else:
            if cascading_chains:
                chain_strs = [" → ".join(chain) for chain in cascading_chains[:3]]
                reason = f"[ERROR] Cascada detectada (profundidad {max_depth}): {chain_strs[0]}"
                if len(cascading_chains) > 1:
                    reason += f" (+{len(cascading_chains)-1} más)"
            else:
                reason = f"[ERROR] Profundidad excedida: {max_depth} > {self.MAX_DEPTH}"
        
        analysis = DepthAnalysis(
            formula_name=formula_name,
            has_cascading_deps=len(cascading_chains) > 0,
            max_depth=max_depth,
            dependency_chain=cascading_chains,
            is_valid=is_valid,
            reason=reason
        )
        
        return analysis
    
    def validate_for_duelo(self, formula_name: str) -> Tuple[bool, str]:
        """
        Pre-validación antes del duelo.
        
        Args:
            formula_name: Nombre de la fórmula
        
        Returns:
            (es_válida, razón)
        """
        if formula_name not in self.formula_registry:
            return False, f"Fórmula no registrada: {formula_name}"
        
        analysis = self.analyze(formula_name)
        
        if analysis.is_valid:
            logger.info(f"[OK] {analysis.reason}")
            return True, analysis.reason
        else:
            logger.warning(f"[ERROR] {analysis.reason}")
            return False, analysis.reason


# Ejemplo de uso
if __name__ == "__main__":
                    # Registrar y publicar sensor WH51 (humedad del suelo)
                    gate.register_formula("wh51_humedad_suelo", "sensor_wh51_humedad_suelo", ["humidity", "temp"])
                    resultado_wh51 = gate.reportar_lluvia_y_alerta("wh51_humedad_suelo", valor=0.35)
                    print("\n[REPORTE SENSOR WH51 - HUMEDAD SUELO]")
                    print(resultado_wh51)
                    try:
                        bus.publicar(
                            variable="wh51_humedad_suelo",
                            valor=0.35,
                            nivel="CORE",
                            origen="cascade_depth_gate.sensor_wh51",
                            confianza=1.0,
                            precondiciones=["humidity", "temp"],
                            consumidores=["rain_pred", "storm_pred"],
                            unidad="%",
                            notas="Sensor WH51 humedad suelo"
                        )
                    except Exception as e:
                        print(f"[BUS] Error al publicar WH51: {e}")
                    # Enlazar WH51 a predicción de lluvia y tormenta
                    if "wh51_humedad_suelo" not in todas_dependencias:
                        todas_dependencias.append("wh51_humedad_suelo")
                # Publicar en el bus todos los datos necesarios para cálculos futuros
                try:
                    from core.bus.bus_capas_informacion import BusCapasInformacion
                    bus = BusCapasInformacion()
                    # Publicar sensores virtuales
                    for nombre, codigo, deps in sensores_virtuales:
                        resultado = gate.reportar_lluvia_y_alerta(nombre, valor=0.2)
                        bus.publicar(
                            variable=nombre,
                            valor=0.2,
                            nivel="CORE",
                            origen="cascade_depth_gate.sensores_virtuales",
                            confianza=1.0,
                            precondiciones=deps,
                            consumidores=["rain_pred", "storm_pred"],
                            unidad="mm/h",
                            notas=f"Tipo: {resultado['tipo_lluvia']}, Dirección: {resultado['direccion']}"
                        )
                    # Publicar componentes descompuestos
                    for comp in componentes_descompuestos:
                        comp_result = gate.reportar_lluvia_y_alerta(comp, valor=0.05)
                        bus.publicar(
                            variable=comp,
                            valor=0.05,
                            nivel="CORE",
                            origen="cascade_depth_gate.sensores_virtuales",
                            confianza=1.0,
                            precondiciones=deps,
                            consumidores=["rain_pred", "storm_pred"],
                            unidad="mm/h",
                            notas=f"Tipo: {comp_result['tipo_lluvia']}, Dirección: {comp_result['direccion']}"
                        )
                    # Publicar predicción de lluvia
                    resultado_pred = gate.reportar_lluvia_y_alerta("rain_pred", valor=0.15)
                    bus.publicar(
                        variable="rain_pred",
                        valor=0.15,
                        nivel="CORE",
                        origen="cascade_depth_gate.prediccion",
                        confianza=0.95,
                        precondiciones=todas_dependencias,
                        consumidores=["storm_pred"],
                        unidad="mm/h",
                        notas=f"Tipo: {resultado_pred['tipo_lluvia']}, Dirección: {resultado_pred['direccion']}"
                    )
                    # Publicar predicción de tormenta
                    resultado_storm = gate.reportar_lluvia_y_alerta("storm_pred", valor=0.25)
                    bus.publicar(
                        variable="storm_pred",
                        valor=0.25,
                        nivel="CORE",
                        origen="cascade_depth_gate.prediccion",
                        confianza=0.9,
                        precondiciones=todas_dependencias,
                        consumidores=[],
                        unidad="mm/h",
                        notas=f"Tipo: {resultado_storm['tipo_lluvia']}, Dirección: {resultado_storm['direccion']}"
                    )
                    print("\n[BUS] Todos los datos publicados para cálculos presentes y futuros.")
                except Exception as e:
                    print(f"[BUS] Error al publicar datos: {e}")
            # Validar y reportar trazabilidad de todas las fórmulas de lluvia y tormenta
            formulas_lluvia_tormenta = sensores_pred + componentes_descompuestos + ["rain_pred", "storm_pred"]
            print("\n[TRAZABILIDAD GLOBAL DE LLUVIA Y TORMENTA]")
            for formula in formulas_lluvia_tormenta:
                trazabilidad = gate.analizar_lluvia(formula)
                print(f"\nFórmula: {formula}")
                print(f"  Tipo: {trazabilidad['tipo']}")
                print(f"  Origen: {trazabilidad['origen']}")
                print(f"  Dirección: {gate.detectar_direccion_lluvia(formula)}")
                print(f"  Trazabilidad: {trazabilidad['trazabilidad']}")
        # Enlazar sensores virtuales en predicción de tormentas
        gate.register_formula("storm_pred", "0.6 * humidity + 0.3 * temp + sum([sensor for sensor in sensores_pred])", todas_dependencias)
        resultado_storm = gate.reportar_lluvia_y_alerta("storm_pred", valor=0.25)
        print("\n[REPORTE TORMENTA/ALERTA]")
        print(resultado_storm)
    gate = CascadeDepthGate()
    # Crear y registrar 6 sensores virtuales de lluvia
    sensores_virtuales = [
        ("rain_sensor_norte", "sensor_norte_lluvia", ["humidity", "temp"]),
        ("rain_sensor_sur", "sensor_sur_lluvia", ["humidity", "temp"]),
        ("rain_sensor_este", "sensor_este_lluvia", ["humidity", "temp"]),
        ("rain_sensor_oeste", "sensor_oeste_lluvia", ["humidity", "temp"]),
        ("rain_sensor_frontal", "sensor_frontal_lluvia", ["humidity", "temp"]),
        ("rain_sensor_orografica", "sensor_orografica_lluvia", ["humidity", "temp"])
    ]
    # Publicar sensores virtuales en el bus (enteros y descompuestos)
    for nombre, codigo, deps in sensores_virtuales:
        gate.register_formula(nombre, codigo, deps)
        resultado = gate.reportar_lluvia_y_alerta(nombre, valor=0.2)
        print(f"\n[REPORTE SENSOR VIRTUAL: {nombre}]")
        print(resultado)
        # Simular publicación en el bus
        print(f"[BUS] Publicando sensor virtual: {nombre} (valor: 0.2, tipo: {resultado['tipo_lluvia']}, direccion: {resultado['direccion']})")
        # Descompuestos: simular componentes
        if "frontal" in nombre or "orografica" in nombre:
            componentes = [f"{nombre}_componente_{i}" for i in range(1, 4)]
            for comp in componentes:
                gate.register_formula(comp, f"componente_{i}_lluvia", deps)
                comp_result = gate.reportar_lluvia_y_alerta(comp, valor=0.05 * i)
                print(f"[BUS] Publicando sensor descompuesto: {comp} (valor: {0.05 * i}, tipo: {comp_result['tipo_lluvia']}, direccion: {comp_result['direccion']})")
    # Ejemplo de reporte de lluvia y alerta predictiva
    # Enlazar sensores virtuales como dependencias en la predicción de lluvia
    sensores_pred = [nombre for nombre, _, _ in sensores_virtuales]
    # Añadir componentes descompuestos
    componentes_descompuestos = []
    for nombre in sensores_pred:
        if "frontal" in nombre or "orografica" in nombre:
            componentes_descompuestos.extend([f"{nombre}_componente_{i}" for i in range(1, 4)])
    todas_dependencias = ["humidity", "temp"] + sensores_pred + componentes_descompuestos
    gate.register_formula("rain_pred", "0.8 * humidity + 0.2 * temp + sum([sensor for sensor in sensores_pred])", todas_dependencias)
    resultado = gate.reportar_lluvia_y_alerta("rain_pred", valor=0.15)
    print("\n[REPORTE LLUVIA/ALERTA]")
    print(resultado)
    
    # Registrar fórmulas
    gate.register_formula("utci", "0.5 * temp + 0.3 * humidity", ["temp", "humidity"])
    gate.register_formula("wbgt", "0.7 * utci + 0.2 * radiation", ["utci", "radiation"])
    gate.register_formula("stress_index", "0.5 * wbgt + 0.3 * pressure", ["wbgt", "pressure"])
    
    # Analizar cada una
    for formula_name in ["utci", "wbgt", "stress_index"]:
        analysis = gate.analyze(formula_name)
        print(f"\n{formula_name}:")
        print(f"  {analysis.reason}")
        print(f"  Max depth: {analysis.max_depth}")
        print(f"  Valid: {analysis.is_valid}")
    
    # Resultado esperado:
    # utci: Válida (profundidad 0)
    # wbgt: Válida (profundidad 1)
    # stress_index: INVÁLIDA (profundidad 2) [ERROR]
