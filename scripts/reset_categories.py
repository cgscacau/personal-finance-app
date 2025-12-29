"""
Script para LIMPAR e RECRIAR todas as categorias do zero
ATENÇÃO: Este script DELETA todas as categorias existentes!
"""

# Categorias padrão CORRIGIDAS e organizadas
DEFAULT_CATEGORIES = {
    # ========== DESPESAS ==========
    "Alimentação": ["Supermercado", "Restaurante", "Delivery", "Padaria", "Lanchonete"],
    "Transporte": ["Combustível", "Uber/99", "Ônibus", "Estacionamento", "Manutenção", "IPVA"],
    "Moradia": ["Aluguel", "Condomínio", "IPTU", "Água", "Luz", "Gás", "Internet"],
    "Saúde": ["Plano de Saúde", "Farmácia", "Médico", "Dentista", "Exames", "Academia"],
    "Educação": ["Mensalidade", "Material", "Livros", "Cursos"],
    "Lazer": ["Cinema", "Shows", "Viagens", "Streaming", "Jogos"],
    "Vestuário": ["Roupas", "Calçados", "Acessórios"],
    "Beleza": ["Salão", "Produtos", "Cosméticos"],
    "Pets": ["Ração", "Veterinário", "Produtos"],
    
    # ========== RECEITAS ==========
    "Salário": ["Salário Mensal", "13º", "Férias", "Bônus"],
    "Freelance": ["Projetos", "Consultorias", "Serviços"],
    "Rendimentos": ["Dividendos", "Juros", "Aluguel"],
    
    # ========== OUTROS ==========
    "Transferências": ["Entre Contas", "Pix", "TED", "DOC"],
    "Doações": ["Caridade", "Presentes", "Ajuda Família"],
}

def reset_and_seed_categories(user_id: str, supa_client):
    """
    DELETA todas as categorias e recria do zero
    """
    print(f"🗑️  LIMPANDO todas as categorias do usuário {user_id}...")
    
    try:
        # DELETAR TODAS as categorias do usuário
        result = supa_client.table("categories")\
            .delete()\
            .eq("user_id", user_id)\
            .execute()
        
        print(f"✅ Categorias antigas deletadas!")
    except Exception as e:
        print(f"⚠️  Aviso ao deletar: {e}")
    
    print(f"\n🌱 Criando nova base de categorias...")
    
    total_cats = 0
    total_subs = 0
    
    for category, subcategories in DEFAULT_CATEGORIES.items():
        try:
            # Cria categoria principal
            cat_result = supa_client.table("categories").insert({
                "user_id": user_id,
                "name": category,
                "parent_name": None,
                "kind": "both"  # Todas como "both" para flexibilidade
            }).execute()
            
            total_cats += 1
            print(f"  ✅ [{total_cats}] {category}")
            
            # Cria subcategorias
            for sub in subcategories:
                supa_client.table("categories").insert({
                    "user_id": user_id,
                    "name": sub,
                    "parent_name": category,
                    "kind": "both"
                }).execute()
                
                total_subs += 1
                print(f"    └─ {sub}")
        
        except Exception as e:
            print(f"  ❌ Erro ao criar {category}: {e}")
            continue
    
    print(f"\n✨ CONCLUÍDO!")
    print(f"   📁 {total_cats} categorias criadas")
    print(f"   📂 {total_subs} subcategorias criadas")
    print(f"   🎯 Total: {total_cats + total_subs} registros")
    
    return total_cats, total_subs


if __name__ == "__main__":
    import os
    import sys
    
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from app.db import supa
    
    if len(sys.argv) < 2:
        print("❌ Uso: python scripts/reset_categories.py <user_id>")
        sys.exit(1)
    
    user_id = sys.argv[1]
    
    confirm = input(f"⚠️  ATENÇÃO: Isso vai DELETAR todas as categorias do usuário {user_id}. Continuar? (sim/não): ")
    
    if confirm.lower() in ['sim', 's', 'yes', 'y']:
        reset_and_seed_categories(user_id, supa())
    else:
        print("❌ Operação cancelada.")
