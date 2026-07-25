import json
import os
import re
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field


BINARY_ALIASES = {
    "winws.exe": "nfqws",
    "nfqws": "nfqws",
}

DESCRIPTIONS = {
    "general": ("General", "Default strategy. Multisplit with seqovl, fake for UDP. Try this first."),
    "general_alt": ("General (ALT)", "Fake+fakedsplit with ts fooling. Good alternative if default doesn't work."),
    "general_alt2": ("General (ALT2)", "Multisplit with seqovl=652, split-pos=2. Variant with different offsets."),
    "general_alt3": ("General (ALT3)", "Hostfakesplit with auto fake TLS (rnd,dupsid,sni). Google sni=www.google.com, general sni=ya.ru."),
    "general_alt4": ("General (ALT4)", "Fake,multisplit with badseq fooling, badseq-increment=1000."),
    "general_alt5": ("General (ALT5)", "Syndata+multidisorder, IPv4 only. Minimal config, no per-hostlist splitting."),
    "general_alt6": ("General (ALT6)", "Multisplit with seqovl=681, split-pos=1. Same technique, different offsets."),
    "general_alt7": ("General (ALT7)", "Multisplit with split-pos=2,sniext+1, seqovl=679 for hostlisted; syndata for ipset."),
    "general_alt8": ("General (ALT8)", "Pure fake with badseq fooling, fake-tls-mod=none. No split, only fakes."),
    "general_alt9": ("General (ALT9)", "Hostfakesplit with ts fooling. Google host=www.google.com, general host=ozon.ru."),
    "general_alt10": ("General (ALT10)", "Pure fake with ts fooling. General uses tls_clienthello_4pda_to.bin as fake."),
    "general_alt11": ("General (ALT11)", "Fake,multisplit with ts fooling, repeats=8. QUIC fake repeats=11."),
    "general_alt12": ("General (ALT12)", "Hybrid: Discord fake,multisplit; Google hostfakesplit; general fake,multisplit."),
    "general_simple_fake": ("General (SIMPLE FAKE)", "Pure fake with ts fooling. Simple and effective for many providers."),
    "general_simple_fake_alt": ("General (SIMPLE FAKE ALT)", "Pure fake with badseq fooling, badseq-increment=2."),
    "general_simple_fake_alt2": ("General (SIMPLE FAKE ALT2)", "Pure fake with ts fooling. Game cutoff=n5."),
    "general_fake_tls_auto": ("General (FAKE TLS AUTO)", "Auto-generated fake TLS with multidisorder. High repeats for reliability."),
    "general_fake_tls_auto_alt": ("General (FAKE TLS AUTO ALT)", "Fake,fakedsplit with badseq fooling, auto fake TLS."),
    "general_fake_tls_auto_alt2": ("General (FAKE TLS AUTO ALT2)", "Fake,multisplit with badseq, badseq-increment=10000000."),
    "general_fake_tls_auto_alt3": ("General (FAKE TLS AUTO ALT3)", "Fake,multisplit with badseq, badseq-increment=1000."),
    "general_exp": ("General (EXP)", "Experimental. Uses quic filter-l7 and hostfakesplit for Google."),
    "general_multisplit": ("General (MULTISPLIT)", "Pure multisplit with seqovl. Multiple split positions for maximum DPI evasion."),
    "general_fake+disorder": ("General (FAKE+DISORDER)", "fake,multidisorder with badseq fooling. Aggressive split+reorder approach."),
    "general_fake_split": ("General (FAKE SPLIT)", "fake,fakedsplit with ts fooling. Combines fake packets with split at SNI boundary."),
    "game_discord": ("Game (DISCORD)", "Optimized for Discord voice/video. Aggressive QUIC fake + low-latency UDP handling."),
    "game_steam": ("Game (STEAM)", "Optimized for Steam. Game downloads, voice chat, and store access."),
    "game_general": ("Game (GENERAL)", "General gaming optimization. Low latency UDP, wide port range, aggressive fake."),
}


