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