import requests
import pandas as pd
import time, urllib.parse
from tqdm import tqdm
from datetime import datetime
import re

# Insira seu token do GitHub aqui
GITHUB_TOKEN = ""

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}"
}

# Função para fazer requisições com retry
def make_request_with_retry(url, max_retries=3):
    for attempt in range(max_retries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=30)
            if r.status_code == 200:
                return r
            elif r.status_code == 403:
                print(f"Rate limit atingido.")
                time.sleep(60)
            else:
                print(f"Erro {r.status_code} na tentativa {attempt + 1}")
                time.sleep(5)
        except requests.exceptions.RequestException as e:
            print(f"Erro de conexão na tentativa {attempt + 1}: {e}")
            time.sleep(10)
    return None


# Função para obter os 1000 repositórios mais estrelados
def fetch_top_repositories():
    repos = []
    for page in range(1, 11):
        url = f"https://api.github.com/search/repositories?q=stars:>1&sort=stars&order=desc&per_page=100&page={page}"
        r = make_request_with_retry(url)
        if r and r.status_code == 200:
            repos.extend(r.json()["items"])
        else:
            print(f"Erro na página {page}")
            break
        time.sleep(2)  # Aguardar 2 segundos entre as requisições
    return repos

# Função para contar releases
def get_releases_count(full_name: str) -> int | None:
    # 1 item por página -> número da última página = total
    url = f"https://api.github.com/repos/{full_name}/releases?per_page=1"
    r = make_request_with_retry(url)
    if not r:
        return None

    if r.status_code == 404:
        return 0
    if r.status_code != 200:
        return None

    link = r.headers.get("Link", "")
    m = re.search(r'[?&]page=(\d+)>;\s*rel="last"', link)
    if m:
        return int(m.group(1))

    # Sem Link header: só essa página existe (0 ou 1 release, pois per_page=1)
    return len(r.json())

# Função para contar pull requests aceitos (merged)
def get_pull_requests_count(full_name: str, max_retries: int = 3) -> int | None:
    owner, repo = full_name.split("/")
    q = f'repo:{owner}/{repo} is:pr is:merged'
    url = f'https://api.github.com/search/issues?q={urllib.parse.quote(q)}&per_page=1'

    for attempt in range(max_retries):
        r = make_request_with_retry(url)  
        if not r:
            return None
        if r.status_code == 403:
            reset = r.headers.get("X-RateLimit-Reset")
            if reset and reset.isdigit():
                sleep_s = max(0, int(reset) - int(time.time()) + 1)
                time.sleep(min(sleep_s, 60))
                continue
            time.sleep(10)
            continue
        if r.status_code == 422:
            time.sleep(2)
            continue

        if r.status_code == 200:
            data = r.json()
            return int(data.get("total_count", 0))
        time.sleep(5)

    return None

# Função para issues abertas e fechadas
def get_issues_stats(full_name):
    owner, repo = full_name.split("/")
    url_closed = f"https://api.github.com/search/issues?q=repo:{owner}/{repo}+type:issue+state:closed"
    url_total = f"https://api.github.com/search/issues?q=repo:{owner}/{repo}+type:issue"
    
    r_closed = make_request_with_retry(url_closed)
    time.sleep(1)  # Delay entre as duas requisições
    r_total = make_request_with_retry(url_total)
    
    if r_closed and r_total and r_closed.status_code == 200 and r_total.status_code == 200:
        closed = r_closed.json()["total_count"]
        total = r_total.json()["total_count"]
        return closed, total
    return None, None

# Processar todos os repositórios
def process_repositories(repos_raw):
    data = []
    for repo in tqdm(repos_raw, desc="Coletando dados dos repositórios"):
        name = repo["full_name"]
        created = repo["created_at"]
        updated = repo["updated_at"]
        language = repo["language"]

        age_days = (datetime.now() - datetime.strptime(created, "%Y-%m-%dT%H:%M:%SZ")).days
        last_update_days = (datetime.now() - datetime.strptime(updated, "%Y-%m-%dT%H:%M:%SZ")).days

        releases = get_releases_count(name)
        time.sleep(1)  # Delay entre requests
        
        pulls = get_pull_requests_count(name)
        time.sleep(1)  # Delay entre requests
        
        closed_issues, total_issues = get_issues_stats(name)
        time.sleep(2)  # Delay maior após múltiplas requests

        issues_ratio = None
        if total_issues and total_issues > 0:
            issues_ratio = closed_issues / total_issues

        data.append({
            "name": name,
            "age_days": age_days,
            "days_since_update": last_update_days,
            "language": language,
            "releases": releases,
            "pull_requests": pulls,
            "issues_closed_ratio": issues_ratio
        })
        
    return pd.DataFrame(data)


# MAIN
if __name__ == "__main__":
    print("\n Métricas:\n")
    df = process_repositories()