@dataclass
class StrategyRule:
    name: str = ""
    params: dict = field(default_factory=dict)

    def to_args(self) -> list:
        args = []
        for key, value in self.params.items():
            if isinstance(value, list):
                for v in value:
                    args.append(f"--{key}")
                    args.append(str(v))
            elif value is True:
                args.append(f"--{key}")
            elif value is not False and value is not None:
                args.append(f"--{key}={value}")
        return args


@dataclass
class Strategy:
    id: str = ""
    name: str = ""
    description: str = ""
    version: str = "1.0"
    author: str = "vesno4null"
    wf_tcp: str = "80,443,2053,2083,2087,2096,8443"
    wf_udp: str = "443,19294-19344,50000-50100"
    rules: list = field(default_factory=list)
    path: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "author": self.author,
            "wf_tcp": self.wf_tcp,
            "wf_udp": self.wf_udp,
            "rules": [
                {"name": r.name, **r.params} for r in self.rules
            ],
        }

    def build_command(
        self,
        binary_path: str,
        bin_dir: str,
        lists_dir: str,
        is_windows: bool = True,
    ) -> list:
        cmd = [str(binary_path)]

        if is_windows:
            raw_tcp = self.wf_tcp.replace("%GameFilterTCP%", "").replace("{game_filter_tcp}", "")
            raw_udp = self.wf_udp.replace("%GameFilterUDP%", "").replace("{game_filter_udp}", "")
            tcp_parts = [p.strip() for p in raw_tcp.split(",") if p.strip()]
            udp_parts = [p.strip() for p in raw_udp.split(",") if p.strip()]
            if tcp_parts:
                cmd.append(f"--wf-tcp={','.join(tcp_parts)}")
            if udp_parts:
                cmd.append(f"--wf-udp={','.join(udp_parts)}")

        for i, rule in enumerate(self.rules):
            rule_args = rule.to_args()
            resolved = []
            skip = False

            for arg in rule_args:
                if arg.startswith("--"):
                    keyval = arg.split("=", 1)
                    if len(keyval) == 2:
                        val = self._resolve_path(keyval[1], bin_dir, lists_dir)
                        if keyval[0] in ("--filter-tcp", "--filter-udp") and not val.strip():
                            skip = True
                            break
                        resolved.append(f"{keyval[0]}={val}")
                    else:
                        resolved.append(keyval[0])
                else:
                    resolved.append(self._resolve_path(arg, bin_dir, lists_dir))

            if skip:
                continue

            cmd.extend(resolved)
            if i < len(self.rules) - 1:
                cmd.append("--new")

        return cmd

    @staticmethod
    def _resolve_path(value: str, bin_dir: str, lists_dir: str) -> str:
        zapret_bin = "/opt/zapret/bin/"
        value = value.replace("{bin}", bin_dir.rstrip("\\/") + "/")
        value = value.replace("{lists}", lists_dir.rstrip("\\/") + "/")
        value = value.replace("{game_filter_tcp}", "")
        value = value.replace("{game_filter_udp}", "")

        if value.startswith(zapret_bin):
            local = bin_dir.rstrip("\\/") + "/" + value[len(zapret_bin):]
            if not os.path.isfile(local) and not os.path.isfile(value):
                pass
            elif os.path.isfile(local) and not os.path.isfile(value):
                value = local

        return value


