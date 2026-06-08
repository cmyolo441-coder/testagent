#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║                  ADVANCED WEB SCANNER v3.0                        ║
║          Multi-Module Security Assessment Toolkit                 ║
╚══════════════════════════════════════════════════════════════════╝

Features:
  - Port scanning (TCP)
  - Directory & file brute-forcing
  - HTTP header analysis & security checks
  - SSL/TLS certificate inspection
  - Subdomain enumeration
  - Technology fingerprinting
  - SQL injection / XSS / LFI detection
  - WHOIS & DNS enumeration
  - Multi-threaded for high speed
  - Beautiful colored terminal output
  - JSON / TXT / HTML report export

Author:  Security Research Toolkit
Usage:   python web_scanner.py -u https://example.com [options]
"""

import argparse
import socket
import ssl
import sys
import json
import time
import re
import os
import hashlib
import random
import string
import urllib.parse
import ipaddress
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict

try:
    import requests
    from requests.exceptions import RequestException, SSLError, ConnectionError, Timeout
except ImportError:
    print("[!] 'requests' library is required. Install: pip install requests")
    sys.exit(1)

try:
    from colorama import init, Fore, Style, Back
    init(autoreset=True)
except ImportError:
    # Fallback if colorama not installed
    class Fore:
        RED = GREEN = YELLOW = BLUE = MAGENTA = CYAN = WHITE = RESET = ""
    class Style:
        BRIGHT = RESET_ALL = DIM = ""
    class Back:
        RED = GREEN = YELLOW = BLUE = MAGENTA = CYAN = WHITE = RESET = ""

# ============================================================================
# CONSTANTS & CONFIGURATION
# ============================================================================
VERSION = "3.0"
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Edge/120.0.0.0",
]
TIMEOUT = 5
MAX_THREADS = 50

# Top common web ports
COMMON_PORTS = {
    21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS",
    80: "HTTP", 110: "POP3", 135: "MSRPC", 139: "NetBIOS", 143: "IMAP",
    443: "HTTPS", 445: "SMB", 993: "IMAPS", 995: "POP3S", 1433: "MSSQL",
    1521: "Oracle", 2082: "cPanel", 2083: "cPanel SSL", 2086: "WHM",
    2087: "WHM SSL", 3306: "MySQL", 3389: "RDP", 5432: "PostgreSQL",
    5900: "VNC", 6379: "Redis", 8000: "HTTP-Alt", 8080: "HTTP-Proxy",
    8443: "HTTPS-Alt", 8888: "Alt-HTTP", 9200: "Elasticsearch",
    27017: "MongoDB", 27018: "MongoDB-Web", 50000: "SAP",
}

# Common paths for directory/file bruteforce
WORDLIST = [
    "admin", "administrator", "login", "wp-admin", "wp-login.php",
    "wp-content", "wp-includes", "wp-config.php", "wp-config.php.bak",
    "config", "config.php", "configuration.php", "settings.php",
    "backup", "backups", "bak", "old", "temp", "tmp", "test",
    "uploads", "upload", "files", "images", "img", "media", "assets",
    "css", "js", "scripts", "static", "public", "private",
    "api", "api/v1", "api/v2", "v1", "v2", "rest", "graphql",
    "robots.txt", "sitemap.xml", "sitemap_index.xml", "crossdomain.xml",
    "humans.txt", "security.txt", ".well-known/security.txt",
    "favicon.ico", "manifest.json", "browserconfig.xml",
    ".git", ".git/HEAD", ".git/config", ".gitignore", ".gitattributes",
    ".env", ".env.example", ".env.local", ".env.production", ".env.backup",
    ".htaccess", ".htpasswd", "web.config", "robots.txt", "readme.md",
    "README.md", "README.txt", "readme.txt", "INSTALL", "LICENSE",
    "CHANGELOG", "VERSION", "package.json", "composer.json",
    "phpinfo.php", "info.php", "test.php", "debug.php", "shell.php",
    "cmd.php", "backdoor.php", "c99.php", "r57.php", "wso.php",
    "user", "users", "account", "accounts", "profile", "profiles",
    "dashboard", "panel", "cpanel", "control", "manage", "manager",
    "phpmyadmin", "pma", "mysql", "adminer", "adminer.php",
    "database", "db", "sql", "dump", "database.sql", "db.sql",
    "log", "logs", "error.log", "error_log", "access.log", "debug.log",
    "server-status", "server-info", "status", "info", "ping",
    "cgi-bin", "cgi-bin/test", "scripts", "bin", "exe",
    "xmlrpc.php", "xmlrpc", "soap", "wsdl",
    "index.php", "index.html", "index.htm", "default.aspx", "default.asp",
    "home", "main", "welcome", "portal", "start", "begin",
    "download", "downloads", "file", "files", "doc", "docs",
    "help", "about", "contact", "support", "faq",
    "blog", "news", "article", "articles", "post", "posts",
    "search", "find", "lookup", "query",
    "register", "signup", "signin", "logout", "auth", "authenticate",
    "token", "session", "cookie", "forgot", "reset", "password",
    "secret", "hidden", "private", "internal", "restricted",
    "console", "terminal", "shell", "command", "exec", "run",
    "dev", "development", "staging", "stage", "prod", "production",
    "demo", "example", "sample", "sandbox", "lab",
    "backup.zip", "backup.tar.gz", "backup.sql", "site.zip", "www.zip",
    "web.zip", "html.zip", "public.zip", "src.zip", "source.zip",
    "old.zip", "bak.zip", "archive.zip", "app.zip", "code.zip",
    "cgi", "fcgi", "perl", "python", "ruby", "node",
    "swagger", "swagger.json", "swagger.yaml", "openapi", "openapi.json",
    "graphql", "graphiql", "playground",
    "metrics", "prometheus", "health", "healthcheck", "ping", "pong",
    "trace", "options", "actuator", "actuator/env", "actuator/health",
    "actuator/info", "actuator/beans", "actuator/mappings", "actuator/configprops",
    "geoserver", "geoserver/web", "jmx", "jolokia", "hawtio",
    "kibana", "grafana", "prometheus", "alertmanager",
    "jenkins", "jenkins/script", "jenkins/login", "teamcity",
    "gitlab", "gitlab/users/sign_in", "gitea", "gogs",
    ".svn", ".svn/entries", ".svn/wc.db", ".hg", ".hg/store",
    "CVS", "CVS/Root", ".DS_Store", "Thumbs.db", "desktop.ini",
    "WEB-INF", "WEB-INF/web.xml", "META-INF", "META-INF/MANIFEST.MF",
]

# Subdomain wordlist
SUBDOMAIN_WORDLIST = [
    "www", "mail", "ftp", "smtp", "pop", "pop3", "imap", "webmail",
    "email", "mx", "mx1", "mx2", "ns", "ns1", "ns2", "ns3", "ns4",
    "dns", "dns1", "dns2", "vpn", "remote", "gateway", "gw", "router",
    "admin", "administrator", "panel", "cpanel", "whm", "webmin",
    "api", "api2", "apiv1", "rest", "graphql", "ws", "websocket",
    "dev", "development", "staging", "stage", "test", "testing", "qa",
    "prod", "production", "live", "demo", "sample", "sandbox", "lab",
    "beta", "alpha", "preview", "pre", "preprod", "uat", "pre-uat",
    "www1", "www2", "www3", "web", "web1", "web2", "web3",
    "app", "apps", "application", "applications", "portal", "portals",
    "secure", "ssl", "tls", "https", "http", "static", "assets", "cdn",
    "media", "images", "img", "photos", "photo", "video", "videos",
    "files", "file", "upload", "uploads", "download", "downloads",
    "static", "assets", "resource", "resources", "content", "cms",
    "blog", "blogs", "news", "forum", "forums", "community", "social",
    "shop", "store", "cart", "pay", "payment", "checkout", "billing",
    "support", "help", "helpdesk", "ticket", "tickets", "service",
    "status", "stats", "monitor", "monitoring", "nagios", "zabbix",
    "log", "logs", "syslog", "kibana", "grafana", "prometheus",
    "backup", "bak", "backups", "archive", "archives", "old", "new",
    "mysql", "postgres", "postgresql", "mongo", "mongodb", "redis",
    "elastic", "elasticsearch", "kibana", "logstash", "solr",
    "jenkins", "bamboo", "travis", "circleci", "github", "gitlab",
    "bitbucket", "jira", "confluence", "slack", "teams", "zoom",
    "intranet", "internal", "private", "corp", "corporate", "office",
    "remote", "vpn", "rdp", "ssh", "sftp", "ftp2", "tftp",
    "proxy", "proxies", "lb", "loadbalancer", "haproxy", "nginx",
    "apache", "tomcat", "iis", "iis6", "iis7", "lighttpd", "caddy",
    "node", "nodejs", "python", "ruby", "rails", "django", "flask",
    "java", "spring", "tomcat", "jboss", "wildfly", "weblogic",
    "aws", "azure", "gcp", "cloud", "cloudfront", "s3", "ec2",
    "heroku", "digitalocean", "linode", "vultr", "ovh", "ionos",
    "test1", "test2", "dev1", "dev2", "staging1", "staging2",
    "us", "uk", "eu", "asia", "jp", "de", "fr", "es", "it", "ru",
    "us-east", "us-west", "eu-west", "eu-central", "ap-southeast",
]

# Vulnerable file extensions
VULN_EXTENSIONS = [
    ".bak", ".backup", ".old", ".orig", ".copy", ".tmp", ".swp",
    ".sql", ".db", ".sqlite", ".sqlite3", ".mdb", ".accdb",
    ".log", ".txt", ".csv", ".json", ".xml", ".yml", ".yaml",
    ".env", ".config", ".ini", ".conf", ".cfg", ".properties",
    ".key", ".pem", ".cer", ".crt", ".pfx", ".p12",
    ".zip", ".tar", ".tar.gz", ".tgz", ".rar", ".7z",
    ".git", ".svn", ".hg", ".DS_Store", "Thumbs.db",
    ".asp", ".aspx", ".jsp", ".jspx", ".php", ".php5", ".php7",
    ".do", ".action", ".cgi", ".pl", ".py", ".rb", ".sh", ".bash",
]

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================
class Logger:
    """Colored output logger."""
    @staticmethod
    def info(msg):
        print(f"{Fore.CYAN}[*]{Style.RESET_ALL} {msg}")

    @staticmethod
    def success(msg):
        print(f"{Fore.GREEN}[+]{Style.RESET_ALL} {msg}")

    @staticmethod
    def warning(msg):
        print(f"{Fore.YELLOW}[!]{Style.RESET_ALL} {msg}")

    @staticmethod
    def error(msg):
        print(f"{Fore.RED}[-]{Style.RESET_ALL} {msg}")

    @staticmethod
    def critical(msg):
        print(f"{Back.RED}{Fore.WHITE}[CRITICAL]{Style.RESET_ALL} {msg}")

    @staticmethod
    def found(msg):
        print(f"{Fore.GREEN}{Style.BRIGHT}[FOUND]{Style.RESET_ALL} {msg}")

    @staticmethod
    def vuln(msg):
        print(f"{Fore.RED}{Style.BRIGHT}[VULN]{Style.RESET_ALL} {msg}")

    @staticmethod
    def banner():
        print(f"""{Fore.CYAN}{Style.BRIGHT}
