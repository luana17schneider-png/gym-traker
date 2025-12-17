import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime

# --- CONFIGURAÇÃO ---
# COLOQUE SEU LINK DO SHEETDB AQUI
API_URL = "https://sheetdb.io/api/v1/f2l7481uc45fn" 

st.set_page_config(page_title="Plano de treino", page_icon="💪", layout="wide")

# ==================================================
# MENU LATERAL
# ==================================================
st.sidebar.title("Navegação")
pagina = st.sidebar.radio("Ir para:", ["🏋️‍♂️ Registrar Treino", "📈 Minha Evolução"])

st.title("💪 Plano de treino")

# ==================================================
# PÁGINA 1: REGISTRAR TREINO
# ==================================================
if pagina == "🏋️‍♂️ Registrar Treino":
    st.header("Hora do Treino")
    
    try:
        response = requests.get(f"{API_URL}?sheet=Treinos")
        if response.status_code == 200:
            df_treinos = pd.DataFrame(response.json())
            
            # Verifica se tem as colunas essenciais
            if not df_treinos.empty and 'Treino_ID' in df_treinos.columns:
                lista_treinos = df_treinos['Treino_ID'].unique()
                treino_escolhido = st.selectbox("Qual ficha vai ser hoje?", lista_treinos)
                
                exercicios_do_dia = df_treinos[df_treinos['Treino_ID'] == treino_escolhido]
                
                st.divider()
                
                with st.form("form_treino"):
                    st.subheader(f"Ficha {treino_escolhido}")
                    resultados = []
                    
                    for index, row in exercicios_do_dia.iterrows():
                        col1, col2 = st.columns([1, 2])
                        with col1:
                            # TÍTULO E IMAGEM
                            st.markdown(f"**{row['Exercicio']}**")
                            st.caption(f"Repetições: {row['Serie']}")
                            
                            # --- CÓDIGO DA IMAGEM ---
                            # Verifica se existe a coluna e se tem link nela
                            if 'Imagem_URL' in row and str(row['Imagem_URL']).startswith('http'):
                                st.image(row['Imagem_URL'], use_container_width=True)
                            else:
                                st.warning("Sem imagem")
                        
                        with col2:
                            # INPUTS
                            carga = st.number_input(f"Carga (kg)", key=f"c_{index}", step=1.0)
                            feito = st.checkbox("Concluído", key=f"f_{index}")
                            
                            if feito:
                                resultados.append({
                                    "Data": datetime.now().strftime("%Y-%m-%d"),
                                    "Treino": treino_escolhido,
                                    "Exercicio": row['Exercicio'],
                                    "Carga": carga,
                                    "Concluido": "Sim"
                                })
                    
                    st.markdown("---")
                    btn_salvar = st.form_submit_button("Salvar Treino")
                    
                    if btn_salvar:
                        if len(resultados) > 0:
                            headers = {'Content-Type': 'application/json'}
                            r = requests.post(f"{API_URL}?sheet=Logs", data=json.dumps(resultados), headers=headers)
                            if r.status_code == 201:
                                st.balloons() # Efeito visual de festa!
                                st.success("Treino salvo! 💪")
                            else:
                                st.error("Erro ao salvar.")
                        else:
                            st.warning("Marque pelo menos um exercício.")
            else:
                st.warning("Aba 'Treinos' vazia. Verifique se preencheu a planilha.")
    except Exception as e:
        st.error(f"Erro de conexão: {e}")

# ==================================================
# PÁGINA 2: EVOLUÇÃO
# ==================================================
elif pagina == "📈 Minha Evolução":
    st.header("Seus Resultados")
    
    # --- 1. Formulário ---
    with st.expander("➕ Adicionar Nova Medição (Peso/Músculo)", expanded=False):
        with st.form("form_bio"):
            c1, c2 = st.columns(2)
            novo_peso = c1.number_input("Peso (kg)", format="%.2f")
            nova_massa = c2.number_input("Massa Muscular (kg)", format="%.2f")
            
            if st.form_submit_button("Salvar Medidas"):
                dados_bio = [{
                    "Data": datetime.now().strftime("%Y-%m-%d"),
                    "Peso": novo_peso,
                    "Massa_Muscular": nova_massa
                }]
                headers = {'Content-Type': 'application/json'}
                requests.post(f"{API_URL}?sheet=Bioimpedancia", data=json.dumps(dados_bio), headers=headers)
                st.success("Salvo! Recarregue a página.")

    st.divider()

    # --- 2. Gráfico ---
    st.subheader("Evolução Corporal")
    try:
        resp_bio = requests.get(f"{API_URL}?sheet=Bioimpedancia")
        if resp_bio.status_code == 200:
            df_bio = pd.DataFrame(resp_bio.json())
            
            if not df_bio.empty and 'Peso' in df_bio.columns:
                # --- TRATAMENTO DE DADOS (A Mágica) ---
                
                # 1. Converte DATA para formato de tempo
                df_bio['Data'] = pd.to_datetime(df_bio['Data'])
                
                # 2. Converte PESO e MASSA para números (substitui vírgula por ponto se precisar)
                # O 'astype(str)' garante que virou texto antes de trocar ',' por '.'
                df_bio['Peso'] = df_bio['Peso'].astype(str).str.replace(',', '.')
                df_bio['Peso'] = pd.to_numeric(df_bio['Peso'], errors='coerce')
                
                df_bio['Massa_Muscular'] = df_bio['Massa_Muscular'].astype(str).str.replace(',', '.')
                df_bio['Massa_Muscular'] = pd.to_numeric(df_bio['Massa_Muscular'], errors='coerce')
                
                # 3. Cria o Gráfico
                st.line_chart(df_bio, x="Data", y=["Peso", "Massa_Muscular"], color=["#FF4B4B", "#1C83E1"])
            else:
                st.info("Ainda não há dados suficientes para gerar o gráfico.")
        else:
            st.warning("Erro ao baixar dados da planilha.")
    except Exception as e:
        st.error(f"Erro ao gerar gráfico: {e}")