class StrategyParser:
    @staticmethod
    def from_file(path: str) -> Optional[Strategy]:
        p = Path(path)
        if p.suffix == ".strategy":
            return StrategyParser._from_json(p)
        elif p.suffix == ".bat":
            return StrategyParser._from_bat(p)
        return None

    @staticmethod
    def _from_json(path: Path) -> Optional[Strategy]:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            s = Strategy()
            s.id = data.get("id", path.stem)
            s.name = data.get("name", s.id)
            s.description = data.get("description", "")
            s.version = data.get("version", "1.0")
            s.author = data.get("author", "Mangopret")
            s.wf_tcp = data.get("wf_tcp", "80,443,2053,2083,2087,2096,8443")
            s.wf_udp = data.get("wf_udp", "443,19294-19344,50000-50100")
            s.path = str(path)

            for rule_data in data.get("rules", []):
                rule = StrategyRule()
                rule.name = rule_data.pop("name", "")
                rule.params = rule_data
                s.rules.append(rule)

            return s
        except Exception:
            return None

    @staticmethod
    def _from_bat(path: Path) -> Optional[Strategy]:
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")

            wf_tcp_match = re.search(r'--wf-tcp=([^\s^]+)', content)
            wf_udp_match = re.search(r'--wf-udp=([^\s^]+)', content)

            wf_tcp = ""
            wf_udp = ""
            if wf_tcp_match:
                wf_tcp = wf_tcp_match.group(1).rstrip("^").strip()
            if wf_udp_match:
                wf_udp = wf_udp_match.group(1).rstrip("^").strip()

            wf_tcp = wf_tcp.replace('%GameFilterTCP%', '').strip(',').strip()
            wf_udp = wf_udp.replace('%GameFilterUDP%', '').strip(',').strip()

            winws_match = re.search(r'winws\.exe["\s]', content)
            if not winws_match:
                return None

            cmd_text = content[winws_match.end():]

            cmd_text = cmd_text.replace('^\n', ' ')
            cmd_text = cmd_text.replace('^\r\n', ' ')
            cmd_text = re.sub(r'\^(?=\s|$)', '', cmd_text)
            cmd_text = cmd_text.replace('\r\n', ' ').replace('\n', ' ')

            cmd_text = re.sub(r'::.*$', '', cmd_text, flags=re.MULTILINE)

            cmd_text = cmd_text.strip()

            tokens = StrategyParser._tokenize(cmd_text)

            rules = []
            current_rule = {}
            rule_names = []

            for token in tokens:
                if token == "--new":
                    if current_rule:
                        rname = StrategyParser._generate_rule_name(current_rule, rule_names)
                        rules.append(StrategyRule(name=rname, params=dict(current_rule)))
                    current_rule = {}
                    rule_names = []
                    continue

                if token.startswith("--"):
                    eq_idx = token.find("=")
                    if eq_idx != -1:
                        key = token[2:eq_idx]
                        val = token[eq_idx + 1:]
                        val = StrategyParser._clean_value(val)
                    else:
                        key = token[2:]
                        val = True

                    if key in ("wf-tcp", "wf-udp"):
                        continue

                    if key == "filter-udp" and not rule_names:
                        rule_names.append(f"UDP {val}")
                    elif key == "filter-tcp" and not rule_names:
                        rule_names.append(f"TCP {val}")
                    elif key == "filter-l7" and not rule_names:
                        rule_names.append(f"L7 {val}")
                    elif key == "filter-l3" and not rule_names:
                        rule_names.append(f"L3 {val}")
                    elif key == "hostlist-domains" and not any(
                        n.startswith("Discord") or n.startswith("Google") for n in rule_names
                    ):
                        domain = str(val)
                        if "discord" in domain.lower():
                            rule_names.append("Discord Media")
                        elif "google" in domain.lower():
                            rule_names.append("Google")
                        else:
                            rule_names.append(f"Domains {domain}")

                    if key in current_rule and isinstance(current_rule[key], list):
                        current_rule[key].append(val)
                    elif key in current_rule:
                        current_rule[key] = [current_rule[key], val]
                    else:
                        current_rule[key] = val

                elif token.startswith('"') and token.endswith('"'):
                    pass
                elif not token.startswith("-") and current_rule:
                    last_key = list(current_rule.keys())[-1] if current_rule else None
                    if last_key and current_rule[last_key] is True:
                        current_rule[last_key] = token

            if current_rule:
                rname = StrategyParser._generate_rule_name(current_rule, rule_names)
                rules.append(StrategyRule(name=rname, params=dict(current_rule)))

            stem = path.stem
            clean_id = stem
            clean_name = stem.replace("(", " ").replace(")", " ").strip()
            clean_name = re.sub(r'\s+', ' ', clean_name).strip()

            name_key = stem.lower().replace(" ", "_").replace("(", "").replace(")", "")
            if name_key in DESCRIPTIONS:
                display_name, desc = DESCRIPTIONS[name_key]
            else:
                display_name = clean_name
                desc = f"Strategy converted from {path.name}"

            s = Strategy()
            s.id = clean_id
            s.name = display_name
            s.description = desc
            s.wf_tcp = wf_tcp
            s.wf_udp = wf_udp
            s.rules = rules
            s.path = str(path)
            return s

        except Exception as e:
            print(f"  [ERROR] Failed to parse {path.name}: {e}")
            import traceback
            traceback.print_exc()
            return None

    @staticmethod
    def _clean_value(val: str) -> str:
        val = val.strip('"')
        val = val.replace('^!', '!')
        val = val.replace('^"', '"')

        val = val.replace('%BIN%', '{bin}/')
        val = val.replace('%LISTS%', '{lists}/')
        val = val.replace('%GameFilterTCP%', '{game_filter_tcp}')
        val = val.replace('%GameFilterUDP%', '{game_filter_udp}')

        if val.startswith('"') and val.endswith('"'):
            inner = val[1:-1]
            if '{bin}' in inner or '{lists}' in inner:
                val = inner

        return val

    @staticmethod
    def _generate_rule_name(rule: dict, fallback_names: list) -> str:
        if fallback_names:
            base = fallback_names[0]
        elif "filter-udp" in rule:
            base = f"UDP {rule['filter-udp']}"
        elif "filter-tcp" in rule:
            base = f"TCP {rule['filter-tcp']}"
        elif "filter-l7" in rule:
            base = f"L7 {rule['filter-l7']}"
        elif "filter-l3" in rule:
            base = f"L3 {rule['filter-l3']}"
        else:
            base = "Rule"

        desync = rule.get("dpi-desync", "")
        if desync:
            short_desync = desync.split(",")[0]
            if "game" in str(rule.get("ipset", "")).lower():
                base = f"Game {base}"
            elif "ipset" in str(rule.get("ipset", "")):
                base = f"IPSet {base}"

        seen = []
        for part in base.split():
            if part not in seen:
                seen.append(part)
        return " ".join(seen)

    @staticmethod
    def _tokenize(text: str) -> list:
        tokens = []
        current = ""
        in_quote = False
        quote_char = ""
        i = 0

        while i < len(text):
            ch = text[i]

            if in_quote:
                if ch == '\\' and i + 1 < len(text) and text[i + 1] == quote_char:
                    current += text[i + 1]
                    i += 2
                    continue
                if ch == quote_char:
                    in_quote = False
                    current += ch
                else:
                    current += ch
            elif ch in ('"', "'"):
                in_quote = True
                quote_char = ch
                current += ch
            elif ch in (' ', '\t', '\n', '\r'):
                if current.strip():
                    tokens.append(current.strip())
                current = ""
            else:
                current += ch

            i += 1

        if current.strip():
            tokens.append(current.strip())

        return tokens

    @staticmethod
    def to_strategy_file(strategy: Strategy, path: str):
        data = strategy.to_dict()

        ordered = {
            "id": data["id"],
            "name": data["name"],
            "description": data["description"],
            "version": data["version"],
            "author": data["author"],
            "wf_tcp": data["wf_tcp"],
            "wf_udp": data["wf_udp"],
            "rules": data["rules"],
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(ordered, f, indent=2, ensure_ascii=False)
            f.write("\n")

    @staticmethod
    def convert_all_bats(bat_dir: str, output_dir: str):
        bat_dir = Path(bat_dir)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        converted = []
        failed = []

        bat_files = sorted(bat_dir.glob("general*.bat"))
        if not bat_files:
            print(f"  No general*.bat files found in {bat_dir}")
            return converted

        for bat_file in bat_files:
            print(f"  Converting: {bat_file.name} ... ", end="", flush=True)
            strategy = StrategyParser._from_bat(bat_file)
            if strategy and strategy.rules:
                out_path = output_dir / f"{strategy.id}.strategy"
                StrategyParser.to_strategy_file(strategy, out_path)
                converted.append(strategy)
                print(f"OK ({len(strategy.rules)} rules)")
            else:
                failed.append(bat_file.name)
                print("FAILED")

        if failed:
            print(f"\n  Failed: {', '.join(failed)}")

        return converted
