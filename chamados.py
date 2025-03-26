# chamados.py
import streamlit as st
from supabase_client import supabase
from datetime import datetime, timedelta
import pytz

# Define o fuso de Fortaleza
FORTALEZA_TZ = pytz.timezone("America/Fortaleza")

def gerar_protocolo_sequencial():
    try:
        resp = supabase.table("chamados").select("protocolo", count="exact").execute()
        protocolos = [item["protocolo"] for item in resp.data if item.get("protocolo") is not None]
        return max(protocolos, default=0) + 1
    except Exception as e:
        st.error(f"Erro ao gerar protocolo: {e}")
        return None

def get_chamado_by_protocolo(protocolo):
    try:
        resp = supabase.table("chamados").select("*").eq("protocolo", protocolo).execute()
        return resp.data[0] if resp.data else None
    except Exception as e:
        st.error(f"Erro ao buscar chamado: {e}")
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
        st.error(f"Erro ao buscar patrimonio: {e}")
        return None

def add_chamado(username, ubs, setor, tipo_defeito, problema, machine=None, patrimonio=None):
    """
    Cria um chamado no Supabase, definindo a hora de abertura
    com o fuso horário de Fortaleza (UTC−3).
    """
    try:
        protocolo = gerar_protocolo_sequencial()
        if protocolo is None:
            return None

        # Gera horário local de Fortaleza
        hora_local = datetime.now(FORTALEZA_TZ).strftime('%d/%m/%Y %H:%M:%S')

        data = {
            "username": username,
            "ubs": ubs,
            "setor": setor,
            "tipo_defeito": tipo_defeito,
            "problema": problema,
            "hora_abertura": hora_local,  # <-- horário local
            "protocolo": protocolo,
            "machine": machine,
            "patrimonio": patrimonio
        }
        supabase.table("chamados").insert(data).execute()
        st.success("Chamado aberto com sucesso!")
        return protocolo
    except Exception as e:
        st.error(f"Erro ao adicionar chamado: {e}")
        return None

def finalizar_chamado(id_chamado, solucao, pecas_usadas=None):
    """
    Finaliza um chamado, definindo a hora de fechamento
    com o fuso horário de Fortaleza (UTC−3).
    Também insere as peças usadas e registra histórico de manutenção.
    """
    try:
        hora_fechamento_local = datetime.now(FORTALEZA_TZ).strftime('%d/%m/%Y %H:%M:%S')

        supabase.table("chamados").update({
            "solucao": solucao,
            "hora_fechamento": hora_fechamento_local
        }).eq("id", id_chamado).execute()
        
        # Se nenhuma entrada de peças for fornecida, pergunta ao usuário
        if pecas_usadas is None:
            pecas_input = st.text_area("Informe as peças utilizadas (separadas por vírgula)")
            pecas_usadas = [p.strip() for p in pecas_input.split(",") if p.strip()] if pecas_input else []
        
        # Se houver peças usadas, insere na tabela pecas_usadas e dá baixa no estoque
        if pecas_usadas:
            for peca in pecas_usadas:
                supabase.table("pecas_usadas").insert({
                    "chamado_id": id_chamado,
                    "peca_nome": peca,
                    "data_uso": hora_fechamento_local
                }).execute()
                from estoque import dar_baixa_estoque
                dar_baixa_estoque(peca, quantidade_usada=1)
        
        resp = supabase.table("chamados").select("patrimonio").eq("id", id_chamado).execute()
        if resp.data and len(resp.data) > 0:
            patrimonio = resp.data[0].get("patrimonio")
        else:
            patrimonio = None

        if patrimonio:
            descricao = f"Manutenção: {solucao}. Peças utilizadas: {', '.join(pecas_usadas) if pecas_usadas else 'Nenhuma'}."
            supabase.table("historico_manutencao").insert({
                "numero_patrimonio": patrimonio,
                "descricao": descricao,
                "data_manutencao": hora_fechamento_local
            }).execute()
        
        st.success(f"Chamado {id_chamado} finalizado.")
    except Exception as e:
        st.error(f"Erro ao finalizar chamado: {e}")

