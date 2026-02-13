import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# Configuração da Página
st.set_page_config(page_title="Sistema Escolar", layout="wide")

# Função de Conexão Segura
@st.cache_resource
def conectar_google_sheets():
    # Aqui pegamos a senha dos "Segredos" do Streamlit, não do arquivo json
    credenciais_dict = st.secrets["gcp_service_account"]
    
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    credentials = Credentials.from_service_account_info(credenciais_dict, scopes=scopes)
    gc = gspread.authorize(credentials)
    return gc

# Função Principal
def main():
    st.title("🎓 Sistema de Gestão de Professores")
    st.write("Conectando ao banco de dados...")

    try:
        gc = conectar_google_sheets()
        
        # Tenta abrir a planilha CADASTROS
        # ATENÇÃO: O nome do arquivo no código deve ser EXATAMENTE igual ao do Drive
        sh_cadastros = gc.open("CADASTROS") 
        ws_prof = sh_cadastros.worksheet("CADASTRO_PROF")
        
        # Mostra que conectou
        st.success("Conexão com CADASTROS realizada com sucesso!")
        
        # Lê os dados
        df_professores = pd.DataFrame(ws_prof.get_all_records())
        
        # Filtros
        st.sidebar.header("Opções")
        mes = st.sidebar.selectbox("Mês Referência", ["JANEIRO", "FEVEREIRO", "MARCO", "ABRIL", "MAIO", "JUNHO"])
        
        if st.sidebar.button("Gerar Relatório"):
            st.write(f"Buscando atividades de {len(df_professores)} professores para o mês de {mes}...")
            
            # Barra de progresso
            bar = st.progress(0)
            dados_consolidados = []
            
            for i, row in df_professores.iterrows():
                # Atualiza barra
                bar.progress((i + 1) / len(df_professores))
                
                prof = row['PROFESSOR (A)']
                link = row['LINK DA PLANILHA']
                
                if link:
                    try:
                        # Abre a planilha individual
                        sh_ind = gc.open_by_url(link)
                        ws_mes = sh_ind.worksheet(mes)
                        registros = ws_mes.get_all_records()
                        
                        for reg in registros:
                            reg['Professor'] = prof
                            dados_consolidados.append(reg)
                            
                    except Exception as e:
                        st.warning(f"Não foi possível ler dados de {prof}. Verifique se a aba '{mes}' existe.")
            
            bar.empty()
            
            if dados_consolidados:
                df_final = pd.DataFrame(dados_consolidados)
                st.subheader("Relatório Consolidado")
                st.dataframe(df_final)
                
                # Botão de Download
                csv = df_final.to_csv(index=False).encode('utf-8')
                st.download_button("Baixar CSV", csv, "relatorio.csv", "text/csv")
            else:
                st.warning("Nenhum dado encontrado.")
                
    except Exception as e:
        st.error(f"Erro de conexão: {e}")
        st.info("Verifique se compartilhou a planilha CADASTROS com o email do robô.")

if __name__ == "__main__":
    main()
