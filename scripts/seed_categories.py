"""
Script para popular o banco de dados com categorias padrão brasileiras
Execute uma única vez para cada usuário novo
"""

# Categorias padrão organizadas por tipo
DEFAULT_CATEGORIES = {
    # DESPESAS
    "Alimentação": {
        "subcategories": ["Supermercado", "Restaurante", "Delivery", "Padaria", "Lanchonete"],
        "kind": "expense"
    },
    "Transporte": {
        "subcategories": ["Combustível", "Uber/99", "Ônibus/Metrô", "Estacionamento", "Manutenção", "IPVA", "Seguro"],
        "kind": "expense"
    },
    "Moradia": {
        "subcategories": ["Aluguel", "Condomínio", "IPTU", "Água", "Luz", "Gás", "Internet", "Telefone", "Manutenção"],
        "kind": "expense"
    },
    "Saúde": {
        "subcategories": ["Plano de Saúde", "Farmácia", "Médico", "Dentista", "Exames", "Academia"],
        "kind": "expense"
    },
    "Educação": {
        "subcategories": ["Mensalidade", "Material Escolar", "Livros", "Cursos", "Idiomas"],
        "kind": "expense"
    },
    "Lazer": {
        "subcategories": ["Cinema", "Shows", "Viagens", "Streaming", "Jogos", "Hobbies"],
        "kind": "expense"
    },
    "Vestuário": {
        "subcategories": ["Roupas", "Calçados", "Acessórios"],
        "kind": "expense"
    },
    "Beleza": {
        "subcategories": ["Salão", "Produtos", "Cosméticos"],
        "kind": "expense"
    },
    "Pets": {
        "subcategories": ["Ração", "Veterinário", "Produtos"],
        "kind": "expense"
    },
    "Impostos": {
        "subcategories": ["IR", "IPTU", "IPVA", "Outros"],
        "kind": "expense"
    },
    "Seguros": {
        "subcategories": ["Saúde", "Vida", "Veículo", "Residencial"],
        "kind": "expense"
    },
    "Investimentos": {
        "subcategories": ["Ações", "Fundos", "Tesouro", "Previdência", "Criptomoedas"],
        "kind": "expense"
    },
    "Outros Gastos": {
        "subcategories": ["Presentes", "Doações", "Despesas Diversas"],
        "kind": "expense"
    },
    
    # RECEITAS
    "Salário": {
        "subcategories": ["Salário Mensal", "13º Salário", "Férias", "Bônus", "Comissões"],
        "kind": "income"
    },
    "Freelance": {
        "subcategories": ["Projetos", "Consultorias", "Serviços"],
        "kind": "income"
    },
    "Investimentos (Receita)": {
        "subcategories": ["Dividendos", "Juros", "Rendimentos", "Lucros"],
        "kind": "income"
    },
    "Outros Rendimentos": {
        "subcategories": ["Aluguel", "Vendas", "Prêmios", "Reembolsos"],
        "kind": "income"
    },
    
    # TRANSFERÊNCIAS (ambos)
    "Transferências": {
        "subcategories": ["Entre Contas", "Pix Recebido", "Pix Enviado", "TED", "DOC"],
        "kind": "both"
    },
}

def seed_categories(user_id: str, supa_client):
    """
    Popula o banco com categorias padrão para um usuário
    
    Args:
        user_id: ID do usuário
        supa_client: Cliente do Supabase
    """
    import sys
    
    print(f"🌱 Populando categorias para usuário {user_id}...")
    
    total_cats = 0
    total_subs = 0
    
    for category, data in DEFAULT_CATEGORIES.items():
        subcategories = data["subcategories"]
        kind = data["kind"]
        
        try:
            # Verifica se a categoria já existe
            check = supa_client.table("categories")\
                .select("*")\
                .eq("user_id", user_id)\
                .eq("name", category)\
                .is_("parent_name", "null")\
                .execute()
            
            # Se não existe, cria
            if not check.data:
                supa_client.table("categories").insert({
                    "user_id": user_id,
                    "name": category,
                    "parent_name": None,
                    "kind": kind
                }).execute()
                
                total_cats += 1
                print(f"  ✅ Categoria criada: {category}")
            else:
                print(f"  ⏭️  Categoria já existe: {category}")
            
            # Cria subcategorias
            for sub in subcategories:
                sub_check = supa_client.table("categories")\
                    .select("*")\
                    .eq("user_id", user_id)\
                    .eq("name", sub)\
                    .eq("parent_name", category)\
                    .execute()
                
                if not sub_check.data:
                    supa_client.table("categories").insert({
                        "user_id": user_id,
                        "name": sub,
                        "parent_name": category,
                        "kind": kind
                    }).execute()
                    
                    total_subs += 1
                    print(f"    └─ ✅ Subcategoria criada: {sub}")
        
        except Exception as e:
            print(f"  ❌ Erro ao criar {category}: {e}", file=sys.stderr)
            continue
    
    print(f"\n✨ Concluído! {total_cats} categorias e {total_subs} subcategorias criadas.")
    return total_cats, total_subs


if __name__ == "__main__":
    import os
    import sys
    
    # Adiciona o diretório raiz ao path
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from app.db import supa
    from app.auth import current_user_id
    
    # Tenta pegar o user_id do argumento ou usa o usuário atual
    if len(sys.argv) > 1:
        user_id = sys.argv[1]
    else:
        try:
            user_id = current_user_id()
        except:
            print("❌ Erro: Informe o user_id como argumento")
            print("Uso: python scripts/seed_categories.py <user_id>")
            sys.exit(1)
    
    # Executa o seed
    seed_categories(user_id, supa())