def list_chamados():
    """
    Retorna todos os chamados da tabela 'chamados'.
    """
    try:
        resp = supabase.table("chamados").select("*").execute()
        return resp.data
    except Exception as e:
        st.error(f"Erro ao listar chamados: {e}")
        return []

def list_chamados_em_aberto():
    """
    Retorna todos os chamados onde hora_fechamento IS NULL.
    """
    try:
        resp = supabase.table("chamados").select("*").is_("hora_fechamento", None).execute()
        return resp.data
    except Exception as e:
        st.error(f"Erro ao listar chamados abertos: {e}")
        return []

def get_chamados_por_patrimonio(patrimonio):
    """
    Retorna todos os chamados vinculados a um patrimônio específico.
    """
    try:
        resp = supabase.table("chamados").select("*").eq("patrimonio", patrimonio).execute()
        return resp.data if resp.data else []
    except Exception as e:
        st.error(f"Erro ao buscar chamados para o patrimonio {patrimonio}: {e}")
        return []

def calculate_working_hours(start, end):
    """
    Calcula o tempo útil entre 'start' e 'end', considerando o expediente:
      - Manhã: 08:00 a 12:00
      - Tarde: 13:00 a 17:00
    Ignora sábados e domingos.
    Retorna um objeto timedelta com o tempo útil.
    """
    if start >= end:
        return timedelta(0)
    
    total_seconds = 0
    current = start

    while current < end:
        # Se for sábado (5) ou domingo (6), pula para o próximo dia
        if current.weekday() >= 5:
            current = datetime.combine(current.date() + timedelta(days=1), datetime.min.time())
            continue

        morning_start = current.replace(hour=8, minute=0, second=0, microsecond=0)
        morning_end = current.replace(hour=12, minute=0, second=0, microsecond=0)
        afternoon_start = current.replace(hour=13, minute=0, second=0, microsecond=0)
        afternoon_end = current.replace(hour=17, minute=0, second=0, microsecond=0)

        if end > morning_start:
            interval_start = max(current, morning_start)
            interval_end = min(end, morning_end)
            if interval_end > interval_start:
                total_seconds += (interval_end - interval_start).total_seconds()
        
        if end > afternoon_start:
            interval_start = max(current, afternoon_start)
            interval_end = min(end, afternoon_end)
            if interval_end > interval_start:
                total_seconds += (interval_end - interval_start).total_seconds()
        
        current = datetime.combine(current.date() + timedelta(days=1), datetime.min.time())
    
    return timedelta(seconds=total_seconds)

###########################
# Função para reabrir chamado
###########################
def reabrir_chamado(id_chamado, remover_historico=False):
    """
    Reabre um chamado que foi finalizado, removendo hora_fechamento e solucao.
    Se remover_historico=True, também apaga o registro de manutencao
    referente à data de fechamento anterior (se quiser).
    """
    try:
        # 1) Busca dados do chamado
        resp = supabase.table("chamados").select("*").eq("id", id_chamado).execute()
        if not resp.data:
            st.error("Chamado não encontrado.")
            return
        chamado = resp.data[0]

        # Verifica se realmente está fechado
        if not chamado.get("hora_fechamento"):
            st.info("Chamado já está em aberto.")
            return

        old_hora_fechamento = chamado["hora_fechamento"]
        patrimonio = chamado.get("patrimonio")

        # 2) Atualiza hora_fechamento e solucao para None
        supabase.table("chamados").update({
            "hora_fechamento": None,
            "solucao": None
        }).eq("id", id_chamado).execute()

        # 3) Se remover_historico=True, remove o registro no historico_manutencao
        # que tenha data_manutencao == old_hora_fechamento (caso tenha sido criado ao finalizar)
        if remover_historico and patrimonio and old_hora_fechamento:
            supabase.table("historico_manutencao").delete() \
                .eq("numero_patrimonio", patrimonio) \
                .eq("data_manutencao", old_hora_fechamento) \
                .execute()

        st.success(f"Chamado {id_chamado} reaberto com sucesso!")
    except Exception as e:
        st.error(f"Erro ao reabrir chamado: {e}")

if __name__ == "__main__":
    st.write("Módulo de Chamados - Supabase - Hora Local de Fortaleza")