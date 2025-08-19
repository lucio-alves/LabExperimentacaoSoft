import requests
import pandas as pd
import time
from tqdm import tqdm
from datetime import datetime

# Insira seu token do GitHub aqui
GITHUB_TOKEN = " "

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}"
}

# Função para obter os 1000 repositórios mais estrelados
def fetch_top_repositories():
    repos = []
    for page in range(1, 11):
        url = f"https://api.github.com/search/repositories?q=stars:>1&sort=stars&order=desc&per_page=100&page={page}"
        r = requests.get(url, headers=HEADERS)
        if r.status_code == 200:
            repos.extend(r.json()["items"])
        else:
            print(f"Erro na página {page}: {r.status_code}")
            break
        time.sleep(1)
    return repos

# Função para contar releases
def get_releases_count(full_name):
    url = f"https://api.github.com/repos/{full_name}/releases"
    r = requests.get(url, headers=HEADERS)
    if r.status_code == 200:
        return len(r.json())
    return None

# Função para contar pull requests aceitos (merged)
def get_pull_requests_count(full_name):
    url = f"https://api.github.com/repos/{full_name}/pulls?state=closed&per_page=100"
    r = requests.get(url, headers=HEADERS)
    count = 0
    if r.status_code == 200:
        prs = r.json()
        for pr in prs:
            if pr.get("merged_at"):
                count += 1
    return count

# Função para issues abertas e fechadas
def get_issues_stats(full_name):
    owner, repo = full_name.split("/")
    url_closed = f"https://api.github.com/search/issues?q=repo:{owner}/{repo}+type:issue+state:closed"
    url_total = f"https://api.github.com/search/issues?q=repo:{owner}/{repo}+type:issue"
    r_closed = requests.get(url_closed, headers=HEADERS)
    r_total = requests.get(url_total, headers=HEADERS)
    if r_closed.status_code == 200 and r_total.status_code == 200:
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
        pulls = get_pull_requests_count(name)
        closed_issues, total_issues = get_issues_stats(name)

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
        time.sleep(0.5)
    return pd.DataFrame(data)

# func resultado


# MAIN
if __name__ == "__main__":
    print("🔍 Coletando repositórios...")
    top_repos = fetch_top_repositories()

    print("📊 Coletando métricas por repositório...")
    df_repos = process_repositories(top_repos)

    print("\n✅ Respostas das Questões:\n")
    responder_questoes(df_repos)

