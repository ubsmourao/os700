import streamlit as st
from supabase_client import supabase
from datetime import datetime, timedelta

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
        st.success("Chamado aberto com sucesso!")
        return protocolo
    except Exception as e:
        st.error(f"Erro ao adicionar chamado: {e}")
        return None

def finalizar_chamado(id_chamado, solucao):
    try:
        hora_fechamento = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        # Atualiza o chamado com a solução e a hora de fechamento
        supabase.table("chamados").update({
            "solucao": solucao,
            "hora_fechamento": hora_fechamento
        }).eq("id", id_chamado).execute()
        
        # Recebe as peças utilizadas (entrada de texto, separadas por vírgula)
        pecas_input = st.text_area("Informe as peças utilizadas (separadas por vírgula)")
        pecas_usadas = [p.strip() for p in pecas_input.split(",") if p.strip()] if pecas_input else []
        
        if pecas_usadas:
            for peca in pecas_usadas:
                supabase.table("pecas_usadas").insert({
                    "chamado_id": id_chamado,
                    "peca_nome": peca,
                    "data_uso": hora_fechamento
                }).execute()
        
        # Atualiza o histórico de manutenção, se houver patrimônio associado
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
                "data_manutencao": hora_fechamento
            }).execute()
        
        st.success(f"Chamado {id_chamado} finalizado.")
    except Exception as e:
        st.error(f"Erro ao finalizar chamado: {e}")

def list_chamados():
    try:
        resp = supabase.table("chamados").select("*").execute()
        return resp.data
    except Exception as e:
        st.error(f"Erro ao listar chamados: {e}")
        return []

def list_chamados_em_aberto():
    try:
        resp = supabase.table("chamados").select("*").is_("hora_fechamento", None).execute()
        return resp.data
    except Exception as e:
        st.error(f"Erro ao listar chamados abertos: {e}")
        return []

def get_chamados_por_patrimonio(patrimonio):
    try:
        resp = supabase.table("chamados").select("*").eq("patrimonio", patrimonio).execute()
        return resp.data if resp.data else []
    except Exception as e:
        st.error(f"Erro ao buscar chamados para o patrimonio {patrimonio}: {e}")
        return []

def calculate_working_hours(start, end):
    """
    Calcula o tempo util entre 'start' e 'end', considerando um expediente:
      - Manha: 08:00 a 12:00
      - Tarde: 13:00 a 17:00
    Ignora finais de semana.
    
    Retorna um objeto timedelta com o tempo util.
    """
    if start >= end:
        return timedelta(0)
    
    total_seconds = 0
    current = start

    while current < end:
        # Se for sabado ou domingo, pula para o proximo dia
        if current.weekday() >= 5:
            current = datetime.combine(current.date() + timedelta(days=1), datetime.min.time())
            continue

        # Define os intervalos de trabalho para o dia atual
        morning_start = current.replace(hour=8, minute=0, second=0, microsecond=0)
        morning_end = current.replace(hour=12, minute=0, second=0, microsecond=0)
        afternoon_start = current.replace(hour=13, minute=0, second=0, microsecond=0)
        afternoon_end = current.replace(hour=17, minute=0, second=0, microsecond=0)

        # Calcula tempo util na manha, se houver sobreposicao
        if end > morning_start:
            interval_start = max(current, morning_start)
            interval_end = min(end, morning_end)
            if interval_end > interval_start:
                total_seconds += (interval_end - interval_start).total_seconds()
        
        # Calcula tempo util na tarde, se houver sobreposicao
        if end > afternoon_start:
            interval_start = max(current, afternoon_start)
            interval_end = min(end, afternoon_end)
            if interval_end > interval_start:
                total_seconds += (interval_end - interval_start).total_seconds()
        
        # Avanca para o proximo dia
        current = datetime.combine(current.date() + timedelta(days=1), datetime.min.time())
    
    return timedelta(seconds=total_seconds)

if __name__ == "__main__":
    st.write("Modulo de Chamados Técnicos")
