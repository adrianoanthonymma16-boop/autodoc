"""
GeracaoService - gera documentos finais
"""
import os
from modelo_odt import gerar_odt_preenchido
from modelo_docx import gerar_docx_preenchido, docx_suportado

class GeracaoService:
    def __init__(self, state):
        self.state = state

    def gerar_um(self, model_path: str, model_tipo: str, dados: dict, output_path: str):
        if model_tipo == 'odt':
            gerar_odt_preenchido(model_path, dados, output_path)
        elif model_tipo == 'docx':
            if not docx_suportado():
                raise Exception("DOCX não suportado")
            gerar_docx_preenchido(model_path, dados, output_path)
        else:
            raise Exception(f"Tipo desconhecido: {model_tipo}")
