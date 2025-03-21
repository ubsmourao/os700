# chamados.py
from supabase_client import supabase
from datetime import datetime

def gerar_protocolo_sequencial():
    try:
        resp = supabase.table("chamados").select("protocolo", count="exact").execute()
        protocolos = [item["protocolo"] for item in resp.data if item.get("protocolo") is not None]
        return max(protocolos, default=0) + 1
    except Exception as e:
        print(f"Erro ao gerar protocolo: {e}")
        return None

def get_chamado_by_protocolo(protocolo):
    try:
        resp = supabase.table("chamados").select("*").eq("protocolo", protocolo).execute()
        return resp.data[0] if resp.data else None
    except Exception as e:
        print(f"Erro ao buscar chamado: {e}")
        return None

def buscar_no_inventario_por_patrimonio(patrimonio):
    try:
        resp = supabase.table("inventario").select("*").eq("numero_patrimonio", patrimonio).execute()
        if resp.data:
            machine = resp.data[0]
            return {
                "tipo": machine.get("tipo"),
                "marca": machine.get("marca"),
                "modelo": machine.get("modelo"),
                "patrimonio": machine.get("numero_patrimonio"),
                "localizacao": machine.get("localizacao"),
                "setor": machine.get("setor")
            }
        return None
    except Exception as e:
        print(f"Erro ao buscar patrimônio: {e}")
        return None

def add_chamado(username, ubs, setor, tipo_defeito, problema, machine=None, patrimonio=None):
    try:
        protocolo = gerar_protocolo_sequencial()
        if protocolo is None:
            return None
        hora_abertura = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        data = {
            "username": username,
            "ubs": ubs,
            "setor": setor,
            "tipo_defeito": tipo_defeito,
            "problema": problema,
            "hora_abertura": hora_abertura,
            "protocolo": protocolo,
            "machine": machine,
            "patrimonio": patrimonio
        }
        supabase.table("chamados").insert(data).execute()
        return protocolo
    except Exception as e:
        print(f"Erro ao adicionar chamado: {e}")
        return None

def finalizar_chamado(id_chamado, solucao, pecas_usadas=None):
    try:
        hora_fechamento = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        # Atualiza o chamado com a solução e fechamento
        supabase.table("chamados").update({
            "solucao": solucao,
            "hora_fechamento": hora_fechamento
        }).eq("id", id_chamado).execute()

        # Insere peças usadas, se houver
        if pecas_usadas:
            for peca in pecas_usadas:
                supabase.table("pecas_usadas").insert({
                    "chamado_id": id_chamado,
                    "peca_nome": peca,
                    "data_uso": hora_fechamento
                }).execute()
        # Insere histórico de manutenção
        chamado = supabase.table("chamados").select("patrimonio").eq("id", id_chamado).execute().data[0]
        patrimonio = chamado.get("patrimonio")
        if patrimonio:
            descricao = f"Manutenção: {solucao}. Peças: {', '.join(pecas_usadas) if pecas_usadas else 'Nenhuma'}."
            supabase.table("historico_manutencao").insert({
                "numero_patrimonio": patrimonio,
                "descricao": descricao,
                "data_manutencao": hora_fechamento
            }).execute()
        print(f"Chamado {id_chamado} finalizado.")
    except Exception as e:
        print(f"Erro ao finalizar chamado: {e}")

def list_chamados():
    try:
        resp = supabase.table("chamados").select("*").execute()
        return resp.data
    except Exception as e:
        print(f"Erro ao listar chamados: {e}")
        return []

def list_chamados_em_aberto():
    try:
        resp = supabase.table("chamados").select("*").is_("hora_fechamento", None).execute()
        return resp.data
    except Exception as e:
        print(f"Erro ao listar chamados abertos: {e}")
        return []
