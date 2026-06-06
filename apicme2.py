import time
import requests
import json
import os
import sys
import subprocess
import urllib.parse
import random
import undetected_chromedriver as uc
from datetime import datetime, timedelta
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# tomllib é nativo no Python 3.11+; para versões anteriores, usar tomli
try:
    import tomllib
except ImportError:
    import tomli as tomllib

# ==============================================================================
# CONFIGURAÇÕES
# ==============================================================================
REPO_LOCAL    = r"C:\Users\Usuário\dashboard-market-maker"
PASTA_DESTINO = os.path.join(REPO_LOCAL, "dados")
PERFIL_CHROME = os.path.join(os.getcwd(), "perfil_barchart")
SECRETS_PATH  = os.path.join(REPO_LOCAL, ".streamlit", "secrets.toml")

LISTA_SIMBOLOS = ['IY2M26', 'I0BM26', 'IG2M26']

# Carrega credenciais do secrets.toml (mesmo arquivo do dashboard)
def carregar_credenciais():
    if not os.path.exists(SECRETS_PATH):
        print(f"❌ Arquivo de secrets não encontrado: {SECRETS_PATH}")
        print("   Crie .streamlit/secrets.toml com [barchart] usuario / senha")
        sys.exit(1)
    try:
        with open(SECRETS_PATH, "rb") as f:
            cfg = tomllib.load(f)
        bc = cfg.get("barchart", {})
        usuario = bc.get("usuario", "").strip()
        senha   = bc.get("senha",   "").strip()
        if not usuario or not senha:
            print("❌ [barchart].usuario ou [barchart].senha vazios em secrets.toml")
            sys.exit(1)
        return usuario, senha
    except Exception as e:
        print(f"❌ Erro lendo secrets.toml: {e}")
        sys.exit(1)

USUARIO, SENHA = carregar_credenciais()

if not os.path.exists(PASTA_DESTINO):
    os.makedirs(PASTA_DESTINO)
if not os.path.exists(PERFIL_CHROME):
    os.makedirs(PERFIL_CHROME)
# ==============================================================================
# GIT AUTO-PUSH COM LIMPEZA
# ==============================================================================

def limpar_jsons_antigos(simbolo, data_str, timestamp_atual):
    """Apaga JSONs antigos do mesmo símbolo/data, mantendo só o atual."""
    try:
        arquivos = [
            f for f in os.listdir(PASTA_DESTINO)
            if f.endswith(".json")
            and f.startswith(simbolo)
            and data_str in f
            and timestamp_atual not in f
        ]
        removidos = []
        for arq in arquivos:
            caminho_arq = os.path.join(PASTA_DESTINO, arq)
            subprocess.run(["git", "-C", REPO_LOCAL, "rm", "-f", caminho_arq], capture_output=True)
            removidos.append(arq)
        if removidos:
            print(f"  🗑 Removidos: {', '.join(removidos)}")
        return removidos
    except Exception as e:
        print(f"  ⚠️ Erro ao limpar antigos: {e}")
        return []


def git_push(caminho_arquivo, simbolo, data_str, timestamp_atual):
    """Remove JSONs antigos, faz add + commit + push do arquivo atual."""
    nome = os.path.basename(caminho_arquivo)
    try:
        # Pull com rebase pra evitar non-fast-forward
        pull = subprocess.run(
            ["git", "-C", REPO_LOCAL, "pull", "--rebase", "--autostash"],
            capture_output=True
        )
        if pull.returncode != 0:
            print(f"  ⚠️ pull falhou: {pull.stderr.decode(errors='ignore')[:200]}")

        removidos = limpar_jsons_antigos(simbolo, data_str, timestamp_atual)
        subprocess.run(["git", "-C", REPO_LOCAL, "add", caminho_arquivo], check=True, capture_output=True)
        msg = f"auto: {nome}" + (f" | remove {len(removidos)} antigos" if removidos else "")
        subprocess.run(["git", "-C", REPO_LOCAL, "commit", "-m", msg], check=True, capture_output=True)

        # Push com retry: se falhar, faz pull --rebase e tenta de novo
        push = subprocess.run(["git", "-C", REPO_LOCAL, "push"], capture_output=True)
        if push.returncode != 0:
            print(f"  ⚠️ push rejeitado, tentando pull+push de novo...")
            subprocess.run(["git", "-C", REPO_LOCAL, "pull", "--rebase", "--autostash"], capture_output=True)
            push2 = subprocess.run(["git", "-C", REPO_LOCAL, "push"], capture_output=True)
            if push2.returncode != 0:
                print(f"  ⚠️ push falhou novamente: {push2.stderr.decode(errors='ignore')[:200]}")
                return
        print(f"  ↑ GitHub: {nome} enviado com sucesso.")
    except subprocess.CalledProcessError as e:
        print(f"  ⚠️ Erro no git push: {e.stderr.decode() if e.stderr else e}")
