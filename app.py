import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# Configuração da Página
st.set_page_config(page_title="Sistema Escolar", layout="wide")

# Função de Conexão Segura
@st.cache_resource
def conectar_google_sheets():
    # Aqui pegamos a senha dos "Segredos" do Streamlit
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
        sh_cadastros = gc.open("CADASTROS") 
        ws_prof = sh_cadastros.worksheet("CADASTRO_PROF")
        
        # Mostra que conectou
        st.success("Conexão com CADASTROS realizada com sucesso!")
        
        # --- CORREÇÃO APLICADA AQUI ---
        # Em vez de get_all_records (que exige cabeçalhos perfeitos),
        # usamos get_all_values para ler tudo como texto bruto.
        dados_brutos = ws_prof.get_all_values()
        
        # A primeira linha (índice 0) é o cabeçalho
        cabecalho = dados_brutos[0]
        # O restante (do índice 1 em diante) são os dados
        dados_linhas = dados_brutos[1:]
        
        # Criamos a tabela (DataFrame) manualmente
        df_professores = pd.DataFrame(dados_linhas, columns=cabecalho)
        # -------------------------------
        
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
                        
                        # Mesma lógica para ler as planilhas individuais (evita erro de coluna vazia lá também)
                        dados_ind = ws_mes.get_all_values()
                        if len(dados_ind) > 1:
                            cabecalho_ind = dados_ind[0]
                            # Limpa espaços em branco dos cabeçalhos para evitar erros
                            cabecalho_ind = [c.strip() for c in cabecalho_ind]
                            
                            registros = []
                            for linha in dados_ind[1:]:
                                # Cria um dicionário combinando cabeçalho com a linha
                                reg = dict(zip(cabecalho_ind, linha))
                                reg['Professor'] = prof
                                dados_consolidados.append(reg)
                            
                    except Exception as e:
                        # Apenas avisa no console do servidor, não para o código
                        print(f"Erro em {prof}: {e}")
            
            bar.empty()
            
            if dados_consolidados:
                df_final = pd.DataFrame(dados_consolidados)
                st.subheader("Relatório Consolidado")
                st.dataframe(df_final)
                
                # Botão de Download
                csv = df_final.to_csv(index=False).encode('utf-8')
                st.download_button("Baixar CSV", csv, f"relatorio_{mes}.csv", "text/csv")
            else:
                st.warning(f"Nenhum dado encontrado ou erro ao ler as abas de '{mes}'. Verifique se o nome da aba nas planilhas dos professores está exatamente igual.")
                
    except Exception as e:
        st.error(f"Erro Geral: {e}")
        st.info("Dica: Verifique se o nome da aba na planilha CADASTROS é realmente 'CADASTRO_PROF'.")

if __name__ == "__main__":
    main()
