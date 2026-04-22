from langgraph.graph import StateGraph, END
from core.state import PipelineState
from core.config import Config

from generators.structure_generator import StructureGenerator
from generators.doc_generator import DocGenerator
from validators.json_validator import JsonValidator
from correctors.json_corrector import JsonCorrector

config = Config()
struct_gen = StructureGenerator(config)
doc_gen = DocGenerator(config)
json_val = JsonValidator()
json_corr = JsonCorrector(config)


def generate_structure_node(state: PipelineState) -> PipelineState:
    print(f"[*] Ajan (Mimar): İhtiyaçlar analiz ediliyor -> '{state['requirements']}'")
    struct_json = struct_gen.generate(state["requirements"])
    return {**state, "structure": struct_json, "json_retries": 0, "error": None}

def validate_structure_node(state: PipelineState) -> PipelineState:
    print("[*] Linter (Mimari Denetleyici): Klasör şeması inceleniyor...")
    is_valid, error = json_val.validate(state["structure"])
    if is_valid:
        print("[+] Linter: Plan hatasız, onaylandı.")
        return {**state, "error": None}
    else:
        print(f"[-] Linter: Tasarım hatası -> {error}")
        return {**state, "error": error}

def correct_structure_node(state: PipelineState) -> PipelineState:
    retries = state.get("json_retries", 0) + 1
    print(f"[*] Ajan (Mimar Düzeltici): Tasarım kural ihlali onarılıyor... (Deneme: {retries})")
    
    if retries > config.MAX_RETRIES:
        raise ValueError("Maksimum JSON mimari düzeltme denemesine ulaşıldı.")
        
    fixed_json = json_corr.fix(state["structure"], state["error"], state["requirements"])
    return {**state, "structure": fixed_json, "json_retries": retries, "error": None}

def generate_documentation_node(state: PipelineState) -> PipelineState:
    print("[*] Ajan (Belgelendirici): Cursor/Claude için Mimari Proje Dökümü yazılıyor...")
    documentation = doc_gen.generate(state["requirements"], state["structure"])
    print("[+] Belgelendirme tamamlandı.")
    return {**state, "documentation": documentation}

def architecture_router(state: PipelineState) -> str:
    if state.get("error") is None:
        return "generate_documentation"
    return "correct_structure"

def build_graph():
    builder = StateGraph(PipelineState)
    
    # 1. Düğümleri Ekle
    builder.add_node("generate_structure", generate_structure_node)
    builder.add_node("validate_structure", validate_structure_node)
    builder.add_node("correct_structure", correct_structure_node)
    builder.add_node("generate_documentation", generate_documentation_node)
    
    # 2. Bağlantıları Kur
    builder.set_entry_point("generate_structure")
    builder.add_edge("generate_structure", "validate_structure")
    
    builder.add_conditional_edges(
        "validate_structure",
        architecture_router,
        {
            "generate_documentation": "generate_documentation",
            "correct_structure": "correct_structure"
        }
    )
    
    builder.add_edge("correct_structure", "validate_structure")
    builder.add_edge("generate_documentation", END)
    
    return builder.compile()
