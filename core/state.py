from typing import TypedDict, Optional

class PipelineState(TypedDict):
    """Sistemin (Ajanların) ortak hafızasını tutan veri yapısı."""
    requirements: str            # Kullanıcının talep ettiği teknoloji ve vizyon
    structure: Optional[str]     # Mimari JSON iskeleti
    documentation: Optional[str] # Proje hakkında yazılan README/Şema metni
    error: Optional[str]         # Eğer JSON şemaya uymazsa yazılan hata
    json_retries: int            # Hata düzeltme döngüsü sayacı
