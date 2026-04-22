from core.graph import build_graph
from core.filesystem import FileSystemBuilder

def main():
    print("Welcome to the AI Solutions Architect (Micro-Agent Pipeline)")
    print("----------------------------------------------------------")
    print("Bana projenizin ne olduğunu, hangi dilleri/framework'leri (ör. React, Django, Go) kullanacağınızı")
    print("ve özel isteklerinizi detaylıca anlatın.\n")
    
    requirements = input("Proje Gereksinimleriniz: ")
    if not requirements.strip():
        print("Gereksinimler boş olamaz. Program sonlanıyor.")
        return

    # Grafımızı (Beynimizi) inşa ediyoruz
    graph = build_graph()
    
    initial_state = {
        "requirements": requirements,
        "structure": None,
        "documentation": None,
        "error": None,
        "json_retries": 0
    }
    
    print("\n--- [LangGraph Ajan Sistemi Başlatıldı] ---\n")
    
    try:
        final_state = graph.invoke(initial_state)
        
        print("\n\n=== JENERASYON BAŞARIYLA TAMAMLANDI ===")
        print("\n--- [PROJE KLASÖR ŞEMASI] ---")
        print(final_state.get("structure"))
        
        print("\n--- [MİMARİ README] ---")
        doc_snippet = final_state.get("documentation", "")[:300] + "...\n(Dökümanın devamı konsol için kısaltıldı)"
        print(doc_snippet)
        
        print("\n==================================")
        ans = input("Bu projenin şablonunu (klasörlerini ve dosyalarını) bilgisayarınızda oluşturayım mı? (e/h): ")
        
        if ans.lower() == 'e':
            print("\nDonanıma bağlanılıyor... Fiziksel ortam inşa ediliyor...")
            # Masaüstüne "ScaffoldedProjects" diye bir ana dizine çıkarıyoruz
            builder = FileSystemBuilder(base_path=r"c:\Users\musta\Desktop\ScaffoldedProjects")
            out_dir = builder.build(final_state["structure"], final_state["documentation"])
            
            print(f"\n[BAŞARILI] Projeniz kullanıma hazır! Konum: {out_dir}")
            print("Artık VSCode, Cursor veya Claude'u bu klasörün içinde açabilirsiniz!")
        else:
            print("\nFiziksel kurulum iptal edildi. Görüşmek üzere!")
            
    except Exception as e:
        print(f"\n[Kritik Hata] Organizasyon tamamen çöktü: {e}")

if __name__ == "__main__":
    main()