╔══════════════════════════════════════════════════════════════════╗
║                  ADVANCED WEB SCANNER v{VERSION}                        ║
║              Multi-Module Security Assessment                     ║
╚══════════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
        """)


def random_user_agent():
    return random.choice(USER_AGENTS)


def normalize_url(target):
    """Ensure URL has scheme."""
    if not target.startswith(("http://", "https://")):
        return "http://" + target
    return target


def get_domain(target):
    """Extract domain from URL."""
    parsed = urllib.parse.urlparse(target)
    return parsed.netloc or parsed.path


def make_session():
    """Create a requests session with safe defaults."""
    s = requests.Session()
    s.headers.update({
        "User-Agent": random_user_agent(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    })
    return s


# ============================================================================
# MODULE 1: PORT SCANNER
# ============================================================================
class PortScanner:
    """TCP connect port scanner with service detection."""
    def __init__(self, target, ports=None, threads=100):
        self.target = target
        self.ports = ports or list(COMMON_PORTS.keys())
        self.threads = threads
        self.open_ports = []
        self.lock = __import__('threading').Lock()

    def scan_port(self, port):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((self.target, port))
            sock.close()
            if result == 0:
                service = COMMON_PORTS.get(port, "unknown")
                with self.lock:
                    self.open_ports.append({"port": port, "service": service})
                Logger.found(f"Port {port:>5} OPEN  ({service})")
                return port, True
        except (socket.timeout, socket.gaierror, ConnectionRefusedError, OSError):
            return port, False
        return port, False

    def scan(self):
        Logger.info(f"Starting port scan on {self.target} ({len(self.ports)} ports)...")
        import threading
        semaphore = threading.Semaphore(self.threads)
        threads = []
        for port in self.ports:
            def worker(p=port):
                semaphore.acquire()
                try:
                    self.scan_port(p)
                finally:
                    semaphore.release()
            t = threading.Thread(target=worker)
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
        Logger.success(f"Port scan complete. {len(self.open_ports)} open port(s) found.")
        return self.open_ports


# ============================================================================
# MODULE 2: HTTP HEADER ANALYZER
# ============================================================================
class HeaderAnalyzer:
    """Analyze HTTP headers for security issues."""
    SECURITY_HEADERS = {
        "Strict-Transport-Security": "HSTS - forces HTTPS",
        "Content-Security-Policy": "CSP - prevents XSS/injection",
        "X-Frame-Options": "Clickjacking protection",
        "X-Content-Type-Options": "MIME sniffing protection",
        "Referrer-Policy": "Referrer leakage control",
        "Permissions-Policy": "Browser feature restrictions",
        "X-XSS-Protection": "XSS filter (legacy)",
        "X-Permitted-Cross-Domain-Policies": "Flash/PDF cross-domain",
        "Cross-Origin-Opener-Policy": "Process isolation",
        "Cross-Origin-Resource-Policy": "Resource isolation",
        "Cross-Origin-Embedder-Policy": "Embedding restrictions",
    }

    DANGEROUS_HEADERS = [
        "Server", "X-Powered-By", "X-AspNet-Version", "X-AspNetMvc-Version",
    ]

    def __init__(self, target):
        self.target = normalize_url(target)
        self.session = make_session()
        self.findings = {"missing": [], "present": [], "info_disclosure": [], "cookies": []}

    def analyze(self):
        Logger.info(f"Analyzing HTTP headers for {self.target}...")
        try:
            resp = self.session.get(self.target, timeout=TIMEOUT, verify=False, allow_redirects=True)
            headers = resp.headers

            # Check security headers
            for header, desc in self.SECURITY_HEADERS.items():
                if header in headers:
                    self.findings["present"].append({"header": header, "value": headers[header]})
                    Logger.success(f"  ✓ {header}: {headers[header][:80]}")
                else:
                    self.findings["missing"].append({"header": header, "description": desc})
                    Logger.warning(f"  ✗ MISSING {header} ({desc})")

            # Check information disclosure
            for header in self.DANGEROUS_HEADERS:
                if header in headers:
                    self.findings["info_disclosure"].append({"header": header, "value": headers[header]})
                    Logger.warning(f"  ⚠ Info Disclosure: {header}: {headers[header]}")

            # Cookies analysis
            for cookie in resp.cookies:
                flags = []
                if not cookie.secure:
                    flags.append("Missing Secure flag")
                if not cookie.has_nonstandard_attr("HttpOnly"):
                    flags.append("Missing HttpOnly")
                if not cookie.has_nonstandard_attr("SameSite"):
                    flags.append("Missing SameSite")
                if flags:
                    self.findings["cookies"].append({"name": cookie.name, "issues": flags})
                    Logger.vuln(f"  Cookie '{cookie.name}' issues: {', '.join(flags)}")
                else:
                    Logger.success(f"  Cookie '{cookie.name}' is properly configured")

            # CORS
            if "Access-Control-Allow-Origin" in headers:
                aco = headers["Access-Control-Allow-Origin"]
                if aco == "*":
                    Logger.vuln(f"  CORS: Wildcard origin (*) is set")
                self.findings.setdefault("cors", []).append({"header": "Access-Control-Allow-Origin", "value": aco})

            # HTTP methods
            try:
                opts = self.session.options(self.target, timeout=TIMEOUT, verify=False)
                if "Allow" in opts.headers:
                    methods = opts.headers["Allow"]
                    Logger.info(f"  Allowed methods: {methods}")
                    dangerous = [m for m in methods.split(",") if m.strip().upper() in ["PUT", "DELETE", "TRACE", "CONNECT"]]
                    if dangerous:
                        Logger.vuln(f"  Dangerous methods enabled: {', '.join(dangerous)}")
            except Exception:
                pass

        except Exception as e:
            Logger.error(f"Header analysis failed: {e}")
        return self.findings


# ============================================================================
# MODULE 3: SSL/TLS ANALYZER
# ============================================================================
class SSLAnalyzer:
    """SSL/TLS certificate and configuration analyzer."""
    def __init__(self, target):
        self.target = get_domain(target)
        self.findings = {}

    def analyze(self):
        Logger.info(f"Analyzing SSL/TLS for {self.target}...")
        try:
            ctx = ssl.create_default_context()
            with ctx.wrap_socket(socket.socket(), server_hostname=self.target) as s:
                s.settimeout(5)
                s.connect((self.target, 443))
                cert = s.getpeercert()
                cipher = s.cipher()
                tls_version = s.version()

                self.findings["tls_version"] = tls_version
                self.findings["cipher"] = cipher[0] if cipher else "Unknown"
                self.findings["bits"] = cipher[2] if cipher else 0

                # Subject
                subject = dict(x[0] for x in cert.get("subject", []))
                issuer = dict(x[0] for x in cert.get("issuer", []))
                self.findings["subject"] = subject
                self.findings["issuer"] = issuer

                # Validity
                not_before = cert.get("notBefore")
                not_after = cert.get("notAfter")
                self.findings["valid_from"] = not_before
                self.findings["valid_to"] = not_after
                self.findings["san"] = [v for (k, v) in cert.get("subjectAltName", []) if k == "DNS"]

                # Display
                Logger.success(f"  TLS Version: {tls_version}")
                Logger.success(f"  Cipher: {self.findings['cipher']} ({self.findings['bits']} bits)")
                Logger.success(f"  Subject: {subject.get('commonName', 'N/A')}")
                Logger.success(f"  Issuer: {issuer.get('commonName', 'N/A')}")
                Logger.success(f"  Valid: {not_before} → {not_after}")
                Logger.success(f"  SANs: {len(self.findings['san'])} domain(s)")

                # Warnings
                if tls_version in ["TLSv1", "TLSv1.1", "SSLv2", "SSLv3"]:
                    Logger.vuln(f"  Weak TLS version: {tls_version}")
                if self.findings["bits"] < 128:
                    Logger.vuln(f"  Weak cipher strength: {self.findings['bits']} bits")

                # Expiry check
                try:
                    expiry = datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z")
                    days_left = (expiry - datetime.utcnow()).days
                    if days_left < 0:
                        Logger.critical(f"  Certificate EXPIRED {-days_left} days ago!")
                    elif days_left < 30:
                        Logger.vuln(f"  Certificate expires in {days_left} days!")
                    else:
                        Logger.success(f"  Certificate valid for {days_left} more days")
                except Exception:
                    pass

        except (socket.gaierror, ConnectionRefusedError, ssl.SSLError, socket.timeout, OSError) as e:
            Logger.error(f"SSL analysis failed: {e}")
        return self.findings


# ============================================================================
# MODULE 4: DIRECTORY & FILE BRUTEFORCER
# ============================================================================
class DirectoryBruteforcer:
    """Bruteforce directories and files."""
    def __init__(self, target, wordlist=None, threads=MAX_THREADS, extensions=None):
        self.target = normalize_url(target).rstrip("/")
        self.wordlist = wordlist or WORDLIST
        self.threads = threads
        self.extensions = extensions or []
        self.found = []
        self.session = make_session()
        self.session.verify = False
        self.interesting_codes = {200, 201, 202, 204, 301, 302, 307, 308, 401, 403, 405, 500, 503}

    def check_path(self, path):
        url = f"{self.target}/{path.lstrip('/')}"
        try:
            resp = self.session.get(url, timeout=TIMEOUT, allow_redirects=False, stream=True)
            size = int(resp.headers.get("Content-Length", 0))
            status = resp.status
            resp.close()
            if status in self.interesting_codes:
                entry = {"url": url, "status": status, "size": size, "path": path}
                self.found.append(entry)
                color = Fore.GREEN if status == 200 else (Fore.YELLOW if status in [301, 302] else Fore.RED)
                size_str = f"{size:>10}" if size else f"{'(empty)':>10}"
                print(f"  {color}[{status}]{Style.RESET_ALL} {size_str}B  {url}")
                return entry
        except (RequestException, Timeout, ConnectionError):
            return None
        return None

    def bruteforce(self):
        Logger.info(f"Starting directory bruteforce on {self.target} ({len(self.wordlist)} paths)...")
        paths = list(self.wordlist)
        # Add extensions
        for ext in self.extensions:
            for w in self.wordlist[:50]:  # Top 50 with extensions
                paths.append(f"{w}{ext}")
        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            futures = {executor.submit(self.check_path, p): p for p in paths}
            for future in as_completed(futures):
                _ = future.result()
        Logger.success(f"Directory scan complete. {len(self.found)} item(s) found.")
        return self.found


# ============================================================================
# MODULE 5: SUBDOMAIN ENUMERATOR
# ============================================================================
class SubdomainEnumerator:
    """Enumerate subdomains via DNS resolution."""
    def __init__(self, target, wordlist=None, threads=50):
        self.domain = get_domain(target)
        # Strip subdomains to get root
        parts = self.domain.split(".")
        if len(parts) > 2:
            # Find likely root domain (e.g., example.co.uk → keep 3 parts)
            self.root = ".".join(parts[-2:]) if not self._is_special_tld(parts[-1]) else ".".join(parts[-3:])
        else:
            self.root = self.domain
        self.wordlist = wordlist or SUBDOMAIN_WORDLIST
        self.threads = threads
        self.found = []

    def _is_special_tld(self, tld):
        special = {"uk", "au", "co", "com", "net", "org", "gov", "edu", "ac", "mil"}
        return tld in special

    def check_subdomain(self, sub):
        hostname = f"{sub}.{self.root}"
        try:
            ip = socket.gethostbyname(hostname)
            self.found.append({"subdomain": hostname, "ip": ip})
            Logger.found(f"  {hostname:>40} → {ip}")
            return True
        except (socket.gaierror, UnicodeError):
            return False

    def enumerate(self):
        Logger.info(f"Enumerating subdomains for {self.root} ({len(self.wordlist)} candidates)...")
        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            futures = {executor.submit(self.check_subdomain, sub): sub for sub in self.wordlist}
            for future in as_completed(futures):
                _ = future.result()
        Logger.success(f"Subdomain enumeration complete. {len(self.found)} subdomain(s) found.")
        return self.found


# ============================================================================
# MODULE 6: TECHNOLOGY FINGERPRINTING
# ============================================================================
class TechFingerprinter:
    """Detect web technologies (CMS, frameworks, servers, libraries)."""
    SIGNATURES = {
        # Servers
        "Server": {
            "nginx": r"nginx/?([\d.]+)?",
            "Apache": r"Apache/?([\d.]+)?",
            "IIS": r"Microsoft-IIS/?([\d.]+)?",
            "LiteSpeed": r"LiteSpeed",
            "Caddy": r"Caddy",
            "Cloudflare": r"cloudflare",
            "AWS ELB": r"aws(elb|)",
            "GWS": r"gws",
            "Tomcat": r"Tomcat",
        },
        "X-Powered-By": {
            "PHP": r"PHP/?([\d.]+)?",
            "ASP.NET": r"ASP\.NET",
            "Express": r"Express",
            "Next.js": r"Next\.js",
            "Plesk": r"Plesk",
        },
        # Cookies
        "cookies": {
            "PHPSESSID": "PHP",
            "JSESSIONID": "Java (Tomcat/JBoss)",
            "ASP.NET_SessionId": "ASP.NET",
            "cfid": "ColdFusion",
            "sid": "Java (generic)",
            "rack.session": "Ruby Rack",
            "_session_id": "Ruby on Rails",
            "laravel_session": "Laravel (PHP)",
            "XSRF-TOKEN": "Laravel/Angular",
            "connect.sid": "Node.js Connect/Express",
            "__cfduid": "Cloudflare",
        },
        # HTML signatures
        "html": {
            "wp-content": "WordPress",
            "wp-includes": "WordPress",
            "/wp-json/": "WordPress REST API",
            "Joomla": "Joomla",
            "Drupal": "Drupal",
            "Shopify": "Shopify",
            "Squarespace": "Squarespace",
            "Wix": "Wix",
            "Magento": "Magento",
            "PrestaShop": "PrestaShop",
            "react": "React",
            "angular": "Angular",
            "vue": "Vue.js",
            "jquery": "jQuery",
            "bootstrap": "Bootstrap",
            "tailwind": "Tailwind CSS",
            "analytics.js": "Google Analytics",
            "gtag": "Google Analytics 4",
            "fbq(": "Facebook Pixel",
            "hotjar": "Hotjar",
            "stripe": "Stripe",
            "cloudflare": "Cloudflare",
            "recaptcha": "Google reCAPTCHA",
            "fonts.googleapis.com": "Google Fonts",
            "ajax.googleapis.com": "Google CDN (jQuery)",
        },
        # Meta tags
        "meta": {
            "generator": "CMS/Framework (check value)",
        },
    }

    def __init__(self, target):
        self.target = normalize_url(target)
        self.session = make_session()
        self.session.verify = False
        self.detected = defaultdict(list)

    def analyze(self):
        Logger.info(f"Fingerprinting technologies on {self.target}...")
        try:
            resp = self.session.get(self.target, timeout=TIMEOUT)

            # Headers
            for header, sigs in self.SIGNATURES.items():
                if header in ["html", "meta", "cookies"]:
                    continue
                value = resp.headers.get(header, "")
                if value:
                    for tech, pattern in sigs.items():
                        if re.search(pattern, value, re.IGNORECASE):
                            self.detected[tech].append(f"Header: {header}")
                            Logger.success(f"  Detected: {tech} (via {header})")

            # Cookies
            for cookie in resp.cookies:
                for sig, tech in self.SIGNATURES["cookies"].items():
                    if sig.lower() in cookie.name.lower():
                        self.detected[tech].append(f"Cookie: {cookie.name}")
                        Logger.success(f"  Detected: {tech} (via cookie {cookie.name})")

            # HTML body
            body = resp.text
            for pattern, tech in self.SIGNATURES["html"].items():
                if pattern.lower() in body.lower():
                    self.detected[tech].append(f"HTML body")
                    Logger.success(f"  Detected: {tech}")

            # Meta tags
            meta_matches = re.findall(r'<meta[^>]*name=["\']([^"\']+)["\'][^>]*content=["\']([^"\']+)["\']', body, re.IGNORECASE)
            for name, content in meta_matches:
                if "generator" in name.lower():
                    self.detected[content].append(f"Meta: {name}")
                    Logger.success(f"  Detected: {content} (meta generator)")

            # Script sources
            scripts = re.findall(r'<script[^>]+src=["\']([^"\']+)["\']', body, re.IGNORECASE)
            for s in scripts[:20]:
                if "google-analytics" in s:
                    self.detected["Google Analytics"].append("Script tag")
                if "googletagmanager" in s:
                    self.detected["Google Tag Manager"].append("Script tag")
                if "facebook" in s:
                    self.detected["Facebook SDK"].append("Script tag")
                if "hotjar" in s:
                    self.detected["Hotjar"].append("Script tag")

        except Exception as e:
            Logger.error(f"Tech fingerprinting failed: {e}")
        return dict(self.detected)


# ============================================================================
# MODULE 7: VULNERABILITY SCANNER
# ============================================================================
class VulnerabilityScanner:
    """Test for common web vulnerabilities."""
    SQLI_PAYLOADS = ["'", "\"", "' OR '1'='1", "1' OR '1'='1' --", "' UNION SELECT NULL--", "1; DROP TABLE users--"]
    XSS_PAYLOADS = ["<script>alert('XSS')</script>", "\"><svg onload=alert(1)>", "<img src=x onerror=alert(1)>"]
    LFI_PAYLOADS = ["../../../etc/passwd", "..\\..\\..\\windows\\win.ini", "/etc/passwd", "....//....//....//etc/passwd"]
    RCE_PARAMS = ["cmd", "exec", "command", "execute", "ping", "query", "jump", "code", "reg", "do", "func", "arg", "option", "load", "process", "step", "feature", "obj", "path", "pg", "style", "pdf", "template", "php_path", "doc", "img", "filename"]

    def __init__(self, target, threads=20):
        self.target = normalize_url(target).rstrip("/")
        self.session = make_session()
        self.session.verify = False
        self.threads = threads
        self.findings = []

    def _test_url(self, url, param=None, payload=None, method="GET"):
        try:
            if method == "GET":
                resp = self.session.get(url, timeout=TIMEOUT, allow_redirects=False)
            else:
                resp = self.session.post(url, data={param: payload}, timeout=TIMEOUT, allow_redirects=False)
            return resp
        except Exception:
            return None

    def test_sqli(self):
        Logger.info("Testing for SQL injection vulnerabilities...")
        sql_errors = [
            "you have an error in your sql syntax",
            "warning: mysql", "unclosed quotation mark",
            "quoted string not properly terminated",
            "pg_query()", "psycopg2", "valid mysql result",
            "mysqlclient", "mysqli_", "jdbc.sqlserver",
            "ora-00933", "ora-01756", "ora-",
            "sqlite3.operationalerror", "sqlite_",
            "supplied argument is not a valid", "microsoft ole db provider",
            "microsoft sql native client error",
        ]
        for param in ["id", "page", "cat", "search", "q", "user", "name", "view", "file"]:
            for payload in self.SQLI_PAYLOADS[:3]:
                test_url = f"{self.target}/?{param}={urllib.parse.quote(payload)}"
                resp = self._test_url(test_url)
                if resp:
                    body = resp.text.lower()
                    for err in sql_errors:
                        if err in body:
                            finding = {
                                "type": "SQL Injection (Error-based)",
                                "url": test_url,
                                "param": param,
                                "payload": payload,
                                "evidence": err,
                                "severity": "HIGH",
                            }
                            self.findings.append(finding)
                            Logger.vuln(f"  SQLi @ {test_url}")
                            return True
        Logger.info("  No obvious SQLi found.")
        return False

    def test_xss(self):
        Logger.info("Testing for XSS vulnerabilities (reflected)...")
        for param in ["q", "search", "s", "id", "name", "user", "input", "query"]:
            payload = "vulnscan12345"
            test_url = f"{self.target}/?{param}={urllib.parse.quote(payload)}"
            resp = self._test_url(test_url)
            if resp and payload in resp.text:
                # Check if HTML-encoded or actually reflected
                if payload.lower() in resp.text.lower() and "<" not in payload:
                    finding = {
                        "type": "Reflected XSS (potential)",
                        "url": test_url,
                        "param": param,
                        "payload": payload,
                        "severity": "MEDIUM",
                    }
                    self.findings.append(finding)
                    Logger.warning(f"  Possible reflected XSS @ {test_url}")
                    break
        Logger.info("  XSS testing done.")
        return self.findings

    def test_lfi(self):
        Logger.info("Testing for Local File Inclusion (LFI)...")
        lfi_signatures = ["root:x:0:0", "[extensions]", "for 16-bit app support"]
        for param in ["file", "path", "page", "include", "doc", "img", "filename", "template"]:
            for payload in self.LFI_PAYLOADS:
                test_url = f"{self.target}/?{param}={urllib.parse.quote(payload)}"
                resp = self._test_url(test_url)
                if resp:
                    for sig in lfi_signatures:
                        if sig in resp.text:
                            finding = {
                                "type": "Local File Inclusion (LFI)",
                                "url": test_url,
                                "param": param,
                                "payload": payload,
                                "evidence": sig,
                                "severity": "HIGH",
                            }
                            self.findings.append(finding)
                            Logger.vuln(f"  LFI @ {test_url} → found '{sig}'")
                            return True
        Logger.info("  No LFI detected.")
        return False

    def test_open_redirect(self):
        Logger.info("Testing for Open Redirect...")
        for param in ["url", "redirect", "next", "return", "goto", "target", "rurl", "returnUrl"]:
            for payload in ["https://evil.com", "//evil.com"]:
                test_url = f"{self.target}/?{param}={urllib.parse.quote(payload, safe='')}"
                resp = self._test_url(test_url)
                if resp and resp.status_code in [301, 302, 303, 307, 308]:
                    loc = resp.headers.get("Location", "")
                    if "evil.com" in loc:
                        finding = {
                            "type": "Open Redirect",
                            "url": test_url,
                            "param": param,
                            "payload": payload,
                            "redirect_to": loc,
                            "severity": "LOW",
                        }
                        self.findings.append(finding)
                        Logger.vuln(f"  Open Redirect @ {test_url}")
                        return True
        Logger.info("  No open redirect found.")
        return False

    def test_sensitive_files(self):
        Logger.info("Checking for sensitive file exposure...")
        sensitive = [
            ".env", ".git/HEAD", ".git/config", ".svn/entries",
            "wp-config.php.bak", "config.php.bak", "configuration.php.bak",
            "database.sql", "db.sql", "dump.sql", "backup.sql",
            "phpinfo.php", "info.php", "test.php", "server-status",
            "crossdomain.xml", "elmah.axd", "trace.axd",
            "web.config", "WEB-INF/web.xml", "META-INF/MANIFEST.MF",
            "robots.txt", "security.txt", ".well-known/security.txt",
        ]
        exposed = []
        for path in sensitive:
            url = f"{self.target}/{path}"
            try:
                resp = self.session.get(url, timeout=TIMEOUT, allow_redirects=False)
                if resp.status_code == 200 and len(resp.text) > 0:
                    exposed.append({"url": url, "status": resp.status_code, "size": len(resp.text)})
                    Logger.vuln(f"  Exposed: {url} ({len(resp.text)} bytes)")
            except Exception:
                pass
        if exposed:
            self.findings.append({"type": "Sensitive File Exposure", "files": exposed, "severity": "MEDIUM"})
        else:
            Logger.info("  No sensitive files exposed.")
        return exposed

    def test_directory_listing(self):
        Logger.info("Checking for directory listing...")
        dirs = ["uploads", "images", "files", "backup", "backups", "css", "js", "static", "media", "assets"]
        for d in dirs:
            url = f"{self.target}/{d}/"
            try:
                resp = self.session.get(url, timeout=TIMEOUT, allow_redirects=False)
                body = resp.text.lower()
                if resp.status_code == 200 and ("index of" in body or "directory listing" in body or "<title>index of" in body):
                    self.findings.append({"type": "Directory Listing", "url": url, "severity": "LOW"})
                    Logger.vuln(f"  Directory listing: {url}")
            except Exception:
                pass
        return self.findings

    def scan(self):
        Logger.info("=" * 70)
        Logger.info("STARTING VULNERABILITY SCAN")
        Logger.info("=" * 70)
        self.test_sensitive_files()
        self.test_directory_listing()
        self.test_lfi()
        self.test_sqli()
        self.test_xss()
        self.test_open_redirect()
        Logger.success(f"Vulnerability scan complete. {len(self.findings)} finding(s).")
        return self.findings


# ============================================================================
# MODULE 8: DNS & WHOIS
# ============================================================================
class DNSEnumerator:
    """DNS record enumeration and basic WHOIS."""
    RECORD_TYPES = ["A", "AAAA", "MX", "NS", "TXT", "SOA", "CNAME"]

    def __init__(self, target):
        self.domain = get_domain(target)
        # Strip subdomains
        parts = self.domain.split(".")
        if len(parts) > 2:
            self.root = ".".join(parts[-2:])
        else:
            self.root = self.domain
        self.records = {}

    def get_records(self):
        Logger.info(f"Resolving DNS records for {self.root}...")
        # A records
        try:
            addrs = socket.getaddrinfo(self.root, None)
            ips = list({a[4][0] for a in addrs if a[0] == socket.AF_INET})
            self.records["A"] = ips
            Logger.success(f"  A: {', '.join(ips)}")
        except Exception as e:
            Logger.error(f"  A: {e}")

        # Reverse DNS
        for ip in self.records.get("A", []):
            try:
                host = socket.gethostbyaddr(ip)
                Logger.success(f"  Reverse {ip} → {host[0]}")
            except Exception:
                pass
        return self.records


# ============================================================================
# MODULE 9: REPORT GENERATOR
# ============================================================================
class ReportGenerator:
    """Generate scan reports in multiple formats."""
    def __init__(self, target, results):
        self.target = target
        self.results = results
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    def to_json(self, filepath=None):
        if not filepath:
            filepath = f"scan_report_{self.timestamp}.json"
        with open(filepath, "w") as f:
            json.dump({
                "target": self.target,
                "timestamp": self.timestamp,
                "results": self.results,
            }, f, indent=2, default=str)
        Logger.success(f"JSON report saved: {filepath}")
        return filepath

    def to_txt(self, filepath=None):
        if not filepath:
            filepath = f"scan_report_{self.timestamp}.txt"
        with open(filepath, "w") as f:
            f.write(f"=" * 70 + "\n")
            f.write(f"WEB SCAN REPORT - {self.target}\n")
            f.write(f"Generated: {datetime.now()}\n")
            f.write(f"=" * 70 + "\n\n")
            f.write(json.dumps(self.results, indent=2, default=str))
        Logger.success(f"TXT report saved: {filepath}")
        return filepath

    def to_html(self, filepath=None):
        if not filepath:
            filepath = f"scan_report_{self.timestamp}.html"
        html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Scan Report - {self.target}</title>
<style>
body{{font-family:Arial,sans-serif;margin:40px;background:#1e1e1e;color:#ddd}}
h1{{color:#0ff}}h2{{color:#0af;border-bottom:1px solid #444;padding-bottom:5px}}
pre{{background:#2d2d2d;padding:15px;border-radius:5px;overflow:auto}}
.vuln{{color:#f44}}.ok{{color:#4f4}}.warn{{color:#fa0}}
</style></head><body>
<h1>Web Scan Report</h1>
<p><b>Target:</b> {self.target}</p>
<p><b>Generated:</b> {datetime.now()}</p>
<h2>Full Results</h2>
<pre>{json.dumps(self.results, indent=2, default=str)}</pre>
</body></html>"""
        with open(filepath, "w") as f:
            f.write(html)
        Logger.success(f"HTML report saved: {filepath}")
        return filepath


