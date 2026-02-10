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
            direct_dependencies: Lista de fórmulas/variables que usa directamente
        """
        self.formula_registry[formula_name] = {
            'code': formula_code,
            'direct_deps': set(direct_dependencies or []),
            'timestamp': None
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
    gate = CascadeDepthGate()
    
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
