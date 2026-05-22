# SPDX-License-Identifier: MIT
# Copyright (c) 2026 vesper
"""
RAG (Retrieval Augmented Generation) module for Vesper.
Fetches current context from various sources to supplement AI knowledge.
"""

import logging
import os
import re
from datetime import datetime, timezone

import requests

logger = logging.getLogger(__name__)


def fetch_pypi_package_info(package_name):
    """Fetch latest version and info from PyPI."""
    try:
        resp = requests.get(f"https://pypi.org/pypi/{package_name}/json", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return {
                "name": data["info"]["name"],
                "version": data["info"]["version"],
                "summary": data["info"].get("summary", ""),
                "requires_python": data["info"].get("requires_python", ""),
            }
    except Exception as e:
        logger.debug(f"PyPI lookup failed for {package_name}: {e}")
    return None


def fetch_npm_package_info(package_name):
    """Fetch latest version and info from npm registry."""
    try:
        resp = requests.get(f"https://registry.npmjs.org/{package_name}/latest", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return {
                "name": data.get("name", package_name),
                "version": data.get("version", ""),
                "description": data.get("description", ""),
            }
    except Exception as e:
        logger.debug(f"npm lookup failed for {package_name}: {e}")
    return None


def fetch_security_advisories(ecosystem, package_name):
    """Fetch security advisories from GitHub Advisory Database."""
    try:
        query = """
        query($ecosystem: AdvisoryEcosystem, $package: String) {
          securityAdvisories(first: 3, ecosystem: $ecosystem, package: $package) {
            nodes {
              severity
              summary
              identifier
            }
          }
        }
        """
        variables = {"ecosystem": ecosystem.upper(), "package": package_name}
        resp = requests.post(
            "https://api.github.com/graphql",
            json={"query": query, "variables": variables},
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            advisories = data.get("data", {}).get("securityAdvisories", {}).get("nodes", [])
            return [{"id": a["identifier"], "severity": a["severity"], "summary": a["summary"]} for a in advisories]
    except Exception as e:
        logger.debug(f"Security advisory lookup failed for {package_name}: {e}")
    return []


def fetch_github_recent_changes(repo_name, files_changed, token):
    """Fetch recent commits/changes for files in the PR."""
    if not token or not repo_name:
        return []

    max_items = 5
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    changes = []

    try:
        for filepath in files_changed[:max_items]:
            file_name = filepath.split("/")[-1]
            query = f"repo:{repo_name} path:{file_name} committer-date:>2025-01-01"
            resp = requests.get(
                "https://api.github.com/search/commits",
                params={"q": query, "per_page": 3},
                headers=headers,
                timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json()
                for item in data.get("items", [])[:2]:
                    changes.append(
                        {
                            "file": file_name,
                            "sha": item["sha"][:7],
                            "message": item["commit"]["message"].split("\n")[0][:100],
                            "date": item["commit"]["committer"]["date"][:10],
                        }
                    )
    except Exception as e:
        logger.debug(f"GitHub recent changes lookup failed: {e}")

    return changes


def fetch_docs_search(query_str):
    """Search documentation using DuckDuckGo instant answer API."""
    try:
        resp = requests.get(
            "https://api.duckduckgo.com/",
            params={"q": query_str, "format": "json", "no_html": 1},
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get("AbstractText"):
                return {
                    "title": data.get("Heading", ""),
                    "content": data["AbstractText"][:500],
                    "url": data.get("AbstractURL", ""),
                }
    except Exception as e:
        logger.debug(f"Docs search failed for {query_str}: {e}")
    return None


def fetch_stackoverflow_answers(question, tags):
    """Fetch relevant StackOverflow answers using Stack Exchange API."""
    try:
        params = {
            "order": "desc",
            "sort": "relevance",
            "intitle": question,
            "site": "stackoverflow",
            "pagesize": 3,
        }
        if tags:
            params["tagged"] = ",".join(tags[:2])
        resp = requests.get("https://api.stackexchange.com/2.3/search", params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            results = []
            for item in data.get("items", [])[:3]:
                results.append(
                    {
                        "title": item.get("title", "")[:100],
                        "score": item.get("score", 0),
                        "link": item.get("link", ""),
                        "is_answered": item.get("is_answered", False),
                    }
                )
            return results
    except Exception as e:
        logger.debug(f"StackOverflow lookup failed for {question}: {e}")
    return []


def fetch_tech_news():
    """Fetch recent tech news using NewsAPI."""
    try:
        news_api_key = os.getenv("NEWS_API_KEY")
        if not news_api_key:
            news_api_key = "demo"
        resp = requests.get(
            "https://newsapi.org/v2/top-headlines",
            params={"category": "technology", "language": "en", "pageSize": 5},
            headers={"X-Api-Key": news_api_key},
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            return [
                {"title": a["title"][:100], "source": a["source"]["name"], "url": a["url"]}
                for a in data.get("articles", [])[:5]
            ]
    except Exception as e:
        logger.debug(f"News lookup failed: {e}")
    return []


def fetch_weather(location):
    """Fetch current weather for a location using OpenWeatherMap."""
    try:
        weather_api_key = os.getenv("OPENWEATHER_API_KEY")
        if not weather_api_key:
            return None
        resp = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={"q": location, "appid": weather_api_key, "units": "metric"},
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            return {
                "location": data.get("name", ""),
                "temp": data["main"]["temp"],
                "description": data["weather"][0]["description"],
                "humidity": data["main"]["humidity"],
            }
    except Exception as e:
        logger.debug(f"Weather lookup failed for {location}: {e}")
    return None


def fetch_reddit_discussions(query):
    """Fetch Reddit discussions using Reddit API."""
    try:
        headers = {"User-Agent": "Vesper/1.0"}
        resp = requests.get(
            "https://www.reddit.com/search.json",
            params={"q": query, "limit": 5, "sort": "relevance"},
            headers=headers,
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            results = []
            for child in data["data"]["children"][:5]:
                item = child["data"]
                results.append(
                    {
                        "title": item.get("title", "")[:100],
                        "score": item.get("score", 0),
                        "subreddit": item.get("subreddit", ""),
                        "url": f"https://reddit.com{item.get('permalink', '')}",
                    }
                )
            return results
    except Exception as e:
        logger.debug(f"Reddit lookup failed for {query}: {e}")
    return []


def fetch_hackernews(query):
    """Fetch HackerNews links related to query."""
    try:
        resp = requests.get("https://hn.algolia.com/api/v1/search", params={"query": query, "hitsPerPage": 5}, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return [
                {
                    "title": h["title"][:100],
                    "points": h.get("points", 0),
                    "url": h.get("url", f"https://news.ycombinator.com/item?id={h['objectID']}"),
                }
                for h in data.get("hits", [])[:5]
            ]
    except Exception as e:
        logger.debug(f"HackerNews lookup failed for {query}: {e}")
    return []


def fetch_crates_info(crate_name):
    """Fetch Rust crate info from crates.io."""
    try:
        resp = requests.get(f"https://crates.io/api/v1/crates/{crate_name}", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return {
                "name": data["crate"]["name"],
                "version": data["version"]["num"],
                "description": data["version"].get("description", ""),
            }
    except Exception as e:
        logger.debug(f"crates.io lookup failed for {crate_name}: {e}")
    return None


def fetch_go_info(module_name):
    """Fetch Go module info from pkg.go.dev."""
    try:
        resp = requests.get(f"https://pkg.go.dev/_/go?tab=licenses&mod={module_name}", timeout=10, allow_redirects=False)
        location = resp.headers.get("Location", "")
        if location:
            mod_path = location.split("?mod=")[-1] if "?mod=" in location else module_name
            resp = requests.get(f"https://pkg.go.dev/{mod_path}", timeout=10)
        if resp.status_code == 200:
            return {"module": module_name, "description": "Go module"}
    except Exception as e:
        logger.debug(f"Go module lookup failed for {module_name}: {e}")
    return None


def fetch_docker_image(image_name):
    """Fetch Docker image info from Docker Hub."""
    try:
        resp = requests.get(f"https://hub.docker.com/v2/repositories/{image_name}/tags", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("results"):
                return {
                    "image": image_name,
                    "latest": data["results"][0]["name"],
                    "pulls": data["results"][0].get("pulls", 0),
                }
    except Exception as e:
        logger.debug(f"Docker Hub lookup failed for {image_name}: {e}")
    return None


def fetch_web_search(query):
    """General web search using DuckDuckGo HTML."""
    try:
        resp = requests.get(
            "https://html.duckduckgo.com/html/",
            params={"q": query},
            timeout=10,
        )
        if resp.status_code == 200:
            titles = re.findall(r'class="result__a"[^>]*>([^<]+)<', resp.text[:5000])
            links = re.findall(r'class="result__url"[^>]*>([^<]+)<', resp.text[:5000])
            results = []
            for title, link in zip(titles[:5], links[:5]):
                results.append({"title": title.strip()[:100], "url": link.strip()})
            return results
    except Exception as e:
        logger.debug(f"Web search failed for {query}: {e}")
    return []


def fetch_aws_docs(service):
    """Fetch AWS documentation for a service."""
    try:
        resp = requests.get(
            f"https://docs.aws.amazon.com/{service.lower()}/latest/userguide/",
            timeout=10,
        )
        if resp.status_code == 200:
            return {"service": service, "url": resp.url}
    except Exception as e:
        logger.debug(f"AWS docs lookup failed for {service}: {e}")
    return None


def fetch_azure_docs(service):
    """Fetch Azure documentation for a service."""
    try:
        resp = requests.get(
            f"https://learn.microsoft.com/azure/{service.lower()}/",
            timeout=10,
        )
        if resp.status_code == 200:
            return {"service": service, "url": resp.url}
    except Exception as e:
        logger.debug(f"Azure docs lookup failed for {service}: {e}")
    return None


def fetch_gcp_docs(service):
    """Fetch Google Cloud documentation for a service."""
    try:
        resp = requests.get(
            f"https://cloud.google.com/{service.lower()}/docs",
            timeout=10,
            allow_redirects=True,
        )
        if resp.status_code == 200:
            return {"service": service, "url": resp.url}
    except Exception as e:
        logger.debug(f"GCP docs lookup failed for {service}: {e}")
    return None


def fetch_apt_package_info(package_name):
    """Fetch Ubuntu/Debian package info."""
    try:
        resp = requests.get(f"https://packages.ubuntu.com/api/{package_name}", timeout=10)
        if resp.status_code == 200:
            return {"package": package_name}
    except Exception:
        pass
    try:
        resp = requests.get(f"https://api.launchpad.net/ubuntu/{package_name}", timeout=10)
        if resp.status_code == 200:
            return {"package": package_name}
    except Exception as e:
        logger.debug(f"APT lookup failed for {package_name}: {e}")
    return None


def fetch_brew_info(package_name):
    """Fetch Homebrew package info."""
    try:
        resp = requests.get(f"https://formulae.brew.sh/api/formula/{package_name}.json", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return {"name": data.get("name", package_name), "desc": data.get("desc", "")}
    except Exception as e:
        logger.debug(f"Brew lookup failed for {package_name}: {e}")
    return None


def fetch_conda_info(package_name):
    """Fetch Conda package info."""
    try:
        resp = requests.get(f"https://api.anaconda.org/package/{package_name}", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return {"name": data.get("name", package_name), "version": data.get("latest_version", "")}
    except Exception as e:
        logger.debug(f"Conda lookup failed for {package_name}: {e}")
    return None


def fetch_nuget_info(package_name):
    """Fetch NuGet package info."""
    try:
        resp = requests.get(f"https://api.nuget.org/v3-flatcontainer/{package_name}/index.json", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return {"name": package_name, "version": data.get("latestVersion", "")}
    except Exception as e:
        logger.debug(f"NuGet lookup failed for {package_name}: {e}")
    return None


def fetch_maven_info(group_id, artifact_id):
    """Fetch Maven/Java package info."""
    try:
        resp = requests.get(
            f"https://search.maven.org/solrsearch/select?q=g:{group_id}+AND+a:{artifact_id}&rows=1&wt=json",
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            docs = data.get("response", {}).get("docs", [])
            if docs:
                return {"group": group_id, "artifact": artifact_id, "version": docs[0].get("latestVersion", "")}
    except Exception as e:
        logger.debug(f"Maven lookup failed for {group_id}:{artifact_id}: {e}")
    return None


def fetch_pub_info(package_name):
    """Fetch Dart/Flutter package info from pub.dev."""
    try:
        resp = requests.get(f"https://pub.dev/api/packages/{package_name}", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return {"name": package_name, "version": data.get("latest", {}).get("version", "")}
    except Exception as e:
        logger.debug(f"pub.dev lookup failed for {package_name}: {e}")
    return None


def fetch_helm_chart_info(chart_name):
    """Fetch Helm chart info from Artifact Hub."""
    try:
        resp = requests.get(f"https://artifacthub.io/api/v1/packages/search?repo={chart_name}&limit=1", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("packages"):
                return {"name": chart_name, "version": data["packages"][0].get("version", "")}
    except Exception as e:
        logger.debug(f"Helm lookup failed for {chart_name}: {e}")
    return None


def fetch_terraform_module_info(module_name):
    """Fetch Terraform module info from Registry."""
    try:
        resp = requests.get(f"https://registry.terraform.io/v1/modules/{module_name}", timeout=10)
        if resp.status_code == 200:
            return {"name": module_name}
    except Exception as e:
        logger.debug(f"Terraform lookup failed for {module_name}: {e}")
    return None


def fetch_huggingface_models(query):
    """Fetch HuggingFace models."""
    try:
        resp = requests.get(
            f"https://huggingface.co/api/models?search={query}&sort=downloads&direction=-1&limit=3", timeout=10
        )
        if resp.status_code == 200:
            data = resp.json()
            return [{"name": m.get("modelId", ""), "downloads": m.get("downloads", 0)} for m in data[:3]]
    except Exception as e:
        logger.debug(f"HuggingFace lookup failed for {query}: {e}")
    return []


def fetch_kaggle_datasets(query):
    """Fetch Kaggle datasets."""
    try:
        api_key = os.getenv("KAGGLE_API_KEY")
        if not api_key:
            return []
        resp = requests.get(
            "https://www.kaggle.com/api/v1/datasets/list",
            params={"sort_by": "hottest", "page": 1},
            headers={"Authorization": f"Basic {api_key}"},
            timeout=10,
        )
        if resp.status_code == 200:
            return resp.json()[:3]
    except Exception as e:
        logger.debug(f"Kaggle lookup failed: {e}")
    return []


def fetch_medium_articles(query):
    """Fetch Medium articles."""
    try:
        resp = requests.get(
            "https://medium.com/_/api/search",
            params={"q": query, "limit": 3},
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            return [{"title": p.get("title", ""), "url": p.get("url", "")} for p in data.get("posts", [])[:3]]
    except Exception as e:
        logger.debug(f"Medium lookup failed for {query}: {e}")
    return []


def fetch_producthunt(query):
    """Fetch Product Hunt products."""
    try:
        resp = requests.get(
            "https://api.producthunt.com/v2/api/graphql",
            json={"query": f'{{ search(query: "{query}", limit: 3) {{ edges {{ node {{ name tagline url }} }} }} }}'},
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            products = data.get("data", {}).get("search", {}).get("edges", [])
            return [{"name": p["node"]["name"], "tagline": p["node"]["tagline"]} for p in products]
    except Exception as e:
        logger.debug(f"ProductHunt lookup failed for {query}: {e}")
    return []


def fetch_confluence_pages(query):
    """Fetch Confluence pages (requires URL configuration)."""
    try:
        base_url = os.getenv("CONFLUENCE_URL")
        if not base_url:
            return []
        api_key = os.getenv("CONFLUENCE_API_KEY")
        if not api_key:
            return []
        resp = requests.get(
            f"{base_url}/rest/api/search",
            params={"cql": f'text ~ "{query}"', "limit": 3},
            headers={"Authorization": f"Basic {api_key}"},
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            return [{"title": r.get("title", ""), "url": r.get("url", "")} for r in data.get("results", [])[:3]]
    except Exception as e:
        logger.debug(f"Confluence lookup failed: {e}")
    return []


def fetch_cocoapods_info(pod_name):
    """Fetch CocoaPods info."""
    try:
        resp = requests.get(f"https://cdn.cocoapods.org/api/pods/{pod_name}.json", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return {"name": pod_name, "version": data.get("version", "")}
    except Exception as e:
        logger.debug(f"CocoaPods lookup failed for {pod_name}: {e}")
    return None


def fetch_packagist_info(package_name):
    """Fetch PHP Composer package info."""
    try:
        resp = requests.get(f"https://packagist.org/packages/{package_name}.json", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return {"name": package_name, "version": data.get("versions", [{}])[0].get("version", "")}
    except Exception as e:
        logger.debug(f"Packagist lookup failed for {package_name}: {e}")
    return None


def fetch_rubygems_info(gem_name):
    """Fetch Ruby gem info."""
    try:
        resp = requests.get(f"https://rubygems.org/api/v1/gems/{gem_name}.json", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return {"name": gem_name, "version": data.get("version", "")}
    except Exception as e:
        logger.debug(f"RubyGems lookup failed for {gem_name}: {e}")
    return None


def fetch_cloudflare_docs(service):
    """Fetch Cloudflare documentation."""
    try:
        resp = requests.get(f"https://developers.cloudflare.com/{service.lower()}/", timeout=10)
        if resp.status_code == 200:
            return {"service": service, "url": resp.url}
    except Exception as e:
        logger.debug(f"Cloudflare docs lookup failed for {service}: {e}")
    return None


def fetch_vercel_docs(service):
    """Fetch Vercel documentation."""
    try:
        resp = requests.get(f"https://vercel.com/docs/{service.lower()}", timeout=10)
        if resp.status_code == 200:
            return {"service": service, "url": resp.url}
    except Exception as e:
        logger.debug(f"Vercel docs lookup failed for {service}: {e}")
    return None


def fetch_heroku_docs(service):
    """Fetch Heroku documentation."""
    try:
        resp = requests.get(f"https://devcenter.heroku.com/categories/{service.lower()}", timeout=10)
        if resp.status_code == 200:
            return {"service": service, "url": resp.url}
    except Exception as e:
        logger.debug(f"Heroku docs lookup failed for {service}: {e}")
    return None


def fetch_slack_docs(method):
    """Fetch Slack API documentation."""
    try:
        resp = requests.get(f"https://api.slack.com/methods/{method}", timeout=10)
        if resp.status_code == 200:
            return {"method": method, "url": resp.url}
    except Exception as e:
        logger.debug(f"Slack docs lookup failed for {method}: {e}")
    return None


def fetch_discord_docs(resource):
    """Fetch Discord developer documentation."""
    try:
        resp = requests.get(f"https://discord.com/developers/docs/{resource.lower()}", timeout=10)
        if resp.status_code == 200:
            return {"resource": resource, "url": resp.url}
    except Exception as e:
        logger.debug(f"Discord docs lookup failed for {resource}: {e}")
    return None


def fetch_telegram_docs(method):
    """Fetch Telegram Bot API documentation."""
    try:
        resp = requests.get(f"https://core.telegram.org/bots/api#{method.lower()}", timeout=10)
        if resp.status_code == 200:
            return {"method": method, "url": resp.url}
    except Exception as e:
        logger.debug(f"Telegram docs lookup failed for {method}: {e}")
    return None


def fetch_jest_docs(method):
    """Fetch Jest documentation."""
    try:
        resp = requests.get(f"https://jestjs.io/docs/{method.lower()}", timeout=10)
        if resp.status_code == 200:
            return {"method": method, "url": resp.url}
    except Exception as e:
        logger.debug(f"Jest docs lookup failed: {e}")
    return None


def fetch_pytest_docs(method):
    """Fetch Pytest documentation."""
    try:
        resp = requests.get(f"https://docs.pytest.org/en/stable/{method}.html", timeout=10)
        if resp.status_code == 200:
            return {"method": method, "url": resp.url}
    except Exception as e:
        logger.debug(f"Pytest docs lookup failed: {e}")
    return None


def fetch_rspec_docs(method):
    """Fetch RSpec documentation."""
    try:
        resp = requests.get(f"https://rspec.info/documentation/{method}/", timeout=10)
        if resp.status_code == 200:
            return {"method": method, "url": resp.url}
    except Exception as e:
        logger.debug(f"RSpec docs lookup failed: {e}")
    return None


def fetch_sonarcloud_issues(project):
    """Fetch SonarCloud issues."""
    try:
        token = os.getenv("SONARCLOUD_TOKEN")
        if not token:
            return []
        resp = requests.get(
            "https://sonarcloud.io/api/issues/search",
            params={"projects": project, "limit": 3},
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            return [{"key": i.get("key"), "severity": i.get("severity")} for i in data.get("issues", [])[:3]]
    except Exception as e:
        logger.debug(f"SonarCloud lookup failed for {project}: {e}")
    return []


def fetch_postgresql_docs(topic):
    """Fetch PostgreSQL documentation."""
    try:
        resp = requests.get(f"https://www.postgresql.org/docs/current/{topic.lower()}.html", timeout=10)
        if resp.status_code == 200:
            return {"topic": topic, "url": resp.url}
    except Exception as e:
        logger.debug(f"PostgreSQL docs lookup failed: {e}")
    return None


def fetch_mongodb_docs(topic):
    """Fetch MongoDB documentation."""
    try:
        resp = requests.get(f"https://www.mongodb.com/docs/drivers/{topic.lower()}", timeout=10)
        if resp.status_code == 200:
            return {"topic": topic, "url": resp.url}
    except Exception as e:
        logger.debug(f"MongoDB docs lookup failed: {e}")
    return None


def fetch_redis_docs(topic):
    """Fetch Redis documentation."""
    try:
        resp = requests.get(f"https://redis.io/docs/{topic.lower()}/", timeout=10)
        if resp.status_code == 200:
            return {"topic": topic, "url": resp.url}
    except Exception as e:
        logger.debug(f"Redis docs lookup failed: {e}")
    return None


def fetch_prisma_docs(topic):
    """Fetch Prisma documentation."""
    try:
        resp = requests.get(f"https://www.prisma.io/docs/{topic.lower()}", timeout=10)
        if resp.status_code == 200:
            return {"topic": topic, "url": resp.url}
    except Exception as e:
        logger.debug(f"Prisma docs lookup failed: {e}")
    return None


def fetch_swagger_docs(api_name):
    """Fetch OpenAPI/Swagger documentation."""
    try:
        resp = requests.get("https://swagger.io/specification/", timeout=10)
        if resp.status_code == 200:
            return {"api": api_name, "url": resp.url}
    except Exception as e:
        logger.debug(f"Swagger docs lookup failed: {e}")
    return None


def fetch_graphql_docs(topic):
    """Fetch GraphQL documentation."""
    try:
        resp = requests.get(f"https://graphql.org/learn/{topic.lower()}/", timeout=10)
        if resp.status_code == 200:
            return {"topic": topic, "url": resp.url}
    except Exception as e:
        logger.debug(f"GraphQL docs lookup failed: {e}")
    return None


def fetch_github_actions_docs(action):
    """Fetch GitHub Actions documentation."""
    try:
        resp = requests.get(f"https://docs.github.com/en/actions/{action.lower()}", timeout=10)
        if resp.status_code == 200:
            return {"action": action, "url": resp.url}
    except Exception as e:
        logger.debug(f"GitHub Actions docs lookup failed: {e}")
    return None


def fetch_gitlab_ci_docs(topic):
    """Fetch GitLab CI documentation."""
    try:
        resp = requests.get(f"https://docs.gitlab.com/ee/ci/{topic.lower()}.html", timeout=10)
        if resp.status_code == 200:
            return {"topic": topic, "url": resp.url}
    except Exception as e:
        logger.debug(f"GitLab CI docs lookup failed: {e}")
    return None


def fetch_jenkins_docs(topic):
    """Fetch Jenkins documentation."""
    try:
        resp = requests.get(f"https://www.jenkins.io/doc/{topic.lower()}/", timeout=10)
        if resp.status_code == 200:
            return {"topic": topic, "url": resp.url}
    except Exception as e:
        logger.debug(f"Jenkins docs lookup failed: {e}")
    return None


def fetch_datadog_docs(topic):
    """Fetch Datadog documentation."""
    try:
        resp = requests.get(f"https://docs.datadoghq.com/{topic.lower()}/", timeout=10)
        if resp.status_code == 200:
            return {"topic": topic, "url": resp.url}
    except Exception as e:
        logger.debug(f"Datadog docs lookup failed: {e}")
    return None


def fetch_newrelic_docs(topic):
    """Fetch New Relic documentation."""
    try:
        resp = requests.get(f"https://docs.newrelic.com/docs/{topic.lower()}/", timeout=10)
        if resp.status_code == 200:
            return {"topic": topic, "url": resp.url}
    except Exception as e:
        logger.debug(f"New Relic docs lookup failed: {e}")
    return None


def fetch_sentry_docs(topic):
    """Fetch Sentry documentation."""
    try:
        resp = requests.get(f"https://docs.sentry.io/{topic.lower()}/", timeout=10)
        if resp.status_code == 200:
            return {"topic": topic, "url": resp.url}
    except Exception as e:
        logger.debug(f"Sentry docs lookup failed: {e}")
    return None


def fetch_openai_docs(api_method):
    """Fetch OpenAI API documentation."""
    try:
        resp = requests.get(f"https://platform.openai.com/docs/{api_method.lower()}", timeout=10)
        if resp.status_code == 200:
            return {"api": api_method, "url": resp.url}
    except Exception as e:
        logger.debug(f"OpenAI docs lookup failed: {e}")
    return None


def fetch_anthropic_docs(method):
    """Fetch Anthropic/Claude API documentation."""
    try:
        resp = requests.get(f"https://docs.anthropic.com/en/api/{method.lower()}", timeout=10)
        if resp.status_code == 200:
            return {"method": method, "url": resp.url}
    except Exception as e:
        logger.debug(f"Anthropic docs lookup failed: {e}")
    return None


def fetch_cohere_docs(model):
    """Fetch Cohere AI documentation."""
    try:
        resp = requests.get(f"https://docs.cohere.com/docs/{model.lower()}", timeout=10)
        if resp.status_code == 200:
            return {"model": model, "url": resp.url}
    except Exception as e:
        logger.debug(f"Cohere docs lookup failed: {e}")
    return None


def fetch_youtube_tutorials(query):
    """Fetch YouTube video tutorials."""
    try:
        api_key = os.getenv("YOUTUBE_API_KEY")
        if not api_key:
            return []
        resp = requests.get(
            "https://www.googleapis.com/youtube/v3/search",
            params={"q": query, "part": "snippet", "type": "video", "maxResults": 3, "key": api_key},
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            return [{"title": v["snippet"]["title"][:100], "videoId": v["id"]["videoId"]} for v in data.get("items", [])[:3]]
    except Exception as e:
        logger.debug(f"YouTube lookup failed for {query}: {e}")
    return []


def fetch_arxiv_papers(query):
    """Fetch arXiv papers."""
    try:
        resp = requests.get(
            "https://export.arxiv.org/api/query",
            params={"search_query": f"all:{query}", "max_results": 3},
            timeout=10,
        )
        if resp.status_code == 200:
            titles = re.findall(r"<title>([^<]+)</title>", resp.text)
            return [{"title": t.strip()[:100]} for t in titles[:3]]
    except Exception as e:
        logger.debug(f"arXiv lookup failed for {query}: {e}")
    return []


def fetch_devto_articles(query):
    """Fetch Dev.to articles."""
    try:
        resp = requests.get(f"https://dev.to/api/articles?tag={query}&per_page=3", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return [
                {"title": a["title"][:100], "public_reactions_count": a.get("public_reactions_count", 0)} for a in data[:3]
            ]
    except Exception as e:
        logger.debug(f"Dev.to lookup failed for {query}: {e}")
    return []


def fetch_npm_trends(package_name):
    """Fetch npm download trends."""
    try:
        resp = requests.get(f"https://api.npmjs.org/downloads/point/last-week/{package_name}", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return {"downloads": data.get("downloads", 0)}
    except Exception as e:
        logger.debug(f"npm trends lookup failed for {package_name}: {e}")
    return None


def fetch_pypi_downloads(package_name):
    """Fetch PyPI download stats."""
    try:
        resp = requests.get(f"https://pypistats.org/api/packages/{package_name}/recent", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("data", {})
    except Exception as e:
        logger.debug(f"PyPI stats lookup failed for {package_name}: {e}")
    return None


def fetch_snyk_vulns(package_name, ecosystem="pip"):
    """Fetch Snyk vulnerabilities."""
    try:
        api_key = os.getenv("SNYK_API_KEY")
        if not api_key:
            return []
        resp = requests.get(
            f"https://api.snyk.io/v1/provider/vulnerabilities/{ecosystem}/{package_name}",
            headers={"Authorization": f"token {api_key}"},
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            return data.get("vulnerabilities", [])[:3]
    except Exception as e:
        logger.debug(f"Snyk lookup failed for {package_name}: {e}")
    return []


def fetch_digitalocean_docs(service):
    """Fetch DigitalOcean documentation."""
    try:
        resp = requests.get(f"https://docs.digitalocean.com/reference/api/{service.lower()}-api/", timeout=10)
        if resp.status_code == 200:
            return {"service": service, "url": resp.url}
    except Exception as e:
        logger.debug(f"DigitalOcean docs lookup failed: {e}")
    return None


def fetch_linode_docs(service):
    """Fetch Linode documentation."""
    try:
        resp = requests.get(f"https://www.linode.com/docs/{service.lower()}/", timeout=10)
        if resp.status_code == 200:
            return {"service": service, "url": resp.url}
    except Exception as e:
        logger.debug(f"Linode docs lookup failed: {e}")
    return None


def fetch_fastly_docs(service):
    """Fetch Fastly documentation."""
    try:
        resp = requests.get(f"https://www.fastly.com/docs/{service.lower()}/", timeout=10)
        if resp.status_code == 200:
            return {"service": service, "url": resp.url}
    except Exception as e:
        logger.debug(f"Fastly docs lookup failed: {e}")
    return None


def fetch_auth0_docs(topic):
    """Fetch Auth0 documentation."""
    try:
        resp = requests.get(f"https://auth0.com/docs/{topic.lower()}", timeout=10)
        if resp.status_code == 200:
            return {"topic": topic, "url": resp.url}
    except Exception as e:
        logger.debug(f"Auth0 docs lookup failed: {e}")
    return None


def fetch_clerk_docs(topic):
    """Fetch Clerk documentation."""
    try:
        resp = requests.get(f"https://clerk.com/docs/{topic.lower()}", timeout=10)
        if resp.status_code == 200:
            return {"topic": topic, "url": resp.url}
    except Exception as e:
        logger.debug(f"Clerk docs lookup failed: {e}")
    return None


def fetch_supabase_docs(topic):
    """Fetch Supabase documentation."""
    try:
        resp = requests.get(f"https://supabase.com/docs/guides/{topic.lower()}", timeout=10)
        if resp.status_code == 200:
            return {"topic": topic, "url": resp.url}
    except Exception as e:
        logger.debug(f"Supabase docs lookup failed: {e}")
    return None


def fetch_cypress_docs(topic):
    """Fetch Cypress documentation."""
    try:
        resp = requests.get(f"https://docs.cypress.io/{topic.lower()}/", timeout=10)
        if resp.status_code == 200:
            return {"topic": topic, "url": resp.url}
    except Exception as e:
        logger.debug(f"Cypress docs lookup failed: {e}")
    return None


def fetch_playwright_docs(topic):
    """Fetch Playwright documentation."""
    try:
        resp = requests.get(f"https://playwright.dev/docs/{topic.lower()}", timeout=10)
        if resp.status_code == 200:
            return {"topic": topic, "url": resp.url}
    except Exception as e:
        logger.debug(f"Playwright docs lookup failed: {e}")
    return None


def fetch_vitest_docs(topic):
    """Fetch Vitest documentation."""
    try:
        resp = requests.get(f"https://vitest.dev/{topic.lower()}.html", timeout=10)
        if resp.status_code == 200:
            return {"topic": topic, "url": resp.url}
    except Exception as e:
        logger.debug(f"Vitest docs lookup failed: {e}")
    return None


def fetch_mysql_docs(topic):
    """Fetch MySQL documentation."""
    try:
        resp = requests.get(f"https://dev.mysql.com/doc/refman/8.0/en/{topic.lower()}.html", timeout=10)
        if resp.status_code == 200:
            return {"topic": topic, "url": resp.url}
    except Exception as e:
        logger.debug(f"MySQL docs lookup failed: {e}")
    return None


def fetch_elasticsearch_docs(topic):
    """Fetch Elasticsearch documentation."""
    try:
        resp = requests.get(f"https://www.elastic.co/guide/en/elasticsearch/reference/{topic.lower()}.html", timeout=10)
        if resp.status_code == 200:
            return {"topic": topic, "url": resp.url}
    except Exception as e:
        logger.debug(f"Elasticsearch docs lookup failed: {e}")
    return None


def fetch_algolia_docs(topic):
    """Fetch Algolia documentation."""
    try:
        resp = requests.get(f"https://www.algolia.com/doc/{topic.lower()}/", timeout=10)
        if resp.status_code == 200:
            return {"topic": topic, "url": resp.url}
    except Exception as e:
        logger.debug(f"Algolia docs lookup failed: {e}")
    return None


def fetch_meilisearch_docs(topic):
    """Fetch MeiliSearch documentation."""
    try:
        resp = requests.get(f"https://www.meilisearch.com/docs/{topic.lower()}", timeout=10)
        if resp.status_code == 200:
            return {"topic": topic, "url": resp.url}
    except Exception as e:
        logger.debug(f"MeiliSearch docs lookup failed: {e}")
    return None


def fetch_rabbitmq_docs(topic):
    """Fetch RabbitMQ documentation."""
    try:
        resp = requests.get(f"https://www.rabbitmq.com/{topic.lower()}.html", timeout=10)
        if resp.status_code == 200:
            return {"topic": topic, "url": resp.url}
    except Exception as e:
        logger.debug(f"RabbitMQ docs lookup failed: {e}")
    return None


def fetch_kafka_docs(topic):
    """Fetch Apache Kafka documentation."""
    try:
        resp = requests.get(f"https://kafka.apache.org/documentation/#{topic.lower()}", timeout=10)
        if resp.status_code == 200:
            return {"topic": topic, "url": resp.url}
    except Exception as e:
        logger.debug(f"Kafka docs lookup failed: {e}")
    return None


def fetch_pulsar_docs(topic):
    """Fetch Apache Pulsar documentation."""
    try:
        resp = requests.get(f"https://pulsar.apache.org/docs/{topic.lower()}/", timeout=10)
        if resp.status_code == 200:
            return {"topic": topic, "url": resp.url}
    except Exception as e:
        logger.debug(f"Pulsar docs lookup failed: {e}")
    return None


def fetch_grpc_docs(topic):
    """Fetch gRPC documentation."""
    try:
        resp = requests.get(f"https://grpc.io/docs/{topic.lower()}/", timeout=10)
        if resp.status_code == 200:
            return {"topic": topic, "url": resp.url}
    except Exception as e:
        logger.debug(f"gRPC docs lookup failed: {e}")
    return None


def fetch_circleci_docs(topic):
    """Fetch CircleCI documentation."""
    try:
        resp = requests.get(f"https://circleci.com/docs/{topic.lower()}/", timeout=10)
        if resp.status_code == 200:
            return {"topic": topic, "url": resp.url}
    except Exception as e:
        logger.debug(f"CircleCI docs lookup failed: {e}")
    return None


def fetch_githubactions_docs(action):
    """Fetch GitHub Actions documentation."""
    try:
        resp = requests.get(f"https://github.com/{action.lower()}/actions", timeout=10)
        if resp.status_code == 200:
            return {"action": action, "url": resp.url}
    except Exception as e:
        logger.debug(f"GitHub Actions lookup failed: {e}")
    return None


def fetch_prometheus_docs(topic):
    """Fetch Prometheus documentation."""
    try:
        resp = requests.get(f"https://prometheus.io/docs/{topic.lower()}/", timeout=10)
        if resp.status_code == 200:
            return {"topic": topic, "url": resp.url}
    except Exception as e:
        logger.debug(f"Prometheus docs lookup failed: {e}")
    return None


def fetch_grafana_docs(topic):
    """Fetch Grafana documentation."""
    try:
        resp = requests.get(f"https://grafana.com/docs/grafana/latest/{topic.lower()}/", timeout=10)
        if resp.status_code == 200:
            return {"topic": topic, "url": resp.url}
    except Exception as e:
        logger.debug(f"Grafana docs lookup failed: {e}")
    return None


def fetch_stripe_docs(resource):
    """Fetch Stripe documentation."""
    try:
        resp = requests.get(f"https://stripe.com/docs/api/{resource.lower()}", timeout=10)
        if resp.status_code == 200:
            return {"resource": resource, "url": resp.url}
    except Exception as e:
        logger.debug(f"Stripe docs lookup failed: {e}")
    return None


def fetch_paypal_docs(resource):
    """Fetch PayPal documentation."""
    try:
        resp = requests.get(f"https://developer.paypal.com/docs/api/{resource.lower()}/", timeout=10)
        if resp.status_code == 200:
            return {"resource": resource, "url": resp.url}
    except Exception as e:
        logger.debug(f"PayPal docs lookup failed: {e}")
    return None


def fetch_braintree_docs(resource):
    """Fetch Braintree documentation."""
    try:
        resp = requests.get(f"https://developer.paypal.com/braintree/docs/reference/{resource.lower()}", timeout=10)
        if resp.status_code == 200:
            return {"resource": resource, "url": resp.url}
    except Exception as e:
        logger.debug(f"Braintree docs lookup failed: {e}")
    return None


def fetch_sendgrid_docs(resource):
    """Fetch SendGrid documentation."""
    try:
        resp = requests.get(f"https://sendgrid.com/docs/{resource.lower()}/", timeout=10)
        if resp.status_code == 200:
            return {"resource": resource, "url": resp.url}
    except Exception as e:
        logger.debug(f"SendGrid docs lookup failed: {e}")
    return None


def fetch_mailgun_docs(resource):
    """Fetch Mailgun documentation."""
    try:
        resp = requests.get(f"https://documentation.mailgun.com/en/latest/{resource.lower()}/", timeout=10)
        if resp.status_code == 200:
            return {"resource": resource, "url": resp.url}
    except Exception as e:
        logger.debug(f"Mailgun docs lookup failed: {e}")
    return None


def fetch_ses_docs(resource):
    """Fetch AWS SES documentation."""
    try:
        resp = requests.get(f"https://docs.aws.amazon.com/ses/latest/dg/{resource.lower()}.html", timeout=10)
        if resp.status_code == 200:
            return {"resource": resource, "url": resp.url}
    except Exception as e:
        logger.debug(f"AWS SES docs lookup failed: {e}")
    return None


def fetch_ansible_docs(module):
    """Fetch Ansible documentation."""
    try:
        resp = requests.get(f"https://docs.ansible.com/ansible/latest/{module.lower()}_module.html", timeout=10)
        if resp.status_code == 200:
            return {"module": module, "url": resp.url}
    except Exception as e:
        logger.debug(f"Ansible docs lookup failed: {e}")
    return None


def fetch_puppet_docs(resource):
    """Fetch Puppet documentation."""
    try:
        resp = requests.get(f"https://puppet.com/docs/{resource.lower()}/", timeout=10)
        if resp.status_code == 200:
            return {"resource": resource, "url": resp.url}
    except Exception as e:
        logger.debug(f"Puppet docs lookup failed: {e}")
    return None


def fetch_packer_docs(topic):
    """Fetch Packer documentation."""
    try:
        resp = requests.get(f"https:// developer.hashicorp.com/packer/docs/{topic.lower()}/", timeout=10)
        if resp.status_code == 200:
            return {"topic": topic, "url": resp.url}
    except Exception as e:
        logger.debug(f"Packer docs lookup failed: {e}")
    return None


def fetch_vagrant_docs(topic):
    """Fetch Vagrant documentation."""
    try:
        resp = requests.get(f"https://developer.hashicorp.com/vagrant/docs/{topic.lower()}/", timeout=10)
        if resp.status_code == 200:
            return {"topic": topic, "url": resp.url}
    except Exception as e:
        logger.debug(f"Vagrant docs lookup failed: {e}")
    return None


def fetch_firebase_functions_docs(function):
    """Fetch Firebase Cloud Functions documentation."""
    try:
        resp = requests.get(f"https://firebase.google.com/docs/functions/{function.lower()}", timeout=10)
        if resp.status_code == 200:
            return {"function": function, "url": resp.url}
    except Exception as e:
        logger.debug(f"Firebase docs lookup failed: {e}")
    return None


def fetch_langchain_docs(topic):
    """Fetch LangChain documentation."""
    try:
        resp = requests.get(f"https://python.langchain.com/docs/{topic.lower()}/", timeout=10)
        if resp.status_code == 200:
            return {"topic": topic, "url": resp.url}
    except Exception as e:
        logger.debug(f"LangChain docs lookup failed: {e}")
    return None


def fetch_gitbook_docs(query):
    """Fetch GitBook documentation."""
    try:
        resp = requests.get(
            "https://api.gitbook.com/v1/search",
            params={"q": query, "limit": 3},
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            return [{"title": r.get("title", ""), "url": r.get("url", "")} for r in data.get("results", [])[:3]]
    except Exception as e:
        logger.debug(f"GitBook lookup failed for {query}: {e}")
    return []


def extract_dependencies(files_changed):
    """Extract package names from changed files."""
    pypi_packages = set()
    npm_packages = set()
    crates_packages = set()
    go_modules = set()
    docker_images = set()
    aws_services = set()
    azure_services = set()
    gcp_services = set()
    apt_packages = set()
    brew_packages = set()
    conda_packages = set()
    nuget_packages = set()
    maven_packages = set()
    pub_packages = set()
    helm_charts = set()
    terraform_modules = set()

    for filepath in files_changed:
        filepath_lower = filepath.lower()
        name = filepath.split("/")[-1]

        if filepath_lower.endswith(".py"):
            pypi_packages.add(name.replace(".py", ""))
        elif filepath_lower.endswith(("js", "ts", "jsx", "tsx")):
            npm_packages.add(name.replace(".js", "").replace(".ts", ""))
        elif filepath_lower.endswith("rs"):
            crates_packages.add(name.replace(".rs", ""))
        elif filepath_lower.endswith(".go"):
            go_modules.add(name.replace(".go", ""))
        elif "dockerfile" in filepath_lower or filepath_lower == "dockerfile":
            docker_images.add("library/" + name.replace("dockerfile", ""))
        elif name in ("package.json", "package-lock.json"):
            npm_packages.add("node")
        elif name in ("requirements.txt", "pyproject.toml", "setup.py"):
            pypi_packages.add("project")
        elif name == "cargo.toml":
            crates_packages.add("project")
        elif name == "go.mod":
            go_modules.add("project")
        elif name.endswith(".tf"):
            terraform_modules.add(name.replace(".tf", ""))
        elif name == "pubspec.yaml":
            pub_packages.add("project")
        elif name == "Cartfile" or name == "Cartfile.resolved":
            nuget_packages.add("project")
        elif name in ("build.gradle", "pom.xml"):
            maven_packages.add("project")
        elif name.endswith(".yaml") or name.endswith(".yml"):
            pass
        elif name.endswith(".json"):
            pass

    return {
        "pypi": list(pypi_packages),
        "npm": list(npm_packages),
        "crates": list(crates_packages),
        "go": list(go_modules),
        "docker": list(docker_images),
        "aws": list(aws_services),
        "azure": list(azure_services),
        "gcp": list(gcp_services),
        "apt": list(apt_packages),
        "brew": list(brew_packages),
        "conda": list(conda_packages),
        "nuget": list(nuget_packages),
        "maven": list(maven_packages),
        "pub": list(pub_packages),
        "helm": list(helm_charts),
        "terraform": list(terraform_modules),
    }


def fetch_rag_context(pr_details, config):
    """Fetch relevant context using RAG."""
    if not config.get("enable_rag", False):
        return ""

    # Handle both string and list formats for rag_sources
    sources_raw = config.get("rag_sources", "")
    if isinstance(sources_raw, list):
        sources = sources_raw
    else:
        sources = sources_raw.split() if sources_raw else []
    max_items = config.get("rag_max_items", 5)
    files_changed = pr_details.get("files_changed", [])
    dependencies = extract_dependencies(files_changed)
    repo_name = pr_details.get("repo_name", "")
    github_token = config.get("rag_github_token", "") or os.getenv("GITHUB_TOKEN")

    context_parts = []
    context_month = datetime.now(timezone.utc).strftime("%B %Y")
    context_parts.append(f"## Current Context ({context_month})")
    context_parts.append("")

    if "pypi" in sources:
        for pkg in dependencies.get("pypi", [])[:max_items]:
            info = fetch_pypi_package_info(pkg)
            if info:
                context_parts.append(f"**PyPI: {info['name']}** v{info['version']}")
                if info.get("summary"):
                    context_parts.append(f"- {info['summary']}")
                context_parts.append("")

    if "npm" in sources:
        for pkg in dependencies.get("npm", [])[:max_items]:
            info = fetch_npm_package_info(pkg)
            if info:
                context_parts.append(f"**npm: {info['name']}** v{info['version']}")
                if info.get("description"):
                    context_parts.append(f"- {info['description']}")
                context_parts.append("")

    if "security" in sources:
        for pkg in dependencies.get("pypi", [])[:2]:
            advisories = fetch_security_advisories("pip", pkg)
            if advisories:
                context_parts.append(f"**Security: {pkg}**")
                for a in advisories:
                    context_parts.append(f"- [{a['severity']}] {a['summary']}")
                context_parts.append("")

    if "github" in sources and repo_name and github_token:
        recent = fetch_github_recent_changes(repo_name, files_changed, github_token)
        if recent:
            context_parts.append("**Recent Changes**")
            for change in recent[:max_items]:
                context_parts.append(f"- `{change['file']}`: {change['message']} ({change['date']})")
            context_parts.append("")

    if "docs" in sources:
        for pkg in dependencies.get("pypi", [])[:3]:
            doc_info = fetch_docs_search(f"{pkg} python library 2025 2026")
            if doc_info:
                context_parts.append(f"**Docs: {doc_info['title']}**")
                context_parts.append(f"- {doc_info['content']}")
                context_parts.append("")

    if "stackoverflow" in sources:
        for pkg in dependencies.get("pypi", [])[:2]:
            so_answers = fetch_stackoverflow_answers(pkg, [pkg, "python"])
            if so_answers:
                context_parts.append(f"**StackOverflow: {pkg}**")
                for ans in so_answers[:2]:
                    status = "✓" if ans["is_answered"] else ""
                    context_parts.append(f"- {status} {ans['title']} (score: {ans['score']})")
                context_parts.append("")

    if "news" in sources:
        news = fetch_tech_news()
        if news:
            context_parts.append("**Tech News (Recent)**")
            for n in news[:3]:
                context_parts.append(f"- {n['title']} ({n['source']})")
            context_parts.append("")

    if "weather" in sources:
        weather_location = os.getenv("WEATHER_LOCATION", "San Francisco")
        weather = fetch_weather(weather_location)
        if weather:
            context_parts.append(f"**Weather: {weather['location']}**")
            context_parts.append(f"- {weather['temp']}°C, {weather['description']}, humidity: {weather['humidity']}%")
            context_parts.append("")

    if "reddit" in sources:
        for pkg in dependencies.get("pypi", [])[:2]:
            reddit_posts = fetch_reddit_discussions(pkg)
            if reddit_posts:
                context_parts.append(f"**Reddit: r/{reddit_posts[0]['subreddit']}**")
                for post in reddit_posts[:2]:
                    context_parts.append(f"- {post['title']} (score: {post['score']})")
                context_parts.append("")

    if "hackernews" in sources:
        for pkg in dependencies.get("pypi", [])[:2]:
            hn_links = fetch_hackernews(pkg)
            if hn_links:
                context_parts.append(f"**HackerNews: {pkg}**")
                for h in hn_links[:2]:
                    context_parts.append(f"- {h['title']} (points: {h['points']})")
                context_parts.append("")

    if "crates" in sources:
        for crate in dependencies.get("crates", [])[:3]:
            info = fetch_crates_info(crate)
            if info:
                context_parts.append(f"**crates.io: {info['name']}** v{info['version']}")
                if info.get("description"):
                    context_parts.append(f"- {info['description']}")
                context_parts.append("")

    if "go" in sources:
        for mod in dependencies.get("go", [])[:3]:
            info = fetch_go_info(mod)
            if info:
                context_parts.append(f"**Go: {info['module']}**")
                context_parts.append("")

    if "dockerhub" in sources:
        for img in dependencies.get("docker", [])[:3]:
            info = fetch_docker_image(img)
            if info:
                context_parts.append(f"**Docker: {info['image']}**")
                context_parts.append(f"- latest: {info.get('latest', 'N/A')}")
                context_parts.append("")

    if "web_search" in sources:
        for pkg in dependencies.get("pypi", [])[:3]:
            results = fetch_web_search(f"{pkg} python library changelog 2025 2026")
            if results:
                context_parts.append(f"**Web: {pkg}**")
                for r in results[:2]:
                    context_parts.append(f"- {r['title']}")
                context_parts.append("")

    if "youtube" in sources:
        for pkg in dependencies.get("pypi", [])[:2]:
            videos = fetch_youtube_tutorials(f"{pkg} python tutorial")
            if videos:
                context_parts.append(f"**YouTube: {pkg}**")
                for v in videos[:2]:
                    context_parts.append(f"- {v['title']}")
                context_parts.append("")

    if "arxiv" in sources:
        for pkg in dependencies.get("pypi", [])[:2]:
            papers = fetch_arxiv_papers(pkg)
            if papers:
                context_parts.append(f"**arXiv: {pkg}**")
                for p in papers[:2]:
                    context_parts.append(f"- {p['title']}")
                context_parts.append("")

    if "devto" in sources:
        for pkg in dependencies.get("pypi", [])[:2]:
            articles = fetch_devto_articles(pkg)
            if articles:
                context_parts.append(f"**Dev.to: {pkg}**")
                for a in articles[:2]:
                    context_parts.append(f"- {a['title']} (reactions: {a.get('public_reactions_count', 0)})")
                context_parts.append("")

    if "npm_trends" in sources:
        for pkg in dependencies.get("npm", [])[:3]:
            trends = fetch_npm_trends(pkg)
            if trends:
                context_parts.append(f"**npm Trends: {pkg}**")
                context_parts.append(f"- downloads (last week): {trends.get('downloads', 'N/A')}")
                context_parts.append("")

    if "pypi_downloads" in sources:
        for pkg in dependencies.get("pypi", [])[:3]:
            stats = fetch_pypi_downloads(pkg)
            if stats:
                context_parts.append(f"**PyPI Stats: {pkg}**")
                context_parts.append("")

    if "snyk" in sources:
        for pkg in dependencies.get("pypi", [])[:2]:
            vulns = fetch_snyk_vulns(pkg)
            if vulns:
                context_parts.append(f"**Snyk: {pkg}**")
                context_parts.append(f"- {len(vulns)} vulnerabilities found")
                context_parts.append("")

    if "gitbook" in sources:
        for pkg in dependencies.get("pypi", [])[:2]:
            docs = fetch_gitbook_docs(pkg)
            if docs:
                context_parts.append(f"**GitBook: {pkg}**")
                for d in docs[:2]:
                    context_parts.append(f"- {d['title']}")
                context_parts.append("")

    if "aws_docs" in sources:
        for svc in dependencies.get("aws", [])[:2]:
            docs = fetch_aws_docs(svc)
            if docs:
                context_parts.append(f"**AWS Docs: {docs['service']}**")
                context_parts.append(f"- {docs.get('url', '')}")
                context_parts.append("")

    if "azure_docs" in sources:
        for svc in dependencies.get("azure", [])[:2]:
            docs = fetch_azure_docs(svc)
            if docs:
                context_parts.append(f"**Azure Docs: {docs['service']}**")
                context_parts.append(f"- {docs.get('url', '')}")
                context_parts.append("")

    if "gcp_docs" in sources:
        for svc in dependencies.get("gcp", [])[:2]:
            docs = fetch_gcp_docs(svc)
            if docs:
                context_parts.append(f"**GCP Docs: {docs['service']}**")
                context_parts.append(f"- {docs.get('url', '')}")
                context_parts.append("")

    if "apt" in sources:
        for pkg in dependencies.get("apt", [])[:3]:
            info = fetch_apt_package_info(pkg)
            if info:
                context_parts.append(f"**APT: {info['package']}**")
                context_parts.append("")

    if "brew" in sources:
        for pkg in dependencies.get("brew", [])[:3]:
            info = fetch_brew_info(pkg)
            if info:
                context_parts.append(f"**Homebrew: {info['name']}**")
                if info.get("desc"):
                    context_parts.append(f"- {info['desc']}")
                context_parts.append("")

    if "conda" in sources:
        for pkg in dependencies.get("conda", [])[:3]:
            info = fetch_conda_info(pkg)
            if info:
                context_parts.append(f"**Conda: {info['name']}**")
                context_parts.append("")

    if "nuget" in sources:
        for pkg in dependencies.get("nuget", [])[:3]:
            info = fetch_nuget_info(pkg)
            if info:
                context_parts.append(f"**NuGet: {info['name']}**")
                context_parts.append("")

    if "maven" in sources:
        for pkg in dependencies.get("maven", [])[:2]:
            parts = pkg.split(":")
            if len(parts) == 2:
                info = fetch_maven_info(parts[0], parts[1])
                if info:
                    context_parts.append(f"**Maven: {info['group']}:{info['artifact']}** v{info.get('version', '')}")
                    context_parts.append("")

    if "pub" in sources:
        for pkg in dependencies.get("pub", [])[:3]:
            info = fetch_pub_info(pkg)
            if info:
                context_parts.append(f"**pub.dev: {info['name']}** v{info.get('version', '')}")
                context_parts.append("")

    if "helm" in sources:
        for chart in dependencies.get("helm", [])[:3]:
            info = fetch_helm_chart_info(chart)
            if info:
                context_parts.append(f"**Helm: {info['name']}** v{info.get('version', '')}")
                context_parts.append("")

    if "terraform_registry" in sources:
        for mod in dependencies.get("terraform", [])[:2]:
            info = fetch_terraform_module_info(mod)
            if info:
                context_parts.append(f"**Terraform: {info['name']}**")
                context_parts.append("")

    if "huggingface" in sources:
        for pkg in dependencies.get("pypi", [])[:2]:
            models = fetch_huggingface_models(pkg)
            if models:
                context_parts.append(f"**HuggingFace: {pkg}**")
                for m in models[:2]:
                    context_parts.append(f"- {m['name']} ({m['downloads']} downloads)")
                context_parts.append("")

    if "kaggle" in sources:
        for pkg in dependencies.get("pypi", [])[:2]:
            datasets = fetch_kaggle_datasets(pkg)
            if datasets:
                context_parts.append(f"**Kaggle: {pkg}**")
                for d in datasets[:2]:
                    context_parts.append(f"- {d.get('title', '')}")
                context_parts.append("")

    if "medium" in sources:
        for pkg in dependencies.get("pypi", [])[:2]:
            articles = fetch_medium_articles(pkg)
            if articles:
                context_parts.append(f"**Medium: {pkg}**")
                for a in articles[:2]:
                    context_parts.append(f"- {a['title']}")
                context_parts.append("")

    if "producthunt" in sources:
        for pkg in dependencies.get("pypi", [])[:2]:
            products = fetch_producthunt(pkg)
            if products:
                context_parts.append(f"**ProductHunt: {pkg}**")
                for p in products[:2]:
                    context_parts.append(f"- {p['name']}: {p['tagline']}")
                context_parts.append("")

    if "gitbook" in sources:
        for pkg in dependencies.get("pypi", [])[:2]:
            docs = fetch_gitbook_docs(pkg)
            if docs:
                context_parts.append(f"**GitBook: {pkg}**")
                for d in docs[:2]:
                    context_parts.append(f"- {d['title']}")
                context_parts.append("")

    if "confluence" in sources:
        for pkg in dependencies.get("pypi", [])[:2]:
            pages = fetch_confluence_pages(pkg)
            if pages:
                context_parts.append(f"**Confluence: {pkg}**")
                for p in pages[:2]:
                    context_parts.append(f"- {p['title']}")
                context_parts.append("")

    if "cocoapods" in sources:
        for pod in dependencies.get("cocoapods", [])[:3]:
            info = fetch_cocoapods_info(pod)
            if info:
                context_parts.append(f"**CocoaPods: {info['name']}** v{info.get('version', '')}")
                context_parts.append("")

    if "packagist" in sources:
        for pkg in dependencies.get("packagist", [])[:3]:
            info = fetch_packagist_info(pkg)
            if info:
                context_parts.append(f"**Packagist: {info['name']}** v{info.get('version', '')}")
                context_parts.append("")

    if "rubygems" in sources:
        for gem in dependencies.get("rubygems", [])[:3]:
            info = fetch_rubygems_info(gem)
            if info:
                context_parts.append(f"**RubyGems: {info['name']}** v{info.get('version', '')}")
                context_parts.append("")

    if "cloudflare" in sources:
        for svc in dependencies.get("cloudflare", [])[:2]:
            docs = fetch_cloudflare_docs(svc)
            if docs:
                context_parts.append(f"**Cloudflare Docs: {docs['service']}**")
                context_parts.append(f"- {docs.get('url', '')}")
                context_parts.append("")

    if "vercel" in sources:
        for svc in dependencies.get("vercel", [])[:2]:
            docs = fetch_vercel_docs(svc)
            if docs:
                context_parts.append(f"**Vercel Docs: {docs['service']}**")
                context_parts.append(f"- {docs.get('url', '')}")
                context_parts.append("")

    if "heroku" in sources:
        for svc in dependencies.get("heroku", [])[:2]:
            docs = fetch_heroku_docs(svc)
            if docs:
                context_parts.append(f"**Heroku Docs: {docs['service']}**")
                context_parts.append(f"- {docs.get('url', '')}")
                context_parts.append("")

    if "slack" in sources:
        for pkg in dependencies.get("pypi", [])[:2]:
            docs = fetch_slack_docs(pkg)
            if docs:
                context_parts.append(f"**Slack API: {docs['method']}**")
                context_parts.append(f"- {docs.get('url', '')}")
                context_parts.append("")

    if "discord" in sources:
        for pkg in dependencies.get("pypi", [])[:2]:
            docs = fetch_discord_docs(pkg)
            if docs:
                context_parts.append(f"**Discord: {docs['resource']}**")
                context_parts.append(f"- {docs.get('url', '')}")
                context_parts.append("")

    if "telegram" in sources:
        for pkg in dependencies.get("pypi", [])[:2]:
            docs = fetch_telegram_docs(pkg)
            if docs:
                context_parts.append(f"**Telegram Bot API: {docs['method']}**")
                context_parts.append(f"- {docs.get('url', '')}")
                context_parts.append("")

    if "jest" in sources:
        docs = fetch_jest_docs("expect")
        if docs:
            context_parts.append("**Jest Docs**")
            context_parts.append(f"- {docs.get('url', '')}")
            context_parts.append("")

    if "pytest" in sources:
        docs = fetch_pytest_docs("api-reference")
        if docs:
            context_parts.append("**Pytest Docs**")
            context_parts.append(f"- {docs.get('url', '')}")
            context_parts.append("")

    if "rspec" in sources:
        docs = fetch_rspec_docs("rspec-expectations")
        if docs:
            context_parts.append("**RSpec Docs**")
            context_parts.append(f"- {docs.get('url', '')}")
            context_parts.append("")

    if "sonarcloud" in sources:
        for proj in dependencies.get("sonarcloud", [])[:2]:
            issues = fetch_sonarcloud_issues(proj)
            if issues:
                context_parts.append(f"**SonarCloud: {proj}**")
                context_parts.append(f"- {len(issues)} issues found")
                context_parts.append("")

    if "postgresql" in sources:
        docs = fetch_postgresql_docs("reference")
        if docs:
            context_parts.append("**PostgreSQL Docs**")
            context_parts.append(f"- {docs.get('url', '')}")
            context_parts.append("")

    if "mongodb" in sources:
        docs = fetch_mongodb_docs("drivers")
        if docs:
            context_parts.append("**MongoDB Docs**")
            context_parts.append(f"- {docs.get('url', '')}")
            context_parts.append("")

    if "redis" in sources:
        docs = fetch_redis_docs("commands")
        if docs:
            context_parts.append("**Redis Docs**")
            context_parts.append(f"- {docs.get('url', '')}")
            context_parts.append("")

    if "prisma" in sources:
        docs = fetch_prisma_docs("getting-started")
        if docs:
            context_parts.append("**Prisma Docs**")
            context_parts.append(f"- {docs.get('url', '')}")
            context_parts.append("")

    if "swagger" in sources:
        docs = fetch_swagger_docs("openapi")
        if docs:
            context_parts.append("**OpenAPI/Swagger Docs**")
            context_parts.append(f"- {docs.get('url', '')}")
            context_parts.append("")

    if "graphql" in sources:
        docs = fetch_graphql_docs("schema")
        if docs:
            context_parts.append("**GraphQL Docs**")
            context_parts.append(f"- {docs.get('url', '')}")
            context_parts.append("")

    if "github_actions" in sources:
        docs = fetch_github_actions_docs("using-workflows")
        if docs:
            context_parts.append("**GitHub Actions Docs**")
            context_parts.append(f"- {docs.get('url', '')}")
            context_parts.append("")

    if "gitlab_ci" in sources:
        docs = fetch_gitlab_ci_docs("quick-start")
        if docs:
            context_parts.append("**GitLab CI Docs**")
            context_parts.append(f"- {docs.get('url', '')}")
            context_parts.append("")

    if "jenkins" in sources:
        docs = fetch_jenkins_docs("tutorial")
        if docs:
            context_parts.append("**Jenkins Docs**")
            context_parts.append(f"- {docs.get('url', '')}")
            context_parts.append("")

    if "datadog" in sources:
        docs = fetch_datadog_docs("getting_started")
        if docs:
            context_parts.append("**Datadog Docs**")
            context_parts.append(f"- {docs.get('url', '')}")
            context_parts.append("")

    if "newrelic" in sources:
        docs = fetch_newrelic_docs("intro-to-new-relic")
        if docs:
            context_parts.append("**New Relic Docs**")
            context_parts.append(f"- {docs.get('url', '')}")
            context_parts.append("")

    if "sentry" in sources:
        docs = fetch_sentry_docs("platforms")
        if docs:
            context_parts.append("**Sentry Docs**")
            context_parts.append(f"- {docs.get('url', '')}")
            context_parts.append("")

    if "openai" in sources:
        docs = fetch_openai_docs("api-reference")
        if docs:
            context_parts.append("**OpenAI Docs**")
            context_parts.append(f"- {docs.get('url', '')}")
            context_parts.append("")

    if "anthropic" in sources:
        docs = fetch_anthropic_docs("claude-api")
        if docs:
            context_parts.append("**Anthropic/Claude Docs**")
            context_parts.append(f"- {docs.get('url', '')}")
            context_parts.append("")

    if "cohere" in sources:
        docs = fetch_cohere_docs("models")
        if docs:
            context_parts.append("**Cohere Docs**")
            context_parts.append(f"- {docs.get('url', '')}")
            context_parts.append("")

    if "digitalocean" in sources:
        docs = fetch_digitalocean_docs("compute")
        if docs:
            context_parts.append("**DigitalOcean Docs**")
            context_parts.append(f"- {docs.get('url', '')}")
            context_parts.append("")

    if "linode" in sources:
        docs = fetch_linode_docs("getting-started")
        if docs:
            context_parts.append("**Linode Docs**")
            context_parts.append(f"- {docs.get('url', '')}")
            context_parts.append("")

    if "fastly" in sources:
        docs = fetch_fastly_docs("guides")
        if docs:
            context_parts.append("**Fastly Docs**")
            context_parts.append(f"- {docs.get('url', '')}")
            context_parts.append("")

    if "auth0" in sources:
        docs = fetch_auth0_docs("getting-started")
        if docs:
            context_parts.append("**Auth0 Docs**")
            context_parts.append(f"- {docs.get('url', '')}")
            context_parts.append("")

    if "clerk" in sources:
        docs = fetch_clerk_docs("quickstart")
        if docs:
            context_parts.append("**Clerk Docs**")
            context_parts.append(f"- {docs.get('url', '')}")
            context_parts.append("")

    if "supabase" in sources:
        docs = fetch_supabase_docs("getting-started")
        if docs:
            context_parts.append("**Supabase Docs**")
            context_parts.append(f"- {docs.get('url', '')}")
            context_parts.append("")

    if "cypress" in sources:
        docs = fetch_cypress_docs("getting-started")
        if docs:
            context_parts.append("**Cypress Docs**")
            context_parts.append(f"- {docs.get('url', '')}")
            context_parts.append("")

    if "playwright" in sources:
        docs = fetch_playwright_docs("intro")
        if docs:
            context_parts.append("**Playwright Docs**")
            context_parts.append(f"- {docs.get('url', '')}")
            context_parts.append("")

    if "vitest" in sources:
        docs = fetch_vitest_docs("guide")
        if docs:
            context_parts.append("**Vitest Docs**")
            context_parts.append(f"- {docs.get('url', '')}")
            context_parts.append("")

    if "mysql" in sources:
        docs = fetch_mysql_docs("reference")
        if docs:
            context_parts.append("**MySQL Docs**")
            context_parts.append(f"- {docs.get('url', '')}")
            context_parts.append("")

    if "elasticsearch" in sources:
        docs = fetch_elasticsearch_docs("intro")
        if docs:
            context_parts.append("**Elasticsearch Docs**")
            context_parts.append(f"- {docs.get('url', '')}")
            context_parts.append("")

    if "algolia" in sources:
        docs = fetch_algolia_docs("getting-started")
        if docs:
            context_parts.append("**Algolia Docs**")
            context_parts.append(f"- {docs.get('url', '')}")
            context_parts.append("")

    if "meilisearch" in sources:
        docs = fetch_meilisearch_docs("getting-started")
        if docs:
            context_parts.append("**MeiliSearch Docs**")
            context_parts.append(f"- {docs.get('url', '')}")
            context_parts.append("")

    if "rabbitmq" in sources:
        docs = fetch_rabbitmq_docs("tutorials")
        if docs:
            context_parts.append("**RabbitMQ Docs**")
            context_parts.append(f"- {docs.get('url', '')}")
            context_parts.append("")

    if "kafka" in sources:
        docs = fetch_kafka_docs("intro")
        if docs:
            context_parts.append("**Kafka Docs**")
            context_parts.append(f"- {docs.get('url', '')}")
            context_parts.append("")

    if "pulsar" in sources:
        docs = fetch_pulsar_docs("getting-started")
        if docs:
            context_parts.append("**Pulsar Docs**")
            context_parts.append(f"- {docs.get('url', '')}")
            context_parts.append("")

    if "grpc" in sources:
        docs = fetch_grpc_docs("tutorials")
        if docs:
            context_parts.append("**gRPC Docs**")
            context_parts.append(f"- {docs.get('url', '')}")
            context_parts.append("")

    if "circleci" in sources:
        docs = fetch_circleci_docs("getting-started")
        if docs:
            context_parts.append("**CircleCI Docs**")
            context_parts.append(f"- {docs.get('url', '')}")
            context_parts.append("")

    if "actions" in sources:
        docs = fetch_githubactions_docs("popular")
        if docs:
            context_parts.append("**GitHub Actions**")
            context_parts.append(f"- {docs.get('url', '')}")
            context_parts.append("")

    if "prometheus" in sources:
        docs = fetch_prometheus_docs("getting-started")
        if docs:
            context_parts.append("**Prometheus Docs**")
            context_parts.append(f"- {docs.get('url', '')}")
            context_parts.append("")

    if "grafana" in sources:
        docs = fetch_grafana_docs("getting-started")
        if docs:
            context_parts.append("**Grafana Docs**")
            context_parts.append(f"- {docs.get('url', '')}")
            context_parts.append("")

    if "stripe" in sources:
        docs = fetch_stripe_docs("charges")
        if docs:
            context_parts.append("**Stripe Docs**")
            context_parts.append(f"- {docs.get('url', '')}")
            context_parts.append("")

    if "paypal" in sources:
        docs = fetch_paypal_docs("orders")
        if docs:
            context_parts.append("**PayPal Docs**")
            context_parts.append(f"- {docs.get('url', '')}")
            context_parts.append("")

    if "braintree" in sources:
        docs = fetch_braintree_docs("overview")
        if docs:
            context_parts.append("**Braintree Docs**")
            context_parts.append(f"- {docs.get('url', '')}")
            context_parts.append("")

    if "sendgrid" in sources:
        docs = fetch_sendgrid_docs("api-reference")
        if docs:
            context_parts.append("**SendGrid Docs**")
            context_parts.append(f"- {docs.get('url', '')}")
            context_parts.append("")

    if "mailgun" in sources:
        docs = fetch_mailgun_docs("api-reference")
        if docs:
            context_parts.append("**Mailgun Docs**")
            context_parts.append(f"- {docs.get('url', '')}")
            context_parts.append("")

    if "ses" in sources:
        docs = fetch_ses_docs("sending-authorization")
        if docs:
            context_parts.append("**AWS SES Docs**")
            context_parts.append(f"- {docs.get('url', '')}")
            context_parts.append("")

    if "ansible" in sources:
        docs = fetch_ansible_docs("package")
        if docs:
            context_parts.append("**Ansible Docs**")
            context_parts.append(f"- {docs.get('url', '')}")
            context_parts.append("")

    if "puppet" in sources:
        docs = fetch_puppet_docs("learning")
        if docs:
            context_parts.append("**Puppet Docs**")
            context_parts.append(f"- {docs.get('url', '')}")
            context_parts.append("")

    if "packer" in sources:
        docs = fetch_packer_docs("intro")
        if docs:
            context_parts.append("**Packer Docs**")
            context_parts.append(f"- {docs.get('url', '')}")
            context_parts.append("")

    if "vagrant" in sources:
        docs = fetch_vagrant_docs("getting-started")
        if docs:
            context_parts.append("**Vagrant Docs**")
            context_parts.append(f"- {docs.get('url', '')}")
            context_parts.append("")

    if "firebase_functions" in sources:
        docs = fetch_firebase_functions_docs("write")
        if docs:
            context_parts.append("**Firebase Functions Docs**")
            context_parts.append(f"- {docs.get('url', '')}")
            context_parts.append("")

    if "langchain" in sources:
        docs = fetch_langchain_docs("getting-started")
        if docs:
            context_parts.append("**LangChain Docs**")
            context_parts.append(f"- {docs.get('url', '')}")
            context_parts.append("")

    if len(context_parts) <= 2:
        return ""

    return "\n".join(context_parts)