# ============================================================================
# MAIN SCANNER ORCHESTRATOR
# ============================================================================
class WebScanner:
    """Main scanner orchestrator."""
    def __init__(self, target, options):
        self.target = target
        self.options = options
        self.results = {
            "target": target,
            "start_time": datetime.now().isoformat(),
            "modules": {},
        }
        # Disable SSL warnings
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def run(self):
        Logger.banner()
        Logger.info(f"Target: {self.target}")
        Logger.info(f"Start time: {datetime.now()}")

        # Module: DNS
        if self.options.get("dns"):
            Logger.info("\n" + "=" * 70)
            Logger.info("MODULE: DNS ENUMERATION")
            Logger.info("=" * 70)
            dns = DNSEnumerator(self.target)
            self.results["modules"]["dns"] = dns.get_records()

        # Module: Port scan
        if self.options.get("ports"):
            Logger.info("\n" + "=" * 70)
            Logger.info("MODULE: PORT SCANNER")
            Logger.info("=" * 70)
            host = get_domain(self.target).split(":")[0]
            try:
                ip = socket.gethostbyname(host)
            except Exception:
                ip = host
            ps = PortScanner(ip, threads=self.options.get("threads", 100))
            self.results["modules"]["ports"] = ps.scan()

        # Module: SSL
        if self.options.get("ssl"):
            Logger.info("\n" + "=" * 70)
            Logger.info("MODULE: SSL/TLS ANALYSIS")
            Logger.info("=" * 70)
            ssl_a = SSLAnalyzer(self.target)
            self.results["modules"]["ssl"] = ssl_a.analyze()

        # Module: Headers
        if self.options.get("headers"):
            Logger.info("\n" + "=" * 70)
            Logger.info("MODULE: HTTP HEADERS")
            Logger.info("=" * 70)
            ha = HeaderAnalyzer(self.target)
            self.results["modules"]["headers"] = ha.analyze()

        # Module: Tech
        if self.options.get("tech"):
            Logger.info("\n" + "=" * 70)
            Logger.info("MODULE: TECH FINGERPRINTING")
            Logger.info("=" * 70)
            tf = TechFingerprinter(self.target)
            self.results["modules"]["tech"] = tf.analyze()

        # Module: Subdomains
        if self.options.get("subdomains"):
            Logger.info("\n" + "=" * 70)
            Logger.info("MODULE: SUBDOMAIN ENUMERATION")
            Logger.info("=" * 70)
            se = SubdomainEnumerator(self.target, threads=self.options.get("threads", 50))
            self.results["modules"]["subdomains"] = se.enumerate()

        # Module: Directory bruteforce
        if self.options.get("dirs"):
            Logger.info("\n" + "=" * 70)
            Logger.info("MODULE: DIRECTORY BRUTEFORCE")
            Logger.info("=" * 70)
            db = DirectoryBruteforcer(
                self.target,
                threads=self.options.get("threads", MAX_THREADS),
                extensions=self.options.get("extensions", []),
            )
            self.results["modules"]["directories"] = db.bruteforce()

        # Module: Vulnerabilities
        if self.options.get("vulns"):
            Logger.info("\n" + "=" * 70)
            Logger.info("MODULE: VULNERABILITY SCAN")
            Logger.info("=" * 70)
            vs = VulnerabilityScanner(self.target)
            self.results["modules"]["vulnerabilities"] = vs.scan()

        # Finish
        self.results["end_time"] = datetime.now().isoformat()
        elapsed = (datetime.fromisoformat(self.results["end_time"]) -
                   datetime.fromisoformat(self.results["start_time"])).total_seconds()
        self.results["duration_seconds"] = elapsed

        Logger.info("\n" + "=" * 70)
        Logger.success(f"SCAN COMPLETED in {elapsed:.2f} seconds")
        Logger.info("=" * 70)

        # Reports
        fmt = self.options.get("output_format", "json")
        outfile = self.options.get("output")
        if fmt or outfile:
            rg = ReportGenerator(self.target, self.results)
            if fmt == "json" or (outfile and outfile.endswith(".json")):
                rg.to_json(outfile)
            elif fmt == "txt" or (outfile and outfile.endswith(".txt")):
                rg.to_txt(outfile)
            elif fmt == "html" or (outfile and outfile.endswith(".html")):
                rg.to_html(outfile)
            elif outfile:
                rg.to_json(outfile)

        return self.results