# ==============================================================================
# FUNÇÕES
# ==============================================================================

def calcular_datas_alvo():
    hoje = datetime.now().date()
    if hoje.weekday() == 5:
        hoje += timedelta(days=2)
    elif hoje.weekday() == 6:
        hoje += timedelta(days=1)
    return [hoje]

def obter_sessao_premier():
    agora_str = datetime.now().strftime('%H:%M:%S')
    print(f"\n[{agora_str}] --- Iniciando UC (Perfil Persistente + Cookie Bypass) ---")

    options = uc.ChromeOptions()
    options.add_argument(f'--user-data-dir={PERFIL_CHROME}')

    driver = None

    try:
        driver = uc.Chrome(options=options, version_main=148)
        session = requests.Session()

        driver.get("https://www.barchart.com/login")

        try:
            cookies_accept = WebDriverWait(driver, 8).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Aceitar todos')] | //button[contains(text(), 'Accept all')]"))
            )
            cookies_accept.click()
            print("Banner de cookies aceito.")
        except:
            pass

        try:
            wait = WebDriverWait(driver, 10)
            email_field = wait.until(EC.presence_of_element_located((By.NAME, "email")))
            print("Realizando login...")
            email_field.send_keys(USUARIO)
            driver.find_element(By.NAME, "password").send_keys(SENHA)
            driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
            time.sleep(10)
        except:
            print("Sessão já ativa ou campo de login não encontrado.")

        selenium_cookies = driver.get_cookies()
        ua = driver.execute_script("return navigator.userAgent;")
        session.headers.update({'User-Agent': ua})

        token_found = False
        for cookie in selenium_cookies:
            session.cookies.set(cookie['name'], cookie['value'])
            if cookie['name'] == 'XSRF-TOKEN':
                token_unquoted = urllib.parse.unquote(cookie['value'])
                session.headers.update({'x-xsrf-token': token_unquoted})
                token_found = True

        return session if token_found else None

    except Exception as e:
        print(f"Erro no Driver: {e}")
        return None
    finally:
        if driver is not None:
            try:
                driver.quit()
                print("Driver encerrado com sucesso.")
            except:
                pass

# ==============================================================================
# EXECUÇÃO
# ==============================================================================

if __name__ == "__main__":
    while True:
        ts_execucao = datetime.now()
        timestamp_arquivo = ts_execucao.strftime("%H%M%S")

        sessao = obter_sessao_premier()

        if sessao:
            datas_para_baixar = calcular_datas_alvo()
            campos = "strike,lastPrice,volume,openInterest,delta,gamma,theta,vega,rho,optImpliedVolatility,impliedVolatilitySkew,bidPrice,askPrice,tradeTime"

            for simbolo_atual in LISTA_SIMBOLOS:
                sessao.headers.update({'Referer': f'https://www.barchart.com/futures/quotes/{simbolo_atual}/options'})
                for data_obj in datas_para_baixar:
                    data_str = data_obj.strftime("%Y-%m-%d")
                    url = (f"https://www.barchart.com/proxies/core-api/v1/quotes/get"
                           f"?symbol={simbolo_atual}&list=futures.options&fields={campos}"
                           f"&groupBy=optionType&orderBy=strike&orderDir=asc&raw=1&expiration={data_str}")

                    try:
                        res = sessao.get(url)
                        if res.status_code == 200:
                            conteudo = res.json()
                            if 'data' in conteudo and conteudo['data']:
                                caminho = os.path.join(PASTA_DESTINO, f"{simbolo_atual}_{data_str}_{timestamp_arquivo}.json")
                                with open(caminho, 'w') as f:
                                    json.dump(conteudo, f, indent=4)
                                print(f"[{timestamp_arquivo}] SUCESSO: {simbolo_atual} → {os.path.basename(caminho)}")
                                git_push(caminho, simbolo_atual, data_str, timestamp_arquivo)
                        else:
                            print(f"[{timestamp_arquivo}] STATUS {res.status_code} em {simbolo_atual}")
                    except Exception as e:
                        print(f"Erro ao baixar {simbolo_atual}: {e}")

                    time.sleep(random.uniform(2, 5))

        intervalo = 1080 + random.randint(1, 60)
        print(f"\nAguardando {intervalo}s para a próxima rodada...")
        time.sleep(intervalo)