"""Harness d'évaluation du classifieur e-mail — v1 vs v2 (Path B).

Rejoue les deux variantes sur un jeu d'e-mails annoté à la main et calcule
precision / recall / F1 par classe pour `urgence` et `action`, plus une
matrice de confusion. Écrit un rapport Markdown dans DOCS/reports/.

Usage :
    python eval/classifier/run_eval.py eval/classifier/dataset.csv
    python eval/classifier/run_eval.py eval/classifier/dataset.example.csv --dry-run

dataset CSV attendu (une ligne = un e-mail) :
    id,source,sender,subject,body,label_urgence,label_action
Les lignes sans label_urgence ET label_action sont ignorées (non annotées).

Nécessite OPENAI_API_KEY (lu depuis .env ou l'environnement). --dry-run n'appelle
pas l'API : les prédictions sont tirées au hasard (sert à valider le pipeline).
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import prompts  # noqa: E402  (module frère eval/classifier/prompts.py)

URGENCE = ["haute", "moyenne", "faible"]
ACTION = ["repondre", "lire", "relancer", "classer", "aucune"]
BATCH = 10


def load_env() -> None:
    envf = REPO / ".env"
    if not envf.exists():
        return
    for line in envf.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"'))


def read_dataset(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            u = (r.get("label_urgence") or "").strip().lower()
            a = (r.get("label_action") or "").strip().lower()
            if not u and not a:
                continue  # non annoté
            rows.append({
                "id": (r.get("id") or f"row{len(rows)}").strip(),
                "source": (r.get("source") or "?").strip(),
                "sender": (r.get("sender") or "").strip(),
                "subject": (r.get("subject") or "").strip(),
                "body": (r.get("body") or "").strip()[:1500],
                "label_urgence": u,
                "label_action": a,
            })
    return rows


def email_payload(rows: list[dict]) -> list[dict]:
    return [
        {"id": r["id"], "subject": r["subject"], "sender": r["sender"], "snippet": r["body"]}
        for r in rows
    ]


def predict(variant: str, rows: list[dict], dry_run: bool) -> dict[str, dict]:
    """-> {id: {"urgence": .., "action": ..}}"""
    if dry_run:
        return {r["id"]: {"urgence": random.choice(URGENCE), "action": random.choice(ACTION)} for r in rows}

    from openai import OpenAI

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    build = prompts.v1_request if variant == "v1" else prompts.v2_request
    out: dict[str, dict] = {}
    for i in range(0, len(rows), BATCH):
        chunk = rows[i:i + BATCH]
        req = build(email_payload(chunk))
        resp = client.chat.completions.create(**req)
        content = resp.choices[0].message.content or "{}"
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            parsed = {"emails": []}
        for e in parsed.get("emails", []):
            if e.get("id"):
                out[str(e["id"])] = {
                    "urgence": str(e.get("urgence", "")).lower(),
                    "action": str(e.get("action", "")).lower(),
                }
    return out


def prf(y_true: list[str], y_pred: list[str], labels: list[str]) -> dict:
    tp = Counter()
    fp = Counter()
    fn = Counter()
    for t, p in zip(y_true, y_pred):
        if t == p:
            tp[t] += 1
        else:
            fp[p] += 1
            fn[t] += 1
    res = {}
    f1s = []
    for lb in labels:
        p = tp[lb] / (tp[lb] + fp[lb]) if (tp[lb] + fp[lb]) else 0.0
        r = tp[lb] / (tp[lb] + fn[lb]) if (tp[lb] + fn[lb]) else 0.0
        f1 = 2 * p * r / (p + r) if (p + r) else 0.0
        res[lb] = {"precision": p, "recall": r, "f1": f1, "support": sum(1 for t in y_true if t == lb)}
        if res[lb]["support"]:
            f1s.append(f1)
    acc = sum(1 for t, p in zip(y_true, y_pred) if t == p) / len(y_true) if y_true else 0.0
    res["_macro_f1"] = sum(f1s) / len(f1s) if f1s else 0.0
    res["_accuracy"] = acc
    return res


def confusion(y_true, y_pred, labels) -> str:
    m = defaultdict(Counter)
    for t, p in zip(y_true, y_pred):
        m[t][p] += 1
    head = "| vrai \\ prédit | " + " | ".join(labels) + " |"
    sep = "|" + "---|" * (len(labels) + 1)
    lines = [head, sep]
    for t in labels:
        lines.append("| " + t + " | " + " | ".join(str(m[t][p]) for p in labels) + " |")
    return "\n".join(lines)


def section(name: str, rows, preds_v1, preds_v2, field: str, labels: list[str]) -> list[str]:
    yt = [r[f"label_{field}"] for r in rows if r[f"label_{field}"]]
    ids = [r["id"] for r in rows if r[f"label_{field}"]]
    yp1 = [preds_v1.get(i, {}).get(field, "") for i in ids]
    yp2 = [preds_v2.get(i, {}).get(field, "") for i in ids]
    m1, m2 = prf(yt, yp1, labels), prf(yt, yp2, labels)
    out = [f"### {name} (`{field}`) — {len(yt)} e-mails annotés\n"]
    out.append("| moteur | accuracy | macro-F1 |\n|---|---|---|")
    out.append(f"| v1 | {m1['_accuracy']:.2f} | {m1['_macro_f1']:.2f} |")
    out.append(f"| v2 | {m2['_accuracy']:.2f} | {m2['_macro_f1']:.2f} |\n")
    out.append("| classe | support | P v1 | R v1 | F1 v1 | P v2 | R v2 | F1 v2 |")
    out.append("|---|---|---|---|---|---|---|---|")
    for lb in labels:
        a, b = m1[lb], m2[lb]
        out.append(
            f"| {lb} | {a['support']} | {a['precision']:.2f} | {a['recall']:.2f} | {a['f1']:.2f} "
            f"| {b['precision']:.2f} | {b['recall']:.2f} | {b['f1']:.2f} |"
        )
    out.append(f"\n**Matrice de confusion v2**\n\n{confusion(yt, yp2, labels)}\n")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("dataset")
    ap.add_argument("--dry-run", action="store_true", help="prédictions aléatoires, pas d'appel API")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    random.seed(args.seed)
    load_env()

    rows = read_dataset(Path(args.dataset))
    if not rows:
        print("Aucune ligne annotée dans", args.dataset, "(remplis label_urgence / label_action).")
        return 1
    if not args.dry_run and not os.environ.get("OPENAI_API_KEY"):
        print("OPENAI_API_KEY manquant (ou utilise --dry-run).")
        return 1

    print(f"{len(rows)} e-mails annotés — variante v1…")
    p1 = predict("v1", rows, args.dry_run)
    print("variante v2…")
    p2 = predict("v2", rows, args.dry_run)

    date = dt.date.today().isoformat()
    md = [
        "# Évaluation classifieur e-mail — v1 vs v2\n",
        f"**Date** : {date}  |  **Jeu** : `{args.dataset}` ({len(rows)} e-mails annotés)"
        + ("  |  ⚠️ **DRY-RUN** (prédictions aléatoires)" if args.dry_run else ""),
        "\n**v1** : appel OpenAI `json_object` + `JSON.parse`. **v2** : `json_schema` strict (Path B, 2026-09-04).",
        f"Modèle : `{prompts.MODEL}`, temp `{prompts.TEMPERATURE}`.\n",
        "---\n",
    ]
    md += section("Urgence", rows, p1, p2, "urgence", URGENCE)
    md += ["\n---\n"]
    md += section("Action", rows, p1, p2, "action", ACTION)
    md += [
        "\n---\n",
        "## Lecture\n",
        "- Si v2 ne dépasse pas v1 en macro-F1 sur `urgence` **et** `action` → garder v1 comme moteur "
        "(cf. `DOCS/plans/cv-embellissement-scope.md`), v2 reste joignable via le toggle.",
        "- Le gain attendu de v2 = **fiabilité du format** (JSON Schema strict, 0 parse cassé), pas "
        "forcément la qualité de classification (même modèle, même consigne).",
    ]

    out = REPO / "DOCS" / "reports" / f"classifier-eval-{date}.md"
    out.write_text("\n".join(md) + "\n", encoding="utf-8")
    print("écrit :", out.relative_to(REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