# ============================================================================
# CLI ENTRY POINT
# ============================================================================
def main():
    parser = argparse.ArgumentParser(
        description="Advanced Web Scanner - Multi-Module Security Assessment",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python web_scanner.py -u https://example.com --all
  python web_scanner.py -u example.com -p -H -t -o report.json
  python web_scanner.py -u https://test.com --vulns --dirs --subdomains
        """
    )
    parser.add_argument("-u", "--url", required=True, help="Target URL or domain")
    parser.add_argument("--all", action="store_true", help="Run all modules")
    parser.add_argument("-p", "--ports", action="store_true", help="Port scan")
    parser.add_argument("-H", "--headers", action="store_true", help="HTTP header analysis")
    parser.add_argument("-s", "--ssl", action="store_true", help="SSL/TLS analysis")
    parser.add_argument("-d", "--dirs", action="store_true", help="Directory bruteforce")
    parser.add_argument("-S", "--subdomains", action="store_true", help="Subdomain enumeration")
    parser.add_argument("-t", "--tech", action="store_true", help="Tech fingerprinting")
    parser.add_argument("-v", "--vulns", action="store_true", help="Vulnerability scan")
    parser.add_argument("-D", "--dns", action="store_true", help="DNS enumeration")
    parser.add_argument("-T", "--threads", type=int, default=50, help="Number of threads")
    parser.add_argument("-e", "--extensions", nargs="+", default=[".bak", ".old", ".txt", ".zip", ".sql", ".log", ".env", ".git", ".config"],
                        help="File extensions to check")
    parser.add_argument("-o", "--output", help="Output file path")
    parser.add_argument("-f", "--output-format", choices=["json", "txt", "html"], default="json",
                        help="Output format")

    args = parser.parse_args()

    # Build options
    options = {
        "ports": args.ports or args.all,
        "headers": args.headers or args.all,
        "ssl": args.ssl or args.all,
        "dirs": args.dirs or args.all,
        "subdomains": args.subdomains or args.all,
        "tech": args.tech or args.all,
        "vulns": args.vulns or args.all,
        "dns": args.dns or args.all,
        "threads": args.threads,
        "extensions": args.extensions,
        "output": args.output,
        "output_format": args.output_format,
    }

    # Check if any module selected
    if not any([args.all, args.ports, args.headers, args.ssl, args.dirs,
                args.subdomains, args.tech, args.vulns, args.dns]):
        parser.print_help()
        print(f"\n{Fore.YELLOW}[!] Please select at least one module to run, or use --all{Style.RESET_ALL}")
        sys.exit(0)

    try:
        scanner = WebScanner(args.url, options)
        scanner.run()
    except KeyboardInterrupt:
        Logger.error("Scan interrupted by user.")
        sys.exit(1)
    except Exception as e:
        Logger.